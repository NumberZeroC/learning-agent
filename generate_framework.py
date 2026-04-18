#!/usr/bin/env python3
"""
知识框架生成脚本

功能：
- 调用大模型生成 AI Agent 开发面试知识体系框架
- 支持预览模式（只显示不保存）
- 支持强制覆盖模式

用法：
    python generate_framework.py              # 生成框架（如已存在则跳过）
    python generate_framework.py --preview    # 预览生成的框架（不保存）
    python generate_framework.py --force      # 强制覆盖现有框架
    python generate_framework.py --view       # 查看现有框架
"""

import os
import sys
import yaml
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
import logging

from dotenv import load_dotenv

env_file = Path(__file__).parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

from services.llm_client import LLMClient

project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))


def setup_logger():
    log_dir = project_dir / "logs"
    log_dir.mkdir(exist_ok=True)

    logger = logging.getLogger("generate_framework")
    logger.setLevel(logging.INFO)

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(console)

    return logger


logger = setup_logger()


FRAMEWORK_PATH = project_dir / "config" / "knowledge_framework.yaml"


SYSTEM_PROMPT = """你是 AI 教育专家和知识架构师，擅长设计系统化的学习路径。

请为"AI Agent 开发岗位面试"设计一个完整的知识体系架构。

## 要求
1. **严格分为 5 个层级**（必须按顺序）：
   - 第 1 层：基础理论层（机器学习、深度学习基础）
   - 第 2 层：技术栈层（Python、框架、工具）
   - 第 3 层：核心能力层（任务规划、工具调用、记忆、多 Agent）
   - 第 4 层：工程实践层（项目、优化、部署）
   - 第 5 层：面试准备层（算法题、系统设计、行为面试）

2. **每层 3-4 个主题**，每个主题包含：
   - name: 主题名称（简洁，2-6 字）
   - priority: 优先级（high/medium）
   
3. **不要添加 subtopics**（由后续工作流自动生成）

4. **输出格式**：严格的 YAML 格式，可直接保存到配置文件

## 输出示例
```yaml
name: Agent 开发面试知识体系
version: "1.0"
description: AI Agent 开发岗位面试知识体系，覆盖从基础理论到面试准备的全链路

layers:
  - layer: 1
    name: 基础理论层
    agent: theory_worker
    description: 机器学习和深度学习基础理论
    topics:
      - name: AI 基础
        priority: high
      - name: LLM 原理
        priority: high

  - layer: 2
    name: 技术栈层
    agent: tech_stack_worker
    description: Agent 开发所需的技术栈和工具
    topics:
      - name: Python 编程
        priority: high

  # ... 其他层级
```

请生成完整的知识架构 YAML。注意：不要添加 subtopics 字段。"""


USER_PROMPT = """请生成 AI Agent 开发面试的完整知识体系架构 YAML。

要求：
1. 5 个层级：基础理论层、技术栈层、核心能力层、工程实践层、面试准备层
2. 每层 3-4 个主题
3. 每个主题只包含 name 和 priority（不要添加 subtopics）
4. 输出可以直接保存的 YAML 格式"""


def get_api_key(config_path: Path) -> str:
    """获取 API Key"""
    api_key = ""
    
    try:
        from services.key_vault import get_key_vault
        vault = get_key_vault()
        api_key = vault.get_key("dashscope") or ""
    except Exception:
        pass
    
    if not api_key:
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                api_key = config.get("providers", {}).get("dashscope", {}).get("api_key_value", "")
            except Exception:
                pass
    
    if not api_key:
        api_key = os.getenv("DASHSCOPE_API_KEY", "")
    
    return api_key


def get_base_url(config_path: Path) -> str:
    """获取 base_url"""
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            return config.get("providers", {}).get("dashscope", {}).get(
                "base_url", "https://coding.dashscope.aliyuncs.com/v1"
            )
        except Exception:
            pass
    return "https://coding.dashscope.aliyuncs.com/v1"


