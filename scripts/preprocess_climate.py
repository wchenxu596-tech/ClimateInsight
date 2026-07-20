"""
NOAA GSOD 气候数据预处理脚本
==============================
输入: data/gsod_YYYY/*.csv (每个气象站一个CSV)
输出: 合并为单个CSV或直接写入HDFS，去除重复表头，标准化列名
"""
import os
import csv
import glob
import sys
import argparse
from datetime import datetime

# NOAA GSOD 原始字段 → 标准化字段映射
COLUMN_MAP = {
    "STATION": "station_id",
    "DATE": "obs_date",
    "LATITUDE": "latitude",
    "LONGITUDE": "longitude",
    "ELEVATION": "elevation",
    "NAME": "station_name",
    "TEMP": "temp_mean_f",
    "DEWP": "dew_point_f",
    "SLP": "pressure_slp",
    "STP": "pressure_stp",
    "VISIB": "visibility",
    "WDSP": "wind_speed",
    "MXSPD": "wind_max_speed",
    "GUST": "wind_gust",
    "MAX": "temp_max_f",
    "MIN": "temp_min_f",
    "PRCP": "precip_inches",
    "SNDP": "snow_depth",
    "FRSHTT": "weather_flags",
}

# 需要保留的列（丢弃 _ATTRIBUTES 列）
KEEP_COLUMNS = list(COLUMN_MAP.keys())

# 输出列顺序（对应 COLUMN_MAP 的 values）
OUTPUT_COLUMNS = list(COLUMN_MAP.values())


def parse_weather_flags(flags_str: str) -> dict:
    """
    解析 FRSHTT 气象标记
    6位字符，每位表示: Frost, Rain, Snow, Hail, Thunder, Tornado
    1=发生, 0=未发生
    """
    flags_str = flags_str.strip()
    if len(flags_str) < 6:
        flags_str = flags_str.ljust(6, "0")
    return {
        "has_frost": 1 if flags_str[0] == "1" else 0,
        "has_rain": 1 if flags_str[1] == "1" else 0,
        "has_snow": 1 if flags_str[2] == "1" else 0,
        "has_hail": 1 if flags_str[3] == "1" else 0,
        "has_thunder": 1 if flags_str[4] == "1" else 0,
        "has_tornado": 1 if flags_str[5] == "1" else 0,
    }


def fahrenheit_to_celsius(f):
    """华氏度 → 摄氏度"""
    try:
        return round((float(f) - 32) * 5 / 9, 1)
    except (ValueError, TypeError):
        return None


def inches_to_mm(inches):
    """英寸 → 毫米"""
    try:
        return round(float(inches) * 25.4, 1)
    except (ValueError, TypeError):
        return None


def clean_value(val):
    """清洗单个值: 去除前后空格, 999.9/9999.9表示缺失值"""
    val = val.strip()
    if val in ("999.9", "9999.9", "99.99", "999.99", ""):
        return None
    try:
        return float(val)
    except ValueError:
        return val


