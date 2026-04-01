# 🌐 东方财富浏览器自动化测试

**目标：** 使用 Playwright 模拟浏览器获取东方财富实时行情

---

## 📦 安装依赖

```bash
# 创建虚拟环境（可选）
python3 -m venv venv-browser
source venv-browser/bin/activate

# 安装 Playwright
pip install playwright

# 安装浏览器
playwright install chromium

# 可选：安装 Chrome 扩展支持
playwright install chromium --with-deps
```

---

## 🚀 快速测试

```bash
cd /home/admin/.openclaw/workspace/browser-test
python test_single.py
```

---

## 📁 项目结构

```
browser-test/
├── test_single.py          # 单只股票测试
├── test_batch.py           # 批量测试
├── test_realtime.py        # 实时监控测试
├── browser_pool.py         # 浏览器池管理
├── requirements.txt        # 依赖
└── README.md              # 本文档
```

---

## 📊 测试内容

1. **单只股票** - 获取实时价格
2. **批量获取** - 一次获取多只股票
3. **实时监控** - 持续监控价格变化
4. **性能测试** - 响应时间/成功率

---

## ⚠️ 注意事项

1. **请求频率** - 间隔 > 5 秒
2. **使用限制** - 个人学习使用
3. **网络环境** - 确保网络稳定
4. **浏览器缓存** - 使用无痕模式

---

*创建时间：2026-03-27*
