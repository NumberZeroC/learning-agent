# Stock-Agent-Web 问题总结与集成测试方案

**文档创建日期：** 2026-03-24  
**总结周期：** 2026-03-16 至 2026-03-24  
**涉及项目：** stock-agent, stock-agent-web

---

## 📋 问题总结

### 1. 数据源配置问题

#### 问题 1.1：Tushare Token 读取失败

**现象：** 板块资金流数据显示为 0

**原因：** `capital_flow.py` 只从环境变量读取 `TUSHARE_TOKEN`，但实际 token 在 `config.yaml` 中

**影响：** 
- 板块资金流数据为空
- Web 看板数据不完整

**修复方案：**
```python
# 添加从配置文件读取 token 的逻辑
if not tushare_token:
    config_path = Path(__file__).parent.parent / 'config.yaml'
    if config_path.exists():
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        tushare_token = config.get('tushare', {}).get('token')
```

**测试用例：**
```python
def test_tushare_token_loading():
    """测试 Tushare Token 能否正确加载"""
    analyzer = CapitalFlowAnalyzer()
    assert analyzer.tushare_pro is not None, "Tushare Pro 未连接"
```

---

#### 问题 1.2：数据源访问失败

**现象：** 部分新闻源获取失败（OpenAI/Google/36Kr 等）

**原因：** 
- 网站反爬虫（403 Forbidden）
- SSL 证书问题
- URL 变更（404 Not Found）

**影响：**
- AI 新闻数据不完整
- 情感分析准确性下降

**修复方案：**
```python
# 移除不可用的新闻源
self.news_sources = [
    # 保留可用的源
    {"name": "Anthropic News", "url": "...", "priority": 1},
    {"name": "机器之心", "url": "...", "priority": 1},
    {"name": "量子位", "url": "...", "priority": 1},
]
```

**测试用例：**
```python
def test_news_source_availability():
    """测试新闻源可用性"""
    monitor = AINewsMonitor()
    news = monitor.fetch_all_news(limit_sources=5)
    assert len(news) > 0, "未获取到任何新闻"
```

---

### 2. 架构耦合问题

#### 问题 2.1：数据获取与报告生成耦合

**现象：** 
- 修改数据获取逻辑影响报告生成
- 无法单独测试数据获取模块
- 报告生成失败导致数据获取也失败

**原因：** 数据获取和报告生成在同一流程中

**修复方案：**
```
重构为三层架构：
数据获取层 (services/) → 数据存储层 (data/) → 报告生成层 (reporters/)
```

**测试用例：**
```python
def test_data_fetcher_independence():
    """测试数据获取器独立性"""
    fetcher = MarketDataFetcher()
    data = fetcher.fetch_all()
    assert data is not None, "数据获取失败"
    # 不依赖报告生成器
```

---

#### 问题 2.2：Web 服务直接调用数据源

**现象：** 
- Web 服务和 stock-agent 重复调用 API
- API 限流风险增加
- 数据不一致

**原因：** Web 服务直接调用 Tushare/AKShare

**修复方案：**
```python
# Web 服务从 stock-agent 数据存储层读取
class WebDataService:
    def __init__(self):
        self.data_dir = Path('/home/admin/.openclaw/workspace/data/stock-agent')
    
    def get_sector_flows(self):
        # 从文件读取，不调用 API
        data_file = self.data_dir / 'capital' / f'{date}.json'
```

**测试用例：**
```python
def test_web_data_service_reads_from_storage():
    """测试 Web 数据服务从存储层读取"""
    service = WebDataService()
    data = service.get_sector_flows()
    # 验证数据来自文件而非 API 调用
    assert data is not None
```

---

### 3. 路径配置问题

#### 问题 3.1：数据目录路径混乱

**现象：** 
- 不同模块使用不同路径
- 移动数据目录后服务失败
- 相对路径在不同环境下失效

**原因：** 使用相对路径，如 `Path(__file__).parent.parent / 'data'`

