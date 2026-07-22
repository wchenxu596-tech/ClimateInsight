#!/bin/bash
# ============================================================
# ClimateInsight 一键设置脚本
# 用法: bash scripts/setup.sh
# 功能: 启动服务 → 下载 NOAA GSOD 数据 → 加载到 MySQL
# ============================================================

set -e

echo "============================================"
echo " ClimateInsight — 全球气候智能分析平台"
echo "============================================"

# 1. 检查 .env
if [ ! -f .env ]; then
    echo "[setup] 创建 .env 文件..."
    cat > .env << EOF
MYSQL_PASSWORD=climate123
EOF
fi

# 2. 启动服务
echo "[setup] 启动 MySQL + Backend + Frontend ..."
docker compose up -d mysql backend frontend

# 3. 等待 MySQL 就绪
echo "[setup] 等待 MySQL 就绪..."
until docker compose exec mysql mysqladmin ping -u root -pclimate123 --silent 2>/dev/null; do
    echo -n "."
    sleep 3
done
echo " OK"

# 4. 等待 Backend 就绪
echo "[setup] 等待 Backend API 就绪..."
until curl -s http://localhost:5000/api/health > /dev/null 2>&1; do
    echo -n "."
    sleep 2
done
echo " OK"

# 5. 加载数据
echo ""
echo "[setup] 下载并加载 NOAA GSOD 2024 年数据..."
echo "[setup] 首次需要下载约 500MB，可能需要 5-10 分钟..."
echo ""
docker compose run --rm setup-data --year 2024 --skip-download

echo ""
echo "============================================"
echo " ✅ ClimateInsight 部署完成！"
echo "    访问 http://localhost:8080"
echo "============================================"
