"""批量导入 NOAA GSOD 全部年份数据"""
import subprocess, sys, os

YEARS = list(range(2010, 2026))
SKIP_EXISTING = True

env = os.environ.copy()
env["MYSQL_HOST"] = "127.0.0.1"
env["MYSQL_PORT"] = "3307"
env["MYSQL_USER"] = "root"
env["MYSQL_PASSWORD"] = "root"
env["MYSQL_DATABASE"] = "climate_dw"
env["NO_PROXY"] = ".noaa.gov"
env["HTTPS_PROXY"] = ""
env["HTTP_PROXY"] = ""

script = os.path.join(os.path.dirname(__file__), "download_and_load.py")

for y in YEARS:
    print(f"\n{'='*60}")
    print(f"  Importing year {y} ...")
    print(f"{'='*60}")
    result = subprocess.run(
        [sys.executable, script, "--year", str(y), "--skip-download"],
        env=env, cwd=os.path.dirname(os.path.dirname(__file__)),
    )
    if result.returncode != 0:
        # Try with download if skip-download fails (file not found)
        print(f"[Retry] Downloading {y} ...")
        result = subprocess.run(
            [sys.executable, script, "--year", str(y)],
            env=env, cwd=os.path.dirname(os.path.dirname(__file__)),
        )

print("\nDone!")
