#!/usr/bin/env python3
"""
启动 CCP Web 服务器
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.web_server import main

if __name__ == '__main__':
    main()