def parse_yaml_from_response(content: str) -> dict:
    """从 LLM 响应中解析 YAML"""
    import re
    
    yaml_match = re.search(r"```yaml\s*([\s\S]*?)\s*```", content)
    if yaml_match:
        yaml_content = yaml_match.group(1)
    else:
        yaml_content = content
    
    try:
        return yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        logger.warning(f"YAML 解析失败：{e}")
        
        lines = yaml_content.strip().split("\n")
        yaml_content_clean = "\n".join([line for line in lines if not line.startswith("```")])
        
        try:
            return yaml.safe_load(yaml_content_clean)
        except yaml.YAMLError:
            return None


def validate_framework(data: dict) -> bool:
    """验证框架结构"""
    if not data:
        return False
    
    if "layers" not in data:
        logger.error("❌ 框架缺少 layers 字段")
        return False
    
    layers = data.get("layers", [])
    if len(layers) != 5:
        logger.error(f"❌ 层级数量不正确：{len(layers)}（应为5）")
        return False
    
    for i, layer in enumerate(layers, 1):
        if layer.get("layer") != i:
            logger.error(f"❌ 第{i}层编号不正确")
            return False
        
        topics = layer.get("topics", [])
        if len(topics) < 3 or len(topics) > 4:
            logger.warning(f"⚠️  第{i}层主题数量：{len(topics)}（建议3-4）")
        
        for topic in topics:
            if "subtopics" in topic:
                logger.warning(f"⚠️  第{i}层主题 '{topic.get('name')}' 包含 subtopics，将被删除")
    
    return True


def clean_framework(data: dict) -> dict:
    """清理框架数据（删除 subtopics）"""
    for layer in data.get("layers", []):
        for topic in layer.get("topics", []):
            if "subtopics" in topic:
                del topic["subtopics"]
    
    return data


def save_framework(data: dict, output_path: Path):
    """保存框架到文件"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    header = f"""# Agent 开发面试知识体系架构
# 版本：{data.get('version', '1.0')}
# 创建日期：{datetime.now().strftime('%Y-%m-%d')}
# 
# 说明：
# - 定义 5 层知识架构（基础理论→技术栈→核心能力→工程实践→面试准备）
# - 每层包含若干主题，每个主题有描述和优先级
# - subtopics 由大模型根据主题自动生成，不再硬编码
# - 增加跨层级知识依赖关系生成

