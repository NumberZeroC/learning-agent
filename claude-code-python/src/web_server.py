"""
CCP Web Server - Web 聊天界面

提供 Web UI 和 WebSocket 支持，实现流式响应
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import AsyncIterator

import structlog
from aiohttp import web, WSMsgType

from .core.session import Session
from .core.agent import AgentLoop
from .tools.registry import get_default_registry
from .llm.anthropic import AnthropicProvider
from .config import load_config

logger = structlog.get_logger(__name__)


class CCPWebServer:
    """CCP Web 服务器"""
    
    def __init__(self, host: str = 'localhost', port: int = 5008):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.sessions: dict[str, Session] = {}
        
        # 设置路由
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_get('/ws/{session_id}', self.handle_websocket)
        self.app.router.add_static('/static', Path(__file__).parent / 'static')
        self.app.router.add_post('/api/chat', self.handle_chat)
        
        # 初始化 LLM 和工具
        import os
        
        # 尝试加载.env 文件
        env_file = Path(__file__).parent.parent / '.env'
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ.setdefault(key.strip(), value.strip())
        
        api_key = os.environ.get('ANTHROPIC_API_KEY', '')
        base_url = os.environ.get('ANTHROPIC_BASE_URL', '')
        model = os.environ.get('ANTHROPIC_MODEL', 'qwen3.5-plus')
        
        # 创建 LLM 配置
        from .models.llm import LLMConfig
        config = LLMConfig(model=model)
        
        self.llm = AnthropicProvider(api_key=api_key, config=config, base_url=base_url)
        self.registry = get_default_registry()
    
    async def handle_index(self, request: web.Request) -> web.Response:
        """处理首页请求"""
        index_html = Path(__file__).parent / 'static' / 'index.html'
        
        if not index_html.exists():
            return web.Response(
                text=self._generate_index_html(),
                content_type='text/html'
            )
        
        return web.FileResponse(index_html)
    
    async def handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        """处理 WebSocket 连接"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        session_id = request.match_info['session_id']
        logger.info("WebSocket connected", session_id=session_id)
        
        # 创建或获取会话
        if session_id not in self.sessions:
            # 设置工作目录为用户空间
            workspace = Path(__file__).parent.parent / 'workspace'
            workspace.mkdir(exist_ok=True)
            
            self.sessions[session_id] = Session(
                id=session_id,
                working_directory=str(workspace)
            )
        
        session = self.sessions[session_id]
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        message = data.get('message', '')
                        
                        if message:
                            # 流式响应
                            await self._stream_response(ws, session, message)
                    
                    except json.JSONDecodeError:
                        await ws.send_json({'error': 'Invalid JSON'})
                
                elif msg.type == WSMsgType.ERROR:
                    logger.error("WebSocket error", error=ws.exception())
        
        finally:
            logger.info("WebSocket disconnected", session_id=session_id)
        
        return ws
    
    async def _stream_response(
        self,
        ws: web.WebSocketResponse,
        session: Session,
        message: str
    ) -> None:
        """流式响应消息"""
        
        # 发送用户消息
        await ws.send_json({
            'type': 'user_message',
            'content': message
        })
        
        try:
            # 创建 ToolContext
            from .tools.base import ToolContext
            context = ToolContext(
                session_id=session.id,
                working_directory=session.working_directory
            )
            
            # 创建 Agent 循环
            agent = AgentLoop(
                llm=self.llm,
                registry=self.registry,
                context=context,
                max_iterations=20
            )
            
            # 执行并流式返回
            async for chunk in self._execute_agent_stream(agent, message):
                await ws.send_json(chunk)
        
        except Exception as e:
            logger.exception("Stream error")
            await ws.send_json({
                'type': 'error',
                'content': str(e)
            })
        
        # 发送结束标记
        await ws.send_json({'type': 'stream_end'})
    
    async def _execute_agent_stream(
        self,
        agent: AgentLoop,
        message: str
    ) -> AsyncIterator[dict]:
        """执行 Agent 并流式返回结果"""
        
        # 思考中
        yield {'type': 'thinking', 'content': '正在思考...'}
        
        try:
            # 执行任务
            result = await agent.run(message)
            
            # 返回结果
            yield {
                'type': 'response',
                'content': result,
                'timestamp': str(asyncio.get_event_loop().time())
            }
        
        except Exception as e:
            yield {
                'type': 'error',
                'content': f'执行错误：{str(e)}'
            }
    
    async def handle_chat(self, request: web.Request) -> web.Response:
        """处理 HTTP 聊天请求（非 WebSocket）"""
        try:
            data = await request.json()
            message = data.get('message', '')
            session_id = data.get('session_id', 'default')
            
            if not message:
                return web.json_response(
                    {'error': 'Message is required'},
                    status=400
                )
            
            # 创建或获取会话
            workspace = Path(__file__).parent.parent / 'workspace'
            workspace.mkdir(exist_ok=True)
            
            if session_id not in self.sessions:
                self.sessions[session_id] = Session(
                    id=session_id,
                    working_directory=str(workspace)
                )
            
            session = self.sessions[session_id]
            
            # 创建 ToolContext
            from .tools.base import ToolContext
            context = ToolContext(
                session_id=session_id,
                working_directory=session.working_directory
            )
            
            # 创建 Agent
            agent = AgentLoop(
                llm=self.llm,
                registry=self.registry,
                context=context
            )
            
            # 执行
            result = await agent.run(message)
            
            return web.json_response({
                'session_id': session_id,
                'response': result,
                'success': True
            })
        
        except Exception as e:
            logger.exception("Chat error")
            return web.json_response(
                {'error': str(e), 'success': False},
                status=500
            )
    
    def _generate_index_html(self) -> str:
        """生成首页 HTML"""
        return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CCP - Claude Code Python</title>
    <!-- Markdown 渲染 -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <!-- 代码高亮 -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/highlight.js@11/styles/github.min.css">
    <script src="https://cdn.jsdelivr.net/npm/highlight.js@11/lib/core.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/highlight.js@11/lib/languages/python.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/highlight.js@11/lib/languages/javascript.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/highlight.js@11/lib/languages/bash.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            width: 90%;
            max-width: 900px;
            height: 90vh;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .header h1 { font-size: 24px; margin-bottom: 5px; }
        .header p { opacity: 0.9; font-size: 14px; }
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .message {
            margin-bottom: 15px;
            display: flex;
            flex-direction: column;
        }
        .message.user {
            align-items: flex-end;
        }
        .message.assistant {
            align-items: flex-start;
        }
        .message-content {
            max-width: 80%;
            padding: 12px 18px;
            border-radius: 18px;
            word-wrap: break-word;
            line-height: 1.6;
        }
        .message.user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-bottom-right-radius: 4px;
        }
        .message.assistant .message-content {
            background: white;
            color: #333;
            border-bottom-left-radius: 4px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        /* Markdown 样式 */
        .message.assistant .message-content markdown {
            display: block;
        }
        .message.assistant .message-content markdown p {
            margin-bottom: 10px;
        }
        .message.assistant .message-content markdown p:last-child {
            margin-bottom: 0;
        }
        .message.assistant .message-content markdown h1,
        .message.assistant .message-content markdown h2,
        .message.assistant .message-content markdown h3 {
            margin-top: 15px;
            margin-bottom: 10px;
            color: #667eea;
        }
        .message.assistant .message-content markdown h1 { font-size: 1.5em; }
        .message.assistant .message-content markdown h2 { font-size: 1.3em; }
        .message.assistant .message-content markdown h3 { font-size: 1.1em; }
        .message.assistant .message-content markdown ul,
        .message.assistant .message-content markdown ol {
            margin-left: 20px;
            margin-bottom: 10px;
        }
        .message.assistant .message-content markdown li {
            margin-bottom: 5px;
        }
        .message.assistant .message-content markdown code {
            background: #f0f0f0;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: "Consolas", "Monaco", monospace;
            font-size: 0.9em;
        }
        .message.assistant .message-content markdown pre {
            background: #f6f8fa;
            padding: 12px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 10px 0;
        }
        .message.assistant .message-content markdown pre code {
            background: transparent;
            padding: 0;
        }
        .message.assistant .message-content markdown blockquote {
            border-left: 4px solid #667eea;
            padding-left: 15px;
            color: #666;
            margin: 10px 0;
        }
        .message.assistant .message-content markdown table {
            border-collapse: collapse;
            width: 100%;
            margin: 10px 0;
        }
        .message.assistant .message-content markdown th,
        .message.assistant .message-content markdown td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        .message.assistant .message-content markdown th {
            background: #f0f0f0;
            font-weight: bold;
        }
        .message.thinking .message-content {
            background: #e0e0e0;
            color: #666;
            font-style: italic;
        }
        .message.error .message-content {
            background: #fee;
            color: #c00;
            border: 1px solid #fcc;
        }
        .input-container {
            padding: 20px;
            background: white;
            border-top: 1px solid #eee;
            display: flex;
            gap: 10px;
        }
        .input-container input {
            flex: 1;
            padding: 12px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.3s;
        }
        .input-container input:focus {
            border-color: #667eea;
        }
        .input-container button {
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 14px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .input-container button:hover {
            transform: scale(1.05);
        }
        .input-container button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        .timestamp {
            font-size: 11px;
            color: #999;
            margin-top: 5px;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .thinking {
            animation: pulse 1.5s infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 CCP - Claude Code Python</h1>
            <p>AI 编程助手 - Web 界面</p>
        </div>
        
        <div class="chat-container" id="chatContainer">
            <div class="message assistant">
                <div class="message-content">
                    你好！我是 CCP，你的 AI 编程助手。有什么可以帮你的吗？
                </div>
            </div>
        </div>
        
        <div class="input-container">
            <input 
                type="text" 
                id="messageInput" 
                placeholder="输入消息... (例如：创建一个 Python 项目)"
                autocomplete="off"
            />
            <button id="sendBtn" onclick="sendMessage()">发送</button>
        </div>
    </div>
    
    <script>
        const sessionId = 'session_' + Date.now();
        let ws = null;
        const chatContainer = document.getElementById('chatContainer');
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        
        // 连接 WebSocket
        function connectWebSocket() {
            ws = new WebSocket(`ws://${location.host}/ws/${sessionId}`);
            
            ws.onopen = () => {
                console.log('WebSocket connected');
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleMessage(data);
            };
            
            ws.onclose = () => {
                console.log('WebSocket disconnected');
                setTimeout(connectWebSocket, 3000);
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        }
        
        // 处理消息
        function handleMessage(data) {
            switch(data.type) {
                case 'user_message':
                    addMessage(data.content, 'user');
                    break;
                case 'thinking':
                    addMessage(data.content, 'thinking');
                    break;
                case 'response':
                    removeThinking();
                    addMessage(data.content, 'assistant');
                    break;
                case 'error':
                    removeThinking();
                    addMessage(data.content, 'error');
                    break;
                case 'stream_end':
                    sendBtn.disabled = false;
                    messageInput.disabled = false;
                    messageInput.focus();
                    break;
            }
        }
        
        // 添加消息到聊天
        function addMessage(content, type) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            
            // Assistant 消息使用 Markdown 渲染
            if (type === 'assistant') {
                const markdownDiv = document.createElement('markdown');
                markdownDiv.innerHTML = marked.parse(content);
                contentDiv.appendChild(markdownDiv);
                
                // 代码高亮
                contentDiv.querySelectorAll('pre code').forEach((block) => {
                    hljs.highlightElement(block);
                });
            } else {
                // 用户消息直接显示文本
                contentDiv.textContent = content;
            }
            
            messageDiv.appendChild(contentDiv);
            
            const timestamp = document.createElement('div');
            timestamp.className = 'timestamp';
            timestamp.textContent = new Date().toLocaleTimeString();
            messageDiv.appendChild(timestamp);
            
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        // 移除思考中消息
        function removeThinking() {
            const thinking = chatContainer.querySelector('.message.thinking');
            if (thinking) {
                thinking.remove();
            }
        }
        
        // 发送消息
        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;
            
            messageInput.value = '';
            messageInput.disabled = true;
            sendBtn.disabled = true;
            
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ message }));
            } else {
                // 降级使用 HTTP
                try {
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message, session_id: sessionId })
                    });
                    const data = await response.json();
                    if (data.success) {
                        addMessage(message, 'user');
                        addMessage(data.response, 'assistant');
                    } else {
                        addMessage('Error: ' + data.error, 'error');
                    }
                } catch (error) {
                    addMessage('Error: ' + error.message, 'error');
                }
                sendBtn.disabled = false;
                messageInput.disabled = false;
                messageInput.focus();
            }
        }
        
        // 回车发送
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        // 初始化连接
        connectWebSocket();
    </script>
</body>
</html>
'''
    
    def run(self) -> None:
        """运行服务器"""
        logger.info(f"Starting CCP Web Server on http://{self.host}:{self.port}")
        web.run_app(
            self.app,
            host=self.host,
            port=self.port,
            print=lambda x: logger.info(x)
        )


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CCP Web Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind')
    parser.add_argument('--port', type=int, default=5008, help='Port to bind')
    
    args = parser.parse_args()
    
    server = CCPWebServer(host=args.host, port=args.port)
    server.run()


if __name__ == '__main__':
    main()
