#!/bin/bash
# 技术指标选股 - 快速测试脚本

echo "========================================"
echo "📊 技术指标选股 - 测试运行"
echo "========================================"

PYTHON="/home/admin/.openclaw/workspace/stock-notification/venv311/bin/python3"
SCRIPT_DIR="/home/admin/.openclaw/workspace/stock-notification"

cd "$SCRIPT_DIR"

echo ""
echo "1. 检查 Python 环境..."
$PYTHON --version

echo ""
echo "2. 检查依赖..."
$PYTHON -c "import akshare; import pandas; import numpy; print('✅ akshare:', akshare.__version__)"

echo ""
echo "3. 测试单只股票分析（平安银行 000001）..."
$PYTHON -c "
from technical_analysis import TechnicalAnalyzer
analyzer = TechnicalAnalyzer()
result = analyzer.analyze_stock('000001', '平安银行')
if result:
    print(f'✅ 分析成功')
    print(f'   得分：{result[\"score\"]}')
    print(f'   信号：{result[\"signals\"]}')
    print(f'   MACD: {\"金叉\" if result[\"macd\"].get(\"golden_cross\") else \"延续\"}')
else:
    print('⚠️ 分析失败或数据不足')
"

echo ""
echo "4. 创建日志目录..."
mkdir -p "$SCRIPT_DIR/logs"
echo "✅ 日志目录：$SCRIPT_DIR/logs"

echo ""
echo "========================================"
echo "✅ 测试完成"
echo "========================================"
echo ""
echo "下一步："
echo "1. 完整扫描：$PYTHON technical_analysis.py --limit 10"
echo "2. 设置定时任务：crontab -e"
echo "3. 查看文档：cat CRON_SETUP.md"