"""
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header)
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    logger.info(f"✅ 框架已保存到：{output_path}")


def view_framework(framework_path: Path):
    """查看现有框架"""
    if not framework_path.exists():
        print(f"❌ 框架文件不存在：{framework_path}")
        return
    
    with open(framework_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    print("\n" + "=" * 60)
    print(f"📚 {data.get('name', '知识框架')}")
    print("=" * 60)
    print(f"版本：{data.get('version', '1.0')}")
    print(f"描述：{data.get('description', '')}")
    print()
    
    for layer in data.get("layers", []):
        layer_num = layer.get("layer", "?")
        layer_name = layer.get("name", "Unknown")
        agent = layer.get("agent", "")
        desc = layer.get("description", "")
        
        print(f"第{layer_num}层：{layer_name}")
        print(f"  Agent: {agent}")
        print(f"  描述: {desc}")
        
        topics = layer.get("topics", [])
        for topic in topics:
            name = topic.get("name", "")
            priority = topic.get("priority", "medium")
            marker = "★" if priority == "high" else "○"
            print(f"  {marker} {name}")
        print()
    
    print("=" * 60)
    total_topics = sum(len(layer.get("topics", [])) for layer in data.get("layers", []))
    print(f"总计：{len(data.get('layers', []))} 层，{total_topics} 个主题")
    print()


async def generate_framework(api_key: str, base_url: str, preview: bool = False, force: bool = False):
    """生成知识框架"""
    
    if FRAMEWORK_PATH.exists() and not force and not preview:
        logger.info(f"📐 框架文件已存在：{FRAMEWORK_PATH}")
        logger.info("   使用 --force 强制覆盖，或 --preview 预览新框架")
        return {"success": False, "reason": "已存在"}
    
    logger.info("=" * 60)
    logger.info("🤖 开始生成知识框架...")
    logger.info("=" * 60)
    
    llm = LLMClient(
        api_key=api_key,
        base_url=base_url,
        model="qwen3.5-plus",
        agent_name="framework_generator",
        enable_cache=False
    )
    
    try:
        logger.info("📝 调用大模型生成框架...")
        result = await llm.async_chat(
            messages=[{"role": "user", "content": USER_PROMPT}],
            system_prompt=SYSTEM_PROMPT,
            max_retries=2
        )
        
        if not result.get("success"):
            logger.error(f"❌ LLM 调用失败：{result.get('error')}")
            return {"success": False, "error": result.get("error")}
        
        content = result.get("content", "")
        logger.info("✅ LLM 响应成功")
        
        data = parse_yaml_from_response(content)
        
        if not data:
            logger.error("❌ 无法解析 YAML 内容")
            logger.info("原始响应：")
            print(content[:500])
            return {"success": False, "error": "YAML解析失败"}
        
        logger.info("🔍 验证框架结构...")
        if not validate_framework(data):
            logger.error("❌ 框架结构验证失败")
            return {"success": False, "error": "结构验证失败"}
        
        logger.info("🧹 清理框架数据...")
        data = clean_framework(data)
        
        if preview:
            logger.info("\n📋 预览生成的框架：")
            print("\n" + yaml.dump(data, allow_unicode=True, default_flow_style=False))
            return {"success": True, "preview": True, "data": data}
        
        save_framework(data, FRAMEWORK_PATH)
        
        logger.info("\n📊 生成的框架统计：")
        logger.info(f"   层级数：{len(data.get('layers', []))}")
        total_topics = sum(len(layer.get("topics", [])) for layer in data.get("layers", []))
        logger.info(f"   主题总数：{total_topics}")
        
        return {"success": True, "data": data}
        
    except Exception as e:
        logger.error(f"❌ 生成异常：{e}")
        return {"success": False, "error": str(e)}
    
    finally:
        await llm.async_close()


def main():
    parser = argparse.ArgumentParser(description="生成 AI Agent 开发面试知识框架")
    parser.add_argument("--preview", action="store_true", help="预览生成的框架（不保存）")
    parser.add_argument("--force", action="store_true", help="强制覆盖现有框架")
    parser.add_argument("--view", action="store_true", help="查看现有框架")
    
    args = parser.parse_args()
    
    if args.view:
        view_framework(FRAMEWORK_PATH)
        return
    
    config_path = project_dir / "config" / "agent_config.yaml"
    
    api_key = get_api_key(config_path)
    if not api_key:
        print("❌ 错误：未配置 API Key")
        print("请配置以下任一方式：")
        print("   1. 环境变量：export DASHSCOPE_API_KEY=sk-xxx")
        print("   2. .env 文件：DASHSCOPE_API_KEY=sk-xxx")
        print("   3. Key Vault：python -c \"from services.key_vault import get_key_vault; get_key_vault().save_key('dashscope', 'sk-xxx')\"")
        return
    
    print(f"✅ API Key 检测通过 (前缀：{api_key[:15]}...)")
    print()
    
    base_url = get_base_url(config_path)
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(
        generate_framework(api_key, base_url, args.preview, args.force)
    )
    
    print()
    if result.get("success"):
        if result.get("preview"):
            print("✅ 预览完成（框架未保存）")
            print("   使用不带 --preview 的命令来保存框架")
        else:
            print("✅ 知识框架生成成功！")
            print(f"   文件位置：{FRAMEWORK_PATH}")
            print()
            print("下一步：")
            print("   python run_workflow.py      # 运行知识生成工作流")
            print("   python generate_framework.py --view   # 查看框架详情")
    else:
        if result.get("reason") == "已存在":
            print("⚠️  框架文件已存在，未生成新框架")
        else:
            print(f"❌ 生成失败：{result.get('error')}")


if __name__ == "__main__":
    main()