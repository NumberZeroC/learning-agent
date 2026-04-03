# 🛑 停止 CCP 会话

如果 CCP 在后台运行，使用以下命令停止：

```bash
# 查找进程
ps aux | grep ccp

# 或查找 Python 进程
ps aux | grep "ccp run"

# 停止进程
kill <PID>

# 或强制停止
kill -9 <PID>
```

---

## 会话管理

如果使用 `process` 工具创建的后台会话：

```bash
# 列出会话
process action=list

# 停止会话
process action=kill sessionId=<会话 ID>
```

---

*最后更新：2026-04-03*