def process_year(input_dir: str, output_file: str, year: int):
    """
    处理一年的数据: 合并所有气象站CSV → 清洗 → 输出单个CSV

    参数:
        input_dir: 包含 *.csv 文件的目录
        output_file: 输出CSV路径
        year: 年份（用于验证数据）
    """
    csv_files = sorted(glob.glob(os.path.join(input_dir, "*.csv")))
    if not csv_files:
        print(f"[错误] 在 {input_dir} 中未找到CSV文件")
        return 0

    print(f"[处理] {len(csv_files)} 个气象站文件")

    lines_written = 0
    lines_skipped = 0

    with open(output_file, "w", newline="", encoding="utf-8") as fout:
        writer = csv.writer(fout)

        # 写入标准化表头
        header = OUTPUT_COLUMNS + [
            "temp_mean_c", "temp_max_c", "temp_min_c",
            "dew_point_c", "precip_mm",
            "year", "month", "day",
            "has_frost", "has_rain", "has_snow",
            "has_hail", "has_thunder", "has_tornado",
            "quality_flag",
        ]
        writer.writerow(header)

        for i, filepath in enumerate(csv_files):
            if (i + 1) % 1000 == 0:
                print(f"  进度: {i+1}/{len(csv_files)} ...")

            with open(filepath, "r", encoding="utf-8") as fin:
                reader = csv.DictReader(fin)

                for row in reader:
                    # 验证年份
                    row_year = row.get("DATE", "0000")[:4]
                    if row_year != str(year):
                        continue

                    # 清洗数值字段
                    temp_mean = clean_value(row.get("TEMP", ""))
                    temp_max = clean_value(row.get("MAX", ""))
                    temp_min = clean_value(row.get("MIN", ""))
                    dew_point = clean_value(row.get("DEWP", ""))
                    precip = clean_value(row.get("PRCP", ""))
                    wind_speed = clean_value(row.get("WDSP", ""))
                    visibility = clean_value(row.get("VISIB", ""))
                    pressure_slp = clean_value(row.get("SLP", ""))
                    pressure_stp = clean_value(row.get("STP", ""))

                    # 温度转换 (华氏→摄氏)
                    temp_mean_c = fahrenheit_to_celsius(temp_mean) if temp_mean else None
                    temp_max_c = fahrenheit_to_celsius(temp_max) if temp_max else None
                    temp_min_c = fahrenheit_to_celsius(temp_min) if temp_min else None
                    dew_point_c = fahrenheit_to_celsius(dew_point) if dew_point else None

                    # 降水转换 (英寸→毫米)
                    precip_mm = inches_to_mm(precip) if precip else None

                    # 解析日期
                    date_str = row.get("DATE", "1900-01-01")
                    try:
                        dt = datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        lines_skipped += 1
                        continue

                    # 解析气象标记
                    flags = parse_weather_flags(row.get("FRSHTT", "000000"))

                    # 质量标记: 温度超过合理范围 → 可疑
                    quality = "valid"
                    if temp_mean_c is not None and (temp_mean_c < -90 or temp_mean_c > 60):
                        quality = "suspicious"
                    if temp_max_c is not None and (temp_max_c < -90 or temp_max_c > 60):
                        quality = "suspicious"

                    # 基础字段（原始值）
                    base_values = [
                        row.get("STATION", "").strip(),
                        date_str,
                        clean_value(row.get("LATITUDE", "")),
                        clean_value(row.get("LONGITUDE", "")),
                        clean_value(row.get("ELEVATION", "")),
                        row.get("NAME", "").strip().replace('"', ''),
                        temp_mean,
                        dew_point,
                        pressure_slp,
                        pressure_stp,
                        visibility,
                        wind_speed,
                        clean_value(row.get("MXSPD", "")),
                        clean_value(row.get("GUST", "")),
                        temp_max,
                        temp_min,
                        precip,
                        clean_value(row.get("SNDP", "")),
                        row.get("FRSHTT", "").strip(),
                    ]

                    # 衍生字段
                    derived = [
                        temp_mean_c, temp_max_c, temp_min_c,
                        dew_point_c, precip_mm,
                        dt.year, dt.month, dt.day,
                        flags["has_frost"], flags["has_rain"], flags["has_snow"],
                        flags["has_hail"], flags["has_thunder"], flags["has_tornado"],
                        quality,
                    ]

                    writer.writerow(base_values + derived)
                    lines_written += 1

    print(f"[完成] 写入 {lines_written} 行, 跳过 {lines_skipped} 行")
    print(f"[输出] {output_file} ({os.path.getsize(output_file)/1024/1024:.1f} MB)")
    return lines_written


def main():
    parser = argparse.ArgumentParser(description="NOAA GSOD 气候数据预处理")
    parser.add_argument("--input", "-i", required=True, help="输入目录 (含 *.csv)")
    parser.add_argument("--output", "-o", required=True, help="输出CSV文件路径")
    parser.add_argument("--year", "-y", type=int, required=True, help="年份 (如 2024)")
    args = parser.parse_args()

    count = process_year(args.input, args.output, args.year)
    if count:
        print(f"\n{'='*50}")
        print(f"预处理完成！{args.year}年共 {count} 行记录")
        print(f"可导入到 Hive 表: ods_climate_daily")
        print(f"{'='*50}")


if __name__ == "__main__":
    main()
