#!/usr/bin/env python3
"""
Prompt Builder - Prompt 构建工具

构建各类知识生成的 Prompt 模板。
"""

from typing import Optional


# 难度等级映射
DIFFICULTY_MAP = {
    "beginner": "初级",
    "intermediate": "中级",
    "advanced": "高级",
}

# 层级名称映射
LAYER_NAMES = {
    1: "基础理论层",
    2: "技术栈层",
    3: "核心能力层",
    4: "工程实践层",
    5: "面试准备层",
    6: "FAQ",
}


def build_keypoint_question(
    topic_name: str,
    subtopic_name: str,
    key_point: str,
    difficulty: str = "intermediate",
    layer_num: int = 3,
) -> str:
    """
    构建知识点详情生成的 Prompt（第二轮）

    Args:
        topic_name: 主题名称
        subtopic_name: 子主题名称
        key_point: 关键知识点名称
        difficulty: 难度等级
        layer_num: 层级编号

    Returns:
        str: 构建好的 Prompt
    """
    diff_cn = DIFFICULTY_MAP.get(difficulty, "中级")

    interview_context = ""
    if layer_num >= 3:
        interview_context = """
    "interview_frequency": "high/medium/low（该知识点在面试中出现的频率）",
    "interview_questions": ["面试中常见的相关问题"],
"""

    return f"""
## 任务
针对"{topic_name}"主题中"{subtopic_name}"子主题的关键知识点进行详细讲解。

## 背景
这是 AI Agent 开发者学习内容，面向求职者，需要兼顾理论深度和面试实用性。

## 关键知识点
**{key_point}**

## 输出要求
请严格按照以下 JSON 格式输出详细学习内容：
{{
    "key_point": "{key_point}",
    "explanation": "详细解释（500-800 字，包括概念定义、原理说明、为什么重要、与其他知识点的关联）",
    "core_concepts": [
        {{
            "name": "核心概念名",
            "definition": "概念定义",
            "example": "具体例子或代码示例",
            "related_to": ["关联的其他概念"]
        }}
    ],
    "common_misunderstandings": [
        {{
            "misunderstanding": "常见误解",
            "correction": "正确理解"
        }}
    ],
    "practical_application": "实际应用场景（1-2 个具体案例，Agent开发中的应用）",
    "code_example": "Python 代码示例（如果适用，要可运行、有注释）",
    "difficulty": "{diff_cn}",
    "estimated_study_time": "建议学习时长（分钟）",
    "self_check_questions": [
        "自测问题 1（检验核心概念理解）",
        "自测问题 2（检验实际应用能力）",
        "自测问题 3（检验知识关联）"
    ],{interview_context}
    "further_reading": [
        {{ "type": "article", "title": "文章标题", "url": "链接" }},
        {{ "type": "video", "title": "视频标题", "url": "链接" }}
    ]
}}

注意：
1. 只输出 JSON，不要其他内容
2. 解释要通俗易懂，避免过度使用专业术语
3. 代码示例要可运行、有注释，最好是 Agent 开发相关的代码
4. 自测问题要能检验理解程度和实际应用能力
5. 强调该知识点与前后知识点的关联关系
"""


def build_topic_question(
    topic_name: str,
    layer_num: int,
    previous_layer_topics: list = None,
) -> str:
    """
    构建主题结构生成的 Prompt（第一轮）

    Args:
        topic_name: 主题名称
        layer_num: 层级编号
        previous_layer_topics: 上层主题列表（用于知识关联）

    Returns:
        str: 构建好的 Prompt
    """
    layer_name = LAYER_NAMES.get(layer_num, f"第{layer_num}层")

    previous_context = ""
    if previous_layer_topics and layer_num > 1:
        previous_context = f"""
## 已学习的上层知识
第{layer_num-1}层已学习主题：{', '.join(previous_layer_topics)}
这些知识是本主题的前置基础，请在本主题内容中适当引用和关联。
"""

    layer_description = "构建后续所有知识的理论基础" if layer_num == 1 else "承上启下的能力构建层" if layer_num in [2, 3] else "实践应用层"

    return f"""
## 任务
生成第{layer_num}层"{layer_name}"中"{topic_name}"主题的详细学习内容。

## 背景
这是 AI Agent 开发者学习路径的第{layer_num}层。
该层定位：{layer_name} - {layer_description}
{previous_context}

## 输出要求
请严格按照以下 JSON 格式输出：
{{
    "topic_name": "{topic_name}",
    "description": "详细描述（300-500 字，说明该主题在学习路径中的定位和价值）",
    "subtopics": [
        {{
            "name": "子主题名称",
            "key_points": ["知识点 1", "知识点 2", "知识点 3"],
            "resources": [
                {{ "type": "book", "title": "书名", "author": "作者"}},
                {{ "type": "course", "title": "课程名", "platform": "平台"}},
                {{ "type": "doc", "title": "文档名", "url": "链接"}}
            ],
            "estimated_hours": 10,
            "difficulty": "beginner/intermediate/advanced"
        }}
    ],
    "total_hours": 总学习时长（数字），
    "prerequisites": [
        {{
            "knowledge": "前置知识点名称",
            "from_layer": 来源层级（数字）,
            "from_topic": "来源主题名称（如有）",
            "reason": "为什么需要这个前置知识"
        }}
    ],
    "learning_outcomes": ["学习成果 1", "学习成果 2"],
    "learning_sequence": ["建议的学习顺序：先学知识点A，再学知识点B..."]
}}

注意：
1. 只输出 JSON，不要其他内容
2. 确保 JSON 格式正确，所有引号必须是 ASCII 双引号（"），禁止使用中文引号（""）
3. 内容要详细、实用，体现知识点之间的关联性
4. prerequisites 要具体，指明前置知识来自哪个层级/主题
5. 资源要真实有效，优先推荐官方文档和经典书籍
6. 字符串值中如需引用，请使用单引号或转义双引号，不要使用中文引号
"""


