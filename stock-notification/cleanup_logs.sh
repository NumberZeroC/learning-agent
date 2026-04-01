#!/bin/bash
#
# Stock-Agent 日志清理脚本
# 功能：
#   1. 日志文件清理（保留 10 天）
#   2. 早盘/晚间分析报告（保留 14 天，之前打包压缩）
#   3. 交易时间监控报告（保留 1 天，之前打包压缩）
#   4. 压缩包保留 10 个，多余删除
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
REPORT_DIR="$SCRIPT_DIR/data/reports"
MONITOR_DIR="$SCRIPT_DIR/data/reports/monitor"
ARCHIVE_DIR="$SCRIPT_DIR/data/archives"

# 保留天数
LOG_RETENTION_DAYS=10          # 日志文件保留天数
REPORT_RETENTION_DAYS=14       # 早盘/晚间报告保留天数
MONITOR_RETENTION_DAYS=7       # 监控报告保留天数 (7 天)
MAX_ARCHIVES=10                # 压缩包最大保留数量

# 日期戳
TODAY=$(date +%Y%m%d)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=========================================="
echo "Stock-Agent 日志与报告清理"
echo "=========================================="
echo "📅 执行时间：$(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 创建归档目录
mkdir -p "$ARCHIVE_DIR"

# ============================================
# 1. 清理日志文件 (logs/*.log)
# ============================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 任务 1: 清理日志文件 (保留${LOG_RETENTION_DAYS}天)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -d "$LOG_DIR" ]; then
    BEFORE_COUNT=$(find "$LOG_DIR" -type f -name "*.log" | wc -l)
    BEFORE_SIZE=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1)
    
    DELETED_COUNT=0
    while IFS= read -r -d '' file; do
        if [ -f "$file" ]; then
            FILE_AGE=$(( ($(date +%s) - $(stat -c %Y "$file")) / 86400 ))
            echo "   🗑️  $file (${FILE_AGE}天)"
            rm -f "$file"
            ((DELETED_COUNT++))
        fi
    done < <(find "$LOG_DIR" -type f -name "*.log" -mtime +$LOG_RETENTION_DAYS -print0 2>/dev/null)
    
    AFTER_COUNT=$(find "$LOG_DIR" -type f -name "*.log" | wc -l)
    AFTER_SIZE=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1)
    
    echo "   📊 清理前：$BEFORE_COUNT 个文件 ($BEFORE_SIZE)"
    echo "   📊 清理后：$AFTER_COUNT 个文件 ($AFTER_SIZE)"
    echo "   ✅ 已删除 $DELETED_COUNT 个日志文件"
else
    echo "   ⚠️  日志目录不存在：$LOG_DIR"
fi
echo ""

# ============================================
# 2. 处理早盘/晚间分析报告 (保留 14 天，之前打包)
# ============================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 任务 2: 处理早盘/晚间分析报告 (保留${REPORT_RETENTION_DAYS}天)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -d "$REPORT_DIR" ]; then
    # 查找 14 天前的报告文件
    OLD_REPORTS=$(find "$REPORT_DIR" -maxdepth 1 -type f \( -name "report_*.md" -o -name "evening_analysis_*.md" -o -name "report_*.json" -o -name "evening_analysis_*.json" \) -mtime +$REPORT_RETENTION_DAYS 2>/dev/null)
    
    if [ -n "$OLD_REPORTS" ]; then
        ARCHIVE_NAME="reports_analysis_${TIMESTAMP}.tar.gz"
        ARCHIVE_PATH="$ARCHIVE_DIR/$ARCHIVE_NAME"
        
        echo "   📦 发现 $(echo "$OLD_REPORTS" | wc -l) 个过期报告，准备打包..."
        
        # 创建临时文件列表
        TEMP_LIST=$(mktemp)
        echo "$OLD_REPORTS" > "$TEMP_LIST"
        
        # 打包压缩
        tar -czf "$ARCHIVE_PATH" -T "$TEMP_LIST" 2>/dev/null
        
        if [ -f "$ARCHIVE_PATH" ]; then
            ARCHIVE_SIZE=$(du -h "$ARCHIVE_PATH" | cut -f1)
            echo "   ✅ 压缩包已创建：$ARCHIVE_NAME ($ARCHIVE_SIZE)"
            
            # 删除已打包的源文件
            echo "$OLD_REPORTS" | while read -r file; do
                if [ -f "$file" ]; then
                    rm -f "$file"
                fi
            done
            echo "   ✅ 已删除 $(echo "$OLD_REPORTS" | wc -l) 个源文件"
        else
            echo "   ❌ 打包失败"
        fi
        
        rm -f "$TEMP_LIST"
    else
        echo "   ✅ 无需打包，所有报告都在${REPORT_RETENTION_DAYS}天内"
    fi
    
    # 显示当前保留的报告
    CURRENT_REPORTS=$(find "$REPORT_DIR" -maxdepth 1 -type f \( -name "report_*.md" -o -name "evening_analysis_*.md" \) -mtime -$REPORT_RETENTION_DAYS 2>/dev/null | wc -l)
    echo "   📊 当前保留报告数：$CURRENT_REPORTS"