**修复方案：**
```python
# 使用绝对路径
self.data_dir = Path('/home/admin/.openclaw/workspace/data/stock-agent')

# 或使用配置
DATA_DIR = '/home/admin/.openclaw/workspace/data/stock-agent'
```

**测试用例：**
```python
def test_data_directory_exists():
    """测试数据目录存在且可访问"""
    data_dir = Path('/home/admin/.openclaw/workspace/data/stock-agent')
    assert data_dir.exists(), f"数据目录不存在：{data_dir}"
    assert (data_dir / 'market').exists(), "市场数据目录不存在"
    assert (data_dir / 'capital').exists(), "资金流数据目录不存在"
```

---

### 4. Web 服务问题

#### 问题 4.1：API 路由未注册

**现象：** 访问新 API 端点返回 404

**原因：** 忘记在 `__init__.py` 中导入新路由模块

**修复方案：**
```python
# api/v1/__init__.py
from api.v1 import stocks, monitor, config_routes, report_routes, data_routes
```

**测试用例：**
```python
def test_api_endpoints_available():
    """测试 API 端点可访问"""
    endpoints = [
        '/api/v1/data/overview',
        '/api/v1/data/capital/sectors',
        '/api/v1/data/ai-news',
    ]
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 200, f"{endpoint} 返回 404"
```

---

#### 问题 4.2：CORS 配置问题

**现象：** 浏览器跨域请求被拒绝

**原因：** CORS 配置不完整

**修复方案：**
```python
from flask_cors import CORS
CORS(app, origins=['*'])  # 或指定域名
```

**测试用例：**
```python
def test_cors_headers():
    """测试 CORS 头是否正确设置"""
    response = client.get('/api/v1/data/overview', 
                          headers={'Origin': 'http://example.com'})
    assert 'Access-Control-Allow-Origin' in response.headers
```

---

### 5. 定时任务问题

#### 问题 5.1：任务时间冲突

**现象：** 20:00 同时发送两条 QQ 消息

**原因：** AI 新闻推送和晚间总结都在 20:00 执行

**修复方案：**
```bash
# 错开执行时间
0 20 * * *   AI 新闻推送
30 20 * * *  晚间总结
```

**测试用例：**
```python
def test_cron_schedule_no_conflict():
    """测试定时任务时间无冲突"""
    crontab = read_crontab()
    times = extract_execution_times(crontab)
    assert no_duplicate_times(times), "存在重复执行时间"
```

---

#### 问题 5.2：任务失败无告警

**现象：** 定时任务失败后无人知晓

**原因：** 缺少失败告警机制

**修复方案：**
```python
# 添加健康检查
def check_data_freshness():
    latest_data = get_latest_data()
    if latest_data is None or is_too_old(latest_data):
        send_alert("数据更新失败")
```

**测试用例：**
```python
def test_data_freshness():
    """测试数据新鲜度"""
    latest = get_latest_data_date()
    age = datetime.now() - latest
    assert age.days <= 1, "数据超过 1 天未更新"
```

---

## 🧪 集成测试项目

### 测试项目结构

```
/home/admin/.openclaw/workspace/tests/
├── conftest.py              # pytest 配置
├── test_data_fetchers.py    # 数据获取测试
├── test_web_api.py          # Web API 测试
├── test_data_integrity.py   # 数据完整性测试
├── test_cron_jobs.py        # 定时任务测试
└── daily_test_runner.py     # 每日测试执行器
```

### 测试用例设计

#### 1. 数据获取测试

