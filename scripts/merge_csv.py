"""
快速合并 NOAA GSOD CSV 文件
- 保留第一个文件的表头
- 后续文件跳过头行
- 输出到目标路径
"""
import os, sys, glob

def merge_year(input_dir: str, output_file: str):
    files = sorted(glob.glob(os.path.join(input_dir, "*.csv")))
    if not files:
        print(f"未找到CSV: {input_dir}")
        return
    
    total = 0
    print(f"合并 {len(files)} 个文件 -> {output_file}")
    
    with open(output_file, "w", encoding="utf-8") as out:
        for i, f in enumerate(files):
            with open(f, "r", encoding="utf-8") as fin:
                lines = fin.readlines()
                if i == 0:
                    out.writelines(lines)      # 第一个文件: 保留表头
                else:
                    out.writelines(lines[1:])  # 后续文件: 跳过表头
                total += len(lines) - (0 if i == 0 else 1)
            if (i+1) % 2000 == 0:
                print(f"  进度: {i+1}/{len(files)}")
    
    size_mb = os.path.getsize(output_file) / 1024 / 1024
    print(f"完成! {total}行, {size_mb:.0f}MB")

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "data/gsod_2024"
    dst = sys.argv[2] if len(sys.argv) > 2 else "data/climate_2024.csv"
    merge_year(src, dst)