else
    echo "   ⚠️  报告目录不存在：$REPORT_DIR"
fi
echo ""

# ============================================
# 3. 处理交易时间监控报告 (保留 1 天，之前打包)
# ============================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 任务 3: 处理交易时间监控报告 (保留${MONITOR_RETENTION_DAYS}天)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -d "$MONITOR_DIR" ]; then
    # 查找 1 天前的监控报告
    OLD_MONITORS=$(find "$MONITOR_DIR" -type f \( -name "stock_monitor_*.md" -o -name "stock_monitor_*.json" \) -mtime +$MONITOR_RETENTION_DAYS 2>/dev/null)
    
    if [ -n "$OLD_MONITORS" ]; then
        ARCHIVE_NAME="reports_monitor_${TIMESTAMP}.tar.gz"
        ARCHIVE_PATH="$ARCHIVE_DIR/$ARCHIVE_NAME"
        
        echo "   📦 发现 $(echo "$OLD_MONITORS" | wc -l) 个过期监控报告，准备打包..."
        
        # 创建临时文件列表
        TEMP_LIST=$(mktemp)
        echo "$OLD_MONITORS" > "$TEMP_LIST"
        
        # 打包压缩
        tar -czf "$ARCHIVE_PATH" -T "$TEMP_LIST" 2>/dev/null
        
        if [ -f "$ARCHIVE_PATH" ]; then
            ARCHIVE_SIZE=$(du -h "$ARCHIVE_PATH" | cut -f1)
            echo "   ✅ 压缩包已创建：$ARCHIVE_NAME ($ARCHIVE_SIZE)"
            
            # 删除已打包的源文件
            echo "$OLD_MONITORS" | while read -r file; do
                if [ -f "$file" ]; then
                    rm -f "$file"
                fi
            done
            echo "   ✅ 已删除 $(echo "$OLD_MONITORS" | wc -l) 个源文件"
        else
            echo "   ❌ 打包失败"
        fi
        
        rm -f "$TEMP_LIST"
    else
        echo "   ✅ 无需打包，所有监控报告都在${MONITOR_RETENTION_DAYS}天内"
    fi
    
    # 显示当前保留的监控报告
    CURRENT_MONITORS=$(find "$MONITOR_DIR" -type f -name "stock_monitor_*.md" -mtime -$MONITOR_RETENTION_DAYS 2>/dev/null | wc -l)
    echo "   📊 当前保留监控报告数：$CURRENT_MONITORS"
else
    echo "   ⚠️  监控报告目录不存在：$MONITOR_DIR"
fi
echo ""

# ============================================
# 4. 清理旧压缩包 (保留最多${MAX_ARCHIVES}个)
# ============================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 任务 4: 清理旧压缩包 (保留最多${MAX_ARCHIVES}个)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -d "$ARCHIVE_DIR" ]; then
    # 获取压缩包列表，按时间排序
    ARCHIVE_COUNT=$(find "$ARCHIVE_DIR" -type f -name "*.tar.gz" | wc -l)
    
    if [ "$ARCHIVE_COUNT" -gt "$MAX_ARCHIVES" ]; then
        DELETE_COUNT=$((ARCHIVE_COUNT - MAX_ARCHIVES))
        echo "   📊 当前压缩包数：$ARCHIVE_COUNT"
        echo "   🗑️  需要删除：$DELETE_COUNT 个"
        
        # 删除最旧的压缩包
        find "$ARCHIVE_DIR" -type f -name "*.tar.gz" -printf "%T+ %p\n" 2>/dev/null | \
            sort | head -n "$DELETE_COUNT" | cut -d' ' -f2- | \
            while read -r file; do
                if [ -f "$file" ]; then
                    echo "   🗑️  $file"
                    rm -f "$file"
                fi
            done
        
        REMAINING=$(find "$ARCHIVE_DIR" -type f -name "*.tar.gz" | wc -l)
        echo "   ✅ 剩余压缩包数：$REMAINING"
    else
        echo "   📊 当前压缩包数：$ARCHIVE_COUNT"
        echo "   ✅ 无需清理，未超过限制"
    fi
    
    # 显示保留的压缩包
    echo ""
    echo "   📦 保留的压缩包:"
    find "$ARCHIVE_DIR" -type f -name "*.tar.gz" -printf "%T+ %p\n" 2>/dev/null | \
        sort -r | head -10 | while read -r line; do
            FILE=$(echo "$line" | cut -d' ' -f2-)
            SIZE=$(du -h "$FILE" 2>/dev/null | cut -f1)
            echo "      - $(basename "$FILE") ($SIZE)"
        done
else
    echo "   ⚠️  归档目录不存在：$ARCHIVE_DIR"
fi
echo ""

# ============================================
# 总结
# ============================================
echo "=========================================="
echo "✅ 清理任务完成"
echo "=========================================="
echo ""
echo "📁 目录结构:"
echo "   日志目录：$LOG_DIR"
echo "   报告目录：$REPORT_DIR"
echo "   监控目录：$MONITOR_DIR"
echo "   归档目录：$ARCHIVE_DIR"
echo ""
echo "⏰ 下次清理：明天 08:00 (cron 自动执行)"
echo ""
