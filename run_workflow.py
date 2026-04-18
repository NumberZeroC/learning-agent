#!/usr/bin/env python3
"""
🚀 运行知识生成工作流

用法：
    python3 run_workflow.py

输出：
    - data/workflow_results/workflow_YYYYMMDD_HHMMSS.json (完整结果)
    - data/workflow_results/layer_X_workflow.json (按层级分类)
    - data/workflow_results/workflow_summary.json (汇总)
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))


def check_api_key():
    """检查 API Key 是否配置"""
    import os
    from pathlib import Path
    
    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    
    # 尝试从配置文件加载
    if not api_key:
        config_path = Path(__file__).parent / "config" / "agent_config.yaml"
        if config_path.exists():
            try:
                import yaml
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    api_key = config.get("providers", {}).get("dashscope", {}).get("api_key_value", "")
            except Exception:
                pass
    
    # 尝试从 .env 加载
    if not api_key:
        env_path = Path(__file__).parent / ".env"
        if env_path.exists():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("DASHSCOPE_API_KEY="):
                            api_key = line.split("=", 1)[1].strip()
                            break
            except Exception:
                pass
    
    if not api_key:
        print("❌ 错误：未检测到 API Key 配置")
        print()
        print("请配置以下任一方式：")
        print("   1. 环境变量：export DASHSCOPE_API_KEY=sk-xxx")
        print("   2. .env 文件：在项目根目录创建 .env 文件，添加 DASHSCOPE_API_KEY=sk-xxx")
        print("   3. 配置文件：修改 config/agent_config.yaml，添加 api_key_value")
        print()
        print("获取 API Key: https://dashscope.console.aliyun.com/")
        print()
        return False
    
    print(f"✅ API Key 检测通过 (前缀：{api_key[:15]}...)")
    print()
    return True


def main():
    """主函数"""
    print("="*70)
    print("🤖 Learning Agent - 知识生成工作流")
    print("="*70)
    print()
    
    # 检查 API Key
    if not check_api_key():
        print("⚠️  工作流无法启动，请配置 API Key 后重试")
        print()
        print("="*70)
        sys.exit(1)
    
    # 检查知识架构配置文件
    from pathlib import Path
    framework_path = Path("config/knowledge_framework.yaml")
    
    print("📐 知识架构配置：")
    if framework_path.exists():
        print(f"   ✅ 配置文件存在：{framework_path}")
        try:
            import yaml
            with open(framework_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            print(f"   📚 架构名称：{data.get('name', 'Unknown')}")
            print(f"   📊 层级数量：{len(data.get('layers', []))}")
            total_topics = sum(len(layer.get('topics', [])) for layer in data.get('layers', []))
            print(f"   📝 主题总数：{total_topics}")
        except Exception as e:
            print(f"   ⚠️  读取配置文件失败：{e}")
    else:
        print(f"   ⚠️  配置文件不存在：{framework_path}")
        print(f"   🤖 将自动调用大模型生成知识架构...")
    print()
    
    print("🎯 工作流说明：")
    print("   1. 加载/生成知识架构（5 层架构）")
    print("   2. 根据架构图创建知识生成任务")
    print("   3. 5 个子 Agent 层间并发执行（同时工作）")
    print("   4. 每个 Agent 调用 Qwen3.5-Plus 大模型生成知识")
    print("   5. 工作流记录所有回答并保存为 JSON")
    print()
    print("="*70)
    print()
    
    # 导入工作流编排器（在 API Key 检查之后）
    from workflow_orchestrator import WorkflowOrchestrator
    
    # 创建工作流编排器（启用自动生成架构）
    orchestrator = WorkflowOrchestrator(auto_generate_framework=True)
    
    # 显示知识架构详情
    print("📚 知识架构详情：")
    for layer in orchestrator.architecture.get("layers", []):
        layer_num = layer.get("layer", "?")
        layer_name = layer.get("name", "Unknown")
        topics = layer.get("topics", [])
        topic_names = ", ".join([t.get("name", "?") for t in topics])
        print(f"   第{layer_num}层：{layer_name} ({len(topics)}主题)")
        print(f"      └─ {topic_names}")
    print()
    print("="*70)
    print()
    
    # 初始化工作流
    print("⚙️  初始化工作流...")
    orchestrator.initialize()
    print()
    
    # 执行工作流
    result = orchestrator.execute_workflow()
    
    # 打印详细总结
    print()
    print("="*70)
    print("📊 工作流执行总结")
    print("="*70)
    print(f"   工作流 ID:    {result.workflow_id}")
    print(f"   开始时间：    {result.started_at}")
    print(f"   完成时间：    {result.completed_at}")
    print(f"   总任务数：    {result.total_tasks}")
    print(f"   ✅ 成功：     {result.success_count}")
    print(f"   ❌ 失败：     {result.failed_count}")
    print(f"   ⏱️  总耗时：   {result.duration_seconds:.2f}秒")
    print()
    
    # 各层级详情
    print("📚 各层级详情:")
    for layer_num, layer_data in result.layer_results.items():
        topics_count = len(layer_data.get('topics', []))
        agent_name = layer_data.get('agent', 'unknown')
        layer_name = layer_data.get('layer_name', f'第{layer_num}层')
        print(f"   第{layer_num}层 ({layer_name}):")
        print(f"      Agent: {agent_name}")
        print(f"      生成主题数：{topics_count}")
    print()
    print("="*70)
    print()
    print("✅ 工作流完成！结果已保存到 data/workflow_results/ 目录")
    print()
    print("📄 输出文件:")
    print(f"   - data/workflow_results/workflow_{result.workflow_id}.json")
    print(f"   - data/workflow_results/layer_X_workflow.json (各层级)")
    print(f"   - data/workflow_results/workflow_summary.json (汇总)")
    print()


if __name__ == "__main__":
    main()