def build_relation_question(
    topic_name: str,
    knowledge: dict,
    layer_num: int,
) -> str:
    """
    构建知识关联生成的 Prompt（第三轮）

    Args:
        topic_name: 主题名称
        knowledge: 已生成的知识内容
        layer_num: 层级编号

    Returns:
        str: 构建好的 Prompt
    """
    import json

    keypoints_summary = []
    for subtopic in knowledge.get("subtopics", []):
        subtopic_name = subtopic.get("name", "")
        for kp in subtopic.get("key_points", []):
            keypoints_summary.append(f"- [{subtopic_name}] {kp}")

    keypoints_text = "\n".join(keypoints_summary)
    layer_name = LAYER_NAMES.get(layer_num, f"第{layer_num}层")

    return f"""
## 任务
为"{topic_name}"主题（第{layer_num}层-{layer_name}）生成知识关联关系、实践项目和面试亮点。

## 已生成的知识点列表
{keypoints_text}

## 前置知识
{json.dumps(knowledge.get("prerequisites", []), ensure_ascii=False, indent=2)}

## 输出要求
请严格按照以下 JSON 格式输出：

{{
    "knowledge_graph": {{
        "dependencies": [
            {{
                "from": "知识点名称A",
                "to": "知识点名称B",
                "strength": "strong/medium/weak",
                "reason": "依赖原因（为什么学B之前要先学A）"
            }}
        ],
        "cross_topic_relations": [
            {{
                "concept": "跨主题共享的核心概念",
                "related_topics": ["相关主题名称列表"],
                "related_layers": [相关层级列表]
            }}
        ],
        "learning_sequence": ["知识点A → 知识点B → 知识点C（建议的学习顺序）"]
    }},
    "practice_project": {{
        "name": "实践项目名称",
        "description": "项目描述（100-150字，说明项目背景和目标）",
        "tasks": [
            "任务1：具体任务描述",
            "任务2：具体任务描述",
            "任务3：具体任务描述"
        ],
        "skills_covered": ["涉及的知识点列表"],
        "difficulty": "beginner/intermediate/advanced",
        "estimated_hours": 预计完成时间（小时）,
        "deliverables": ["项目交付物"],
        "evaluation_criteria": ["完成标准"]
    }},
    "interview_highlights": {{
        "frequently_asked": [
            {{
                "question": "高频面试问题",
                "key_knowledge_points": ["涉及的核心知识点"],
                "answer_outline": "回答要点（简短概括）"
            }}
        ],
        "coding_challenges": [
            {{
                "title": "编程挑战题",
                "description": "题目描述",
                "key_knowledge_points": ["涉及的知识点"],
                "difficulty": "easy/medium/hard"
            }}
        ],
        "system_design": [
            {{
                "title": "系统设计题",
                "description": "题目描述",
                "key_knowledge_points": ["涉及的知识点"],
                "design_hints": ["设计思路提示"]
            }}
        ]
    }}
}}

注意：
1. 只输出 JSON，不要其他内容
2. dependencies 要体现知识点之间的逻辑依赖关系
3. practice_project 要结合 Agent 开发实际场景
4. interview_highlights 要标注面试高频考点
5. coding_challenges 和 system_design 主要在面试准备层（第5层），其他层可适当简化
"""


def build_custom_topic_question(
    topic_name: str,
    layer_num: int,
    description: str = "",
    layer_name: str = None,
) -> str:
    """
    构建自定义主题生成的 Prompt

    Args:
        topic_name: 主题名称
        layer_num: 层级编号
        description: 用户提供的描述
        layer_name: 层级名称（可选）

    Returns:
        str: 构建好的 Prompt
    """
    layer_name = layer_name or LAYER_NAMES.get(layer_num, "自定义主题")

    desc_context = ""
    if description:
        desc_context = f"""用户描述内容：
{description}

请严格按照以上描述内容生成知识点。每个核心概念、术语、名词都应该成为独立的知识条目。"""

    # 根据主题类型选择模板
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

    return f"""## 任务
根据用户的描述内容，生成"{topic_name}"主题的{prompt_type}内容（{layer_name}）。

## 用户需求（核心依据）
{desc_context}

## 输出要求
请严格按照以下 JSON 格式输出：
{json_template.replace("{topic_name}", topic_name)}

## 重要提示
1. 只输出 JSON，不要其他内容
2. 确保 JSON 格式正确
3. 知识条目必须基于用户描述内容，不要偏离主题
4. 每个术语/概念都要有详细解释，内容要实用易懂
5. 如果用户描述中提到了具体领域（如"AI Agent开发领域"），请列出该领域的核心术语
"""