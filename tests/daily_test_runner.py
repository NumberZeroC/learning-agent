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
    
    # 确保测试目录存在
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # 运行 pytest（使用 stock-agent 的虚拟环境）
    try:
        venv_python = Path('/home/admin/.openclaw/workspace/stock-agent/venv311/bin/python3')
        result = subprocess.run(
            [str(venv_python), '-m', 'pytest', str(TEST_DIR), '-v', '--tb=short'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=300  # 5 分钟超时
        )
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'stdout': '',
            'stderr': '测试超时（>5 分钟）',
            'returncode': -1
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'returncode': -1
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
        error_info = result['stderr'][:500] if result['stderr'] else '未知错误'
        message = f"""❌ 每日测试失败

📊 测试结果：{result['returncode']}
🕐 测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
⚠️ 错误信息：{error_info}
📄 详细报告：{REPORT_FILE}

请尽快修复！
"""
    
    # 发送 QQ 通知
    try:
        subprocess.run([
            'openclaw', 'message', 'send',
            '--target', QQ_TARGET,
            '--message', message
        ], timeout=30)
        print("📬 通知已发送")
    except Exception as e:
        print(f"📬 通知发送失败：{e}")


def save_report(result):
    """保存测试报告"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'success': result['success'],
        'returncode': result['returncode'],
        'error': result['stderr'] if not result['success'] else None
    }
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"📄 报告已保存：{REPORT_FILE}")


def main():
    """主函数"""
    print("="*60)
    print("🧪 Stock-Agent-Web 每日集成测试")
    print("="*60)
    
    # 运行测试
    result = run_tests()
    
    # 保存报告
    save_report(result)
    
    # 发送通知
    send_notification(result)
    
    print("="*60)
    if result['success']:
        print("✅ 测试通过")
    else:
        print("❌ 测试失败")
    print("="*60)
    
    # 返回结果
    sys.exit(0 if result['success'] else 1)


if __name__ == '__main__':
    main()