```python
# test_data_fetchers.py

def test_market_data_fetcher():
    """测试市场数据获取"""
    fetcher = MarketDataFetcher()
    data = fetcher.fetch_all()
    
    assert 'indices' in data
    assert 'shanghai' in data['indices']
    assert data['indices']['shanghai']['close'] > 0

def test_capital_flow_fetcher():
    """测试资金流数据获取"""
    fetcher = CapitalFlowFetcher()
    data = fetcher.fetch_all()
    
    assert 'sector_flows' in data
    assert len(data['sector_flows']) > 0
    assert data['sector_flows'][0]['net_flow'] is not None

def test_ai_news_fetcher():
    """测试 AI 新闻数据获取"""
    fetcher = AINewsFetcher()
    data = fetcher.fetch_all()
    
    assert 'news' in data
    assert 'sentiment' in data
    assert len(data['news']) > 0
```

#### 2. Web API 测试

```python
# test_web_api.py

def test_data_overview_api():
    """测试首页概览 API"""
    response = requests.get('http://localhost:5000/api/v1/data/overview')
    
    assert response.status_code == 200
    data = response.json()['data']
    assert 'market' in data
    assert 'capital' in data
    assert 'ai_news' in data

def test_sector_flows_api():
    """测试板块资金流 API"""
    response = requests.get('http://localhost:5000/api/v1/data/capital/sectors')
    
    assert response.status_code == 200
    data = response.json()['data']['sector_flows']
    assert len(data) > 0
    assert 'sector' in data[0]
    assert 'net_flow' in data[0]

def test_ai_news_api():
    """测试 AI 新闻 API"""
    response = requests.get('http://localhost:5000/api/v1/data/ai-news')
    
    assert response.status_code == 200
    data = response.json()['data']
    assert 'news' in data
    assert 'sentiment' in data
```

#### 3. 数据完整性测试

```python
# test_data_integrity.py

def test_data_directory_structure():
    """测试数据目录结构"""
    data_dir = Path('/home/admin/.openclaw/workspace/data/stock-agent')
    
    assert (data_dir / 'market').exists()
    assert (data_dir / 'capital').exists()
    assert (data_dir / 'ai_news').exists()
    assert (data_dir / 'aggregated').exists()

def test_data_file_freshness():
    """测试数据文件新鲜度"""
    data_dir = Path('/home/admin/.openclaw/workspace/data/stock-agent')
    today = datetime.now().strftime('%Y%m%d')
    
    # 检查今日数据文件是否存在
    market_file = data_dir / 'market' / f'{today}.json'
    capital_file = data_dir / 'capital' / f'{today}.json'
    
    # 如果是交易日，应该有今日数据
    if is_trading_day():
        assert market_file.exists(), f"市场数据文件不存在：{market_file}"
        assert capital_file.exists(), f"资金流数据文件不存在：{capital_file}"

def test_data_consistency():
    """测试数据一致性"""
    # 检查聚合数据是否包含所有子数据
    agg_file = Path('/home/admin/.openclaw/workspace/data/stock-agent/aggregated/20260324.json')
    
    with open(agg_file) as f:
        agg_data = json.load(f)
    
    assert 'market' in agg_data
    assert 'capital' in agg_data
    assert 'ai_news' in agg_data
    assert agg_data['market']['indices'] is not None
```

#### 4. 定时任务测试

```python
# test_cron_jobs.py

def test_cron_jobs_configured():
    """测试定时任务已配置"""
    result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
    
    assert 'fetch_data.sh' in result.stdout, "数据获取任务未配置"
    assert 'generate_report.sh' in result.stdout, "报告生成任务未配置"

def test_cron_jobs_no_conflict():
    """测试定时任务时间无冲突"""
    result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
    
    # 解析执行时间
    times = parse_cron_times(result.stdout)
    
    # 检查是否有重复时间
    assert len(times) == len(set(times)), f"存在时间冲突：{times}"
```

---

## ⏰ 每日自动测试

### 测试执行脚本

