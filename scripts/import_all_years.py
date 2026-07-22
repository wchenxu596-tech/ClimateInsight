"""导入全部年份数据（仅处理已存在的 tar.gz）
用法: python scripts/import_all_years.py

前提：手动下载 NOAA GSOD 年度 tar.gz 放到 \data\raw\ 目录
下载地址: https://www.ncei.noaa.gov/data/global-summary-of-the-day/archive/{year}.tar.gz
年份范围: 2010-2025
"""
import subprocess, sys, os, glob

DATA_DIR = r"\data\raw"
YEARS = list(range(2010, 2026))
SCRIPT = os.path.join(os.path.dirname(__file__), "download_and_load.py")
ROOT = os.path.dirname(os.path.dirname(__file__))

env = os.environ.copy()
env["MYSQL_HOST"] = "127.0.0.1"
env["MYSQL_PORT"] = "3307"
env["MYSQL_USER"] = "root"
env["MYSQL_PASSWORD"] = "root"
env["MYSQL_DATABASE"] = "climate_dw"
env["NO_PROXY"] = ".noaa.gov"
env["HTTPS_PROXY"] = ""
env["HTTP_PROXY"] = ""

existing = set()
for f in glob.glob(os.path.join(DATA_DIR, "*.tar.gz")):
    try: existing.add(int(os.path.basename(f).replace(".tar.gz", "")))
    except: pass

missing = [y for y in YEARS if y not in existing]

print(f"已下载: {sorted(existing) if existing else '无'}")
print(f"待下载: {missing}")
print()

if missing:
    print("=" * 60)
    print("  以下年份需手动下载 tar.gz 到 \\data\\raw\\:")
    for y in missing:
        print(f"    {y}: https://www.ncei.noaa.gov/data/global-summary-of-the-day/archive/{y}.tar.gz")
    print("=" * 60)
    print()

success, failed = [], []
for y in sorted(existing):
    print(f"\n--- Importing {y} ---")
    r = subprocess.run([sys.executable, SCRIPT, "--year", str(y), "--skip-download"],
                       env=env, cwd=ROOT)
    if r.returncode == 0:
        success.append(y)
    else:
        failed.append(y)

print(f"\n完成！成功: {success}, 失败: {failed}")
if missing:
    print(f"还需手动下载 {len(missing)} 个年份: {missing}")
