#!/usr/bin/env python3
"""
自定义主题知识生成器 (优化版 v2)

功能：
- 接收用户输入的主题
- 智能分类或手动指定 Agent
- 执行三轮生成流程
- 结果存储到独立目录

优化改进 v2：
- 引用独立模块（models, utils, services）
- 消除重复代码
- 统一 API Key 获取

用法：
    from custom_topic_generator import CustomTopicGenerator

    generator = CustomTopicGenerator()
    result = generator.generate("微服务架构")
    result = generator.generate("微服务架构", agent="engineering_worker")
"""

import os
import sys
import json
import yaml
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import re

from dotenv import load_dotenv

env_file = Path(__file__).parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

# 引用新模块
from models.agent import AsyncSubAgent
from models.custom_topic import CustomTopicResult
from services.agent_factory import create_agents_from_config, create_classifier_agent, get_api_config
from services.llm_client import LLMClient
from utils.knowledge_parser import parse_knowledge
from utils.prompt_builder import build_keypoint_question, build_custom_topic_question
from utils.logger import setup_logger
from core.knowledge_utils import count_keypoints

# 使用统一的 logger
logger = setup_logger("custom_topic", "custom_topic.log")


class CustomTopicGenerator:
    """自定义主题知识生成器"""

    AGENT_MAPPING = {
        "theory_worker": {"layer": 1, "name": "基础理论层"},
        "tech_stack_worker": {"layer": 2, "name": "技术栈层"},
        "core_skill_worker": {"layer": 3, "name": "核心能力层"},
        "engineering_worker": {"layer": 4, "name": "工程实践层"},
        "interview_worker": {"layer": 5, "name": "面试准备层"},
        "faq_worker": {"layer": 6, "name": "FAQ"},
    }

    def __init__(
        self,
        config_path: str = "config/agent_config.yaml",
        custom_config_path: str = "config/custom_topic_config.yaml",
        enable_cache: bool = True,
    ):
        self.config_path = Path(config_path)
        self.custom_config_path = Path(custom_config_path)
        self.agent_config = self._load_config(self.config_path)
        self.custom_config = self._load_custom_config()
        self.enable_cache = enable_cache
        
        self.output_dir = Path(self.custom_config.get("storage", {}).get("output_dir", "data/custom_topics/"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._agents: Dict[str, AsyncSubAgent] = {}
        self._classifier_agent: Optional[AsyncSubAgent] = None
        self._initialized = False

    def _load_config(self, config_path: Path) -> Dict:
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {}

    def _load_custom_config(self) -> Dict:
        if self.custom_config_path.exists():
            with open(self.custom_config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {
            "classifier": {"enabled": True, "rules": {}},
            "generation": {"rounds": {"details": {"enabled": True}, "relation": {"enabled": False}}},
            "storage": {"output_dir": "data/custom_topics/", "index_file": "custom_topics_index.json"},
        }

    def initialize(self):
        """初始化生成器"""
        if self._initialized:
            return
        
        logger.info("🚀 初始化自定义主题生成器")
        
        self._agents = self._create_agents()
        
        classifier_enabled = self.custom_config.get("classifier", {}).get("enabled", True)
        if classifier_enabled:
            self._classifier_agent = self._create_classifier_agent()
        
        self._initialized = True
        logger.info(f"✅ 已创建 {len(self._agents)} 个生成 Agent")

    async def async_initialize(self):
        """异步初始化"""
        self.initialize()

    def _create_agents(self) -> Dict[str, AsyncSubAgent]:
        """创建 Agent（引用统一模块）"""
        return create_agents_from_config(self.agent_config, self.enable_cache, agent_filter=self.AGENT_MAPPING)

    def _create_classifier_agent(self) -> AsyncSubAgent:
        """创建分类 Agent（引用统一模块）"""
        return create_classifier_agent(self.agent_config)

    def generate(
        self,
        topic: str,
        agent: str = None,
        description: str = "",
        skip_details: bool = None,
        skip_relation: bool = None,
    ) -> CustomTopicResult:
        """生成自定义主题（同步入口）"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self._async_generate(topic, agent, description, skip_details, skip_relation)
        )

    async def _async_generate(
        self,
        topic: str,
        agent: str = None,
        description: str = "",
        skip_details: bool = None,
        skip_relation: bool = None,
    ) -> CustomTopicResult:
        """异步生成自定义主题"""
        if not self._initialized:
            await self.async_initialize()
        
        topic_id = f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info("=" * 60)
        logger.info(f"🔄 开始生成自定义主题：{topic}")
        logger.info("=" * 60)
        
        if not agent:
            agent = await self._classify_topic(topic, description)
            if not agent:
                agent = self._classify_by_keywords(topic)
            logger.info(f"   🏷️ 智能分类结果：{agent}")
        
        if agent not in self._agents:
            logger.error(f"❌ Agent 不存在：{agent}")
            return CustomTopicResult(
                topic_id=topic_id,
                topic_name=topic,
                agent=agent,
                success=False,
                error=f"Agent '{agent}' 不存在或未启用",
                created_at=datetime.now().isoformat(),
            )
        
        selected_agent = self._agents[agent]
        layer_info = self.AGENT_MAPPING.get(agent, {"layer": 0, "name": "自定义"})
        
        gen_config = self.custom_config.get("generation", {})
        rounds_config = gen_config.get("rounds", {})
        
        final_skip_details = skip_details if skip_details is not None else not rounds_config.get("details", {}).get("enabled", True)
        final_skip_relation = skip_relation if skip_relation is not None else not rounds_config.get("relation", {}).get("enabled", False)
        
        logger.info(f"   📍 层级：{layer_info['name']} (Layer-{layer_info['layer']})")
        logger.info(f"   ⚙️  配置：跳过详情={final_skip_details}, 跳过关联={final_skip_relation}")
        
        try:
            question = self._build_custom_question(topic, layer_info["layer"], description)
            answer = await selected_agent.ask(question, max_retries=2)
            
            if not answer.get("success"):
                return CustomTopicResult(
                    topic_id=topic_id,
                    topic_name=topic,
                    agent=agent,
                    success=False,
                    error=answer.get("error", "生成失败"),
                    created_at=datetime.now().isoformat(),
                )
            
            knowledge = self._parse_knowledge(answer.get("content", ""), topic)
            
            if not final_skip_details:
                logger.info(f"   📝 开始生成知识点详情...")
                knowledge = await self._generate_keypoint_details(
                    selected_agent, knowledge, topic, layer_info["layer"]
                )
            
            if not final_skip_relation:
                logger.info(f"   🔗 开始生成知识关联...")
                knowledge = await self._generate_relation(
                    selected_agent, knowledge, topic, layer_info["layer"]
                )
            
            knowledge["custom_topic"] = True
            knowledge["generated_by"] = "custom_topic_generator"
            knowledge["agent"] = agent
            knowledge["layer"] = layer_info["layer"]
            knowledge["layer_name"] = layer_info["name"]
            knowledge["created_at"] = datetime.now().isoformat()
            knowledge["topic_id"] = topic_id
            
            self._save_result(topic_id, knowledge)
            self._update_index(topic_id, topic, agent, True)
            
            keypoint_count = self._count_keypoints(knowledge)
            
            logger.info("=" * 60)
            logger.info(f"✅ 自定义主题生成完成：{topic}")
            logger.info(f"   Agent：{agent}")
            logger.info(f"   知识点：{keypoint_count} 个")
            logger.info(f"   存储位置：{self.output_dir / f'{topic_id}.json'}")
            logger.info("=" * 60)
            
            return CustomTopicResult(
                topic_id=topic_id,
                topic_name=topic,
                agent=agent,
                success=True,
                knowledge=knowledge,
                created_at=datetime.now().isoformat(),
                keypoint_count=keypoint_count,
            )
            
        except Exception as e:
            logger.error(f"❌ 生成异常：{e}")
            self._update_index(topic_id, topic, agent, False, str(e))
            return CustomTopicResult(
                topic_id=topic_id,
                topic_name=topic,
                agent=agent,
                success=False,
                error=str(e),
                created_at=datetime.now().isoformat(),
            )

    async def _classify_topic(self, topic: str, description: str = "") -> str:
        """使用 LLM 智能分类主题"""
        if not self._classifier_agent:
            return None
        
        try:
            classify_prompt = f"""
请分析以下主题，判断最适合生成该主题知识的 Agent 类型。

主题名称：{topic}
主题描述：{description or '无'}

可选的 Agent 类型：
- theory_worker：基础理论、算法原理、数学基础
- tech_stack_worker：技术栈、开发工具、编程语言
- core_skill_worker：核心能力、系统设计、架构模式
- engineering_worker：工程实践、项目实战、部署运维
- interview_worker：面试准备、求职技巧、软技能
- faq_worker：FAQ 问答、自定义主题、知识扩展

请直接返回 JSON 格式：
{{"agent": "xxx_worker", "reason": "分类原因"}}
"""
            
            result = await self._classifier_agent.ask(classify_prompt, max_retries=1)
            
            if result.get("success"):
                content = result.get("content", "")
                match = re.search(r'\{[^}]+\}', content)
                if match:
                    data = json.loads(match.group())
                    return data.get("agent", "")
        except Exception as e:
            logger.warning(f"⚠️  LLM 分类失败：{e}")
        
        return None

    def _classify_by_keywords(self, topic: str) -> str:
        """基于关键词分类主题"""
        rules = self.custom_config.get("classifier", {}).get("rules", {})
        
        topic_lower = topic.lower()
        
        scores = {}
        for agent_name, rule in rules.items():
            keywords = rule.get("keywords", [])
            score = sum(1 for kw in keywords if kw.lower() in topic_lower)
            if score > 0:
                scores[agent_name] = score
        
        if scores:
            best_agent = max(scores.items(), key=lambda x: x[1])[0]
            return best_agent
        
        return "core_skill_worker"

    def _build_custom_question(self, topic_name: str, layer_num: int, description: str = "") -> str:
        """构建自定义主题生成问题"""
        layer_names = {
            1: "基础理论层",
            2: "技术栈层",
            3: "核心能力层",
            4: "工程实践层",
            5: "面试准备层",
            6: "FAQ",
        }
        layer_name = layer_names.get(layer_num, "自定义主题")
        
        desc_context = ""
        if description:
            desc_context = f"""用户描述内容：
{description}

请严格按照以上描述内容生成知识点。每个核心概念、术语、名词都应该成为独立的知识条目。"""
        
        if "名词解释" in topic_name or "术语" in topic_name or "概念" in topic_name:
            json_template = """{
    "topic_name": "{topic_name}",
    "description": "简要说明这个名词解释集的内容范围",
    "terms": [
        {
            "name": "中文术语名称",
            "english": "英文全称或缩写",
            "abbreviation": "常用缩写（如有）",
            "definition": "简洁的定义（50-100字）",
            "detailed_explanation": "详细解释（200-400字，包括作用、原理、特点）",
            "usage_scenario": "使用场景说明",
            "related_terms": ["相关术语1", "相关术语2"],
            "example": "实际应用示例或代码片段（可选）"
        }
    ],
    "total_terms": 术语总数（数字）
}"""
            prompt_type = "名词解释"
        else:
            json_template = """{
    "topic_name": "{topic_name}",
    "description": "详细描述（200-300字，说明该主题的核心内容）",
    "subtopics": [
        {
            "name": "子主题名称",
            "key_points": ["知识点1", "知识点2", "知识点3"],
            "resources": [
                {"type": "book", "title": "书名", "author": "作者"},
                {"type": "course", "title": "课程名", "platform": "平台"},
                {"type": "doc", "title": "文档名", "url": "链接"}
            ],
            "estimated_hours": 10,
            "difficulty": "beginner/intermediate/advanced"
        }
    ],
    "total_hours": 总学习时长（数字）
}"""
            prompt_type = "知识体系"
        
        return """## 任务
根据用户的描述内容，生成"{topic}"主题的{type}内容（{layer}）。

## 用户需求（核心依据）
{desc}

## 输出要求
请严格按照以下 JSON 格式输出：
{json_template}

## 重要提示
1. 只输出 JSON，不要其他内容
2. 确保 JSON 格式正确
3. 知识条目必须基于用户描述内容，不要偏离主题
4. 每个术语/概念都要有详细解释，内容要实用易懂
5. 如果用户描述中提到了具体领域（如"AI Agent开发领域"），请列出该领域的核心术语

""".format(
            topic=topic_name,
            type=prompt_type,
            layer=layer_name,
            desc=desc_context,
            json_template=json_template.replace("{topic_name}", topic_name)
        )

    async def _generate_keypoint_details(
        self, agent: AsyncSubAgent, knowledge: Dict, topic_name: str, layer_num: int
    ) -> Dict:
        """生成知识点详情"""
        # 如果是 terms 格式，已经包含了详细解释，不需要再生成
        if "terms" in knowledge:
            terms = knowledge.get("terms", [])
            logger.info(f"   📝 名词解释格式，共 {len(terms)} 个术语")
            for term in terms:
                term_name = term.get("name", "")
                english = term.get("english", "")
                logger.info(f"      📖 {term_name} ({english})")
            return knowledge
        
        # 如果是 subtopics 格式，需要生成详情
        subtopics = knowledge.get("subtopics", [])
        
        for subtopic in subtopics:
            subtopic_name = subtopic.get("name", "")
            difficulty = subtopic.get("difficulty", "intermediate")
            key_points = subtopic.get("key_points", [])
            
            if not key_points:
                continue
            
            detailed_keypoints = []
            logger.info(f"      📖 子主题：{subtopic_name}")
            
            for key_point in key_points:
                logger.info(f"         ⚡ 知识点：{key_point}")
                
                question = self._build_keypoint_question(topic_name, subtopic_name, key_point, difficulty, layer_num)
                answer = await agent.ask(question, max_retries=2)
                
                if answer.get("success"):
                    detailed_content = self._parse_knowledge(answer.get("content", ""), key_point)
                    detailed_keypoints.append({"key_point": key_point, "detailed_content": detailed_content})
                    logger.info(f"         ✅ 已生成详情")
                else:
                    detailed_keypoints.append({"key_point": key_point, "error": answer.get("error", "Unknown error")})
                    logger.warning(f"         ⚠️  生成失败")
            
            subtopic["detailed_keypoints"] = detailed_keypoints
        
        return knowledge

    def _build_keypoint_question(
        self, topic_name: str, subtopic_name: str, key_point: str, difficulty: str, layer_num: int
    ) -> str:
        """构建知识点详情问题"""
        difficulty_map = {"beginner": "初级", "intermediate": "中级", "advanced": "高级"}
        diff_cn = difficulty_map.get(difficulty, "中级")
        
        json_template = """{
    "key_point": "{key_point}",
    "explanation": "详细解释（500-800字，包括概念定义、原理说明、为什么重要）",
    "core_concepts": [
        {
            "name": "核心概念名",
            "definition": "概念定义",
            "example": "具体例子或代码示例",
            "related_to": ["关联的其他概念"]
        }
    ],
    "common_misunderstandings": [
        {
            "misunderstanding": "常见误解",
            "correction": "正确理解"
        }
    ],
    "practical_application": "实际应用场景（1-2个具体案例）",
    "code_example": "代码示例（如果适用，要可运行、有注释）",
    "difficulty": "{diff_cn}",
    "estimated_study_time": "建议学习时长（分钟）",
    "self_check_questions": ["自测问题1", "自测问题2", "自测问题3"],
    "further_reading": [
        {"type": "article", "title": "文章标题", "url": "链接"}
    ]
}"""
        
        return """## 任务
针对"{topic}"主题中"{subtopic}"子主题的关键知识点进行详细讲解。

## 关键知识点
**{kp}**

## 输出要求
请严格按照以下 JSON 格式输出详细学习内容：
{json_template}

注意：
1. 只输出 JSON，不要其他内容
2. 解释要通俗易懂
3. 代码示例要可运行、有注释
""".format(
            topic=topic_name,
            subtopic=subtopic_name,
            kp=key_point,
            json_template=json_template.replace("{key_point}", key_point).replace("{diff_cn}", diff_cn)
        )

    async def _generate_relation(
        self, agent: AsyncSubAgent, knowledge: Dict, topic_name: str, layer_num: int
    ) -> Dict:
        """生成知识关联"""
        keypoints_summary = []
        for subtopic in knowledge.get("subtopics", []):
            subtopic_name = subtopic.get("name", "")
            for kp in subtopic.get("key_points", []):
                keypoints_summary.append(f"- [{subtopic_name}] {kp}")
        
        keypoints_text = "\n".join(keypoints_summary)
        
        json_template = """{
    "knowledge_graph": {
        "dependencies": [
            {
                "from": "知识点A",
                "to": "知识点B",
                "strength": "strong/medium/weak",
                "reason": "依赖原因"
            }
        ],
        "learning_sequence": ["知识点A → 知识点B → 知识点C"]
    },
    "practice_project": {
        "name": "实践项目名称",
        "description": "项目描述（100-150字）",
        "tasks": ["任务1", "任务2", "任务3"],
        "skills_covered": ["涉及的知识点"],
        "difficulty": "beginner/intermediate/advanced",
        "estimated_hours": 预计完成时间（小时）
    },
    "interview_highlights": {
        "key_questions": ["面试高频问题"],
        "answer_tips": ["答题要点"],
        "depth_level": "需要掌握的深度"
    }
}"""
        
        question = """## 任务
为"{topic}"主题生成知识关联关系和实践项目。

## 已生成的知识点列表
{kp_text}

## 输出要求
请严格按照以下 JSON 格式输出：
{json_template}

注意：只输出 JSON，不要其他内容
""".format(
            topic=topic_name,
            kp_text=keypoints_text,
            json_template=json_template
        )
        
        answer = await agent.ask(question, max_retries=2)
        
        if answer.get("success"):
            relation_data = self._parse_knowledge(answer.get("content", ""), "knowledge_relation")
            knowledge["knowledge_graph"] = relation_data.get("knowledge_graph", {})
            knowledge["practice_project"] = relation_data.get("practice_project", {})
            knowledge["interview_highlights"] = relation_data.get("interview_highlights", {})
        
        return knowledge

    def _parse_knowledge(self, content: str, fallback_name: str) -> Dict:
        """解析 LLM 返回的 JSON 内容（引用统一模块）"""
        return parse_knowledge(content, fallback_name)

    def _count_keypoints(self, knowledge: Dict) -> int:
        """统计知识点数量（引用统一模块）"""
        return count_keypoints(knowledge)

    def _save_result(self, topic_id: str, knowledge: Dict):
        """保存结果到文件"""
        result_file = self.output_dir / f"{topic_id}.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(knowledge, f, ensure_ascii=False, indent=2)
        logger.info(f"   💾 已保存：{result_file}")

    def _update_index(self, topic_id: str, topic_name: str, agent: str, success: bool, error: str = None):
        """更新索引文件"""
        index_file = self.output_dir / self.custom_config.get("storage", {}).get("index_file", "custom_topics_index.json")
        
        index_data = {"topics": []}
        if index_file.exists():
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    index_data = json.load(f)
            except Exception:
                pass
        
        entry = {
            "topic_id": topic_id,
            "topic_name": topic_name,
            "agent": agent,
            "success": success,
            "created_at": datetime.now().isoformat(),
            "error": error,
        }
        index_data["topics"].append(entry)
        index_data["total_count"] = len(index_data["topics"])
        index_data["success_count"] = sum(1 for t in index_data["topics"] if t.get("success"))
        
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

    def list_custom_topics(self) -> List[Dict]:
        """列出所有自定义主题"""
        index_file = self.output_dir / self.custom_config.get("storage", {}).get("index_file", "custom_topics_index.json")
        
        if not index_file.exists():
            return []
        
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)
            return index_data.get("topics", [])
        except Exception:
            return []

    def get_custom_topic(self, topic_id: str) -> Optional[Dict]:
        """获取单个自定义主题详情"""
        result_file = self.output_dir / f"{topic_id}.json"
        
        if not result_file.exists():
            return None
        
        try:
            with open(result_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    async def close(self):
        """关闭 Agent 连接"""
        for agent in self._agents.values():
            try:
                await agent.close()
            except Exception:
                pass
        
        if self._classifier_agent:
            try:
                await self._classifier_agent.close()
            except Exception:
                pass


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="自定义主题知识生成器")
    parser.add_argument("topic", nargs="?", help="主题名称")
    parser.add_argument("--agent", help="指定 Agent")
    parser.add_argument("--description", help="主题描述")
    parser.add_argument("--list", action="store_true", help="列出已生成的主题")
    parser.add_argument("--get", help="获取指定主题详情")
    parser.add_argument("--skip-details", action="store_true", help="跳过知识点详情生成")
    parser.add_argument("--skip-relation", action="store_true", help="跳过知识关联生成")
    
    args = parser.parse_args()
    
    generator = CustomTopicGenerator()
    generator.initialize()
    
    if args.list:
        topics = generator.list_custom_topics()
        print(f"\n📚 已生成的自定义主题：{len(topics)} 个")
        print("-" * 60)
        for t in topics:
            status = "✅" if t.get("success") else "❌"
            print(f"  {status} {t.get('topic_name')} [{t.get('agent')}]")
            print(f"     ID: {t.get('topic_id')}")
            print(f"     时间: {t.get('created_at')}")
        print("-" * 60)
    
    elif args.get:
        topic_data = generator.get_custom_topic(args.get)
        if topic_data:
            print(json.dumps(topic_data, ensure_ascii=False, indent=2))
        else:
            print(f"❌ 未找到主题：{args.get}")
    
    elif args.topic:
        result = generator.generate(
            args.topic,
            agent=args.agent,
            description=args.description,
            skip_details=args.skip_details,
            skip_relation=args.skip_relation,
        )
        
        if result.success:
            print(f"\n✅ 生成成功：{result.topic_name}")
            print(f"   Agent：{result.agent}")
            print(f"   知识点：{result.keypoint_count} 个")
            print(f"   文件：{result.topic_id}.json")
        else:
            print(f"\n❌ 生成失败：{result.error}")
    
    else:
        parser.print_help()