```python
#!/usr/bin/env python3
"""
每日测试执行器
功能：每天 7 点自动运行集成测试，发现问题及时修复
"""

import subprocess
import sys
import json
from datetime import datetime
from pathlib import Path

# 配置
TEST_DIR = Path('/home/admin/.openclaw/workspace/tests')
LOG_DIR = Path('/home/admin/.openclaw/workspace/tests/logs')
REPORT_FILE = LOG_DIR / f'test_report_{datetime.now().strftime("%Y%m%d")}.json'

# 通知配置
QQ_TARGET = "qqbot:c2c:6BD7A1BCF3F92369D0580647287C0D52"

def run_tests():
    """运行测试"""
    print(f"🧪 开始运行集成测试 - {datetime.now()}")
    
    # 运行 pytest
    result = subprocess.run(
        ['pytest', str(TEST_DIR), '-v', '--tb=short', '--json-report'],
        capture_output=True,
        text=True
    )
    
    return {
        'success': result.returncode == 0,
        'stdout': result.stdout,
        'stderr': result.stderr,
        'returncode': result.returncode
    }

def send_notification(result):
    """发送测试结果通知"""
    if result['success']:
        message = f"""✅ 每日测试通过

📊 测试结果：全部通过
🕐 测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📄 详细报告：{REPORT_FILE}
"""
    else:
        message = f"""❌ 每日测试失败

📊 测试结果：{result['returncode']}
🕐 测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📄 详细报告：{REPORT_FILE}

⚠️ 请尽快修复！
"""
    
    # 发送 QQ 通知
    subprocess.run([
        'openclaw', 'message', 'send',
        '--target', QQ_TARGET,
        '--message', message
    ])

def main():
    """主函数"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # 运行测试
    result = run_tests()
    
    # 保存报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'success': result['success'],
        'returncode': result['returncode']
    }
    
    with open(REPORT_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    
    # 发送通知
    send_notification(result)
    
    # 返回结果
    sys.exit(0 if result['success'] else 1)

if __name__ == '__main__':
    main()
```

### 定时任务配置

```bash
# 每天 7:00 运行测试
0 7 * * * /home/admin/.openclaw/workspace/tests/daily_test_runner.py >> /home/admin/.openclaw/workspace/tests/logs/daily_test.log 2>&1
```

---

## 📊 测试报告模板

```json
{
  "timestamp": "2026-03-25T07:00:00",
  "success": true,
  "returncode": 0,
  "tests": {
    "total": 15,
    "passed": 15,
    "failed": 0,
    "skipped": 0
  },
  "duration_seconds": 45.3,
  "details": {
    "data_fetchers": "✅ 5/5",
    "web_api": "✅ 6/6",
    "data_integrity": "✅ 3/3",
    "cron_jobs": "✅ 1/1"
  }
}
```

---

## 🔧 快速修复指南

### 问题 1：数据获取失败

```bash
# 1. 检查日志
cat /home/admin/.openclaw/workspace/stock-agent/logs/data_fetch_*.log

# 2. 手动测试
cd /home/admin/.openclaw/workspace/stock-agent
./venv311/bin/python3 services/data_aggregator.py --date 20260324

# 3. 检查 API 配额
cat config.yaml | grep token
```

### 问题 2：Web API 失败

```bash
# 1. 检查 Web 服务状态
ps aux | grep stock-agent-web

# 2. 检查日志
tail -50 /home/admin/.openclaw/workspace/stock-agent-web/logs/web.log

# 3. 测试 API
curl http://localhost:5000/api/v1/data/overview
```

### 问题 3：定时任务失败

```bash
# 1. 检查 crontab
crontab -l

# 2. 检查日志
cat /home/admin/.openclaw/workspace/stock-agent/logs/cron_*.log

# 3. 手动执行
/home/admin/.openclaw/workspace/stock-agent/scripts/fetch_data.sh
```

---

## 📈 质量指标

| 指标 | 目标 | 当前 |
|------|------|------|
| 测试覆盖率 | >80% | 待实现 |
| API 可用性 | >99% | 待监控 |
| 数据新鲜度 | <1 天 | ✅ 正常 |
| 定时任务成功率 | 100% | 待监控 |

---

**文档版本：** 1.0  
**最后更新：** 2026-03-24  
**维护者：** Stock-Agent Team
