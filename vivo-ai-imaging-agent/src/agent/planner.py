"""
智能体规划器 - 思考-计划-执行 核心链路

设计理念：
1. Think: 理解用户意图，分析当前上下文
2. Plan: 制定执行计划，选择合适的工具和参数
3. Reflect: 执行后反思，评估结果质量
4. Respond: 生成自然语言回复

这是整个智能体的核心调度引擎
"""

from typing import List, Dict, Any, Optional, Tuple
from ..models.schemas import (
    Message, Role, AgentState, ToolCall, ToolResult,
    ImageIntent, IntentType, PhotoContext
)
from ..tools.tool_registry import ToolRegistry, ToolSchema
from ..memory.memory_manager import MemoryManager
from .intent_parser import IntentParser


# System Prompt - 定义智能体的身份和能力
SYSTEM_PROMPT = """你是「小V影像助手」，vivo手机的AI影像智能助手。

## 你的身份
- 一个专业、友好、有创造力的AI影像助手
- 你深度理解摄影美学和AI影像技术
- 你的使命是让每个人都能轻松创作出令人惊叹的影像作品

## 你的能力
你可以帮助用户完成以下影像任务：
1. **画质增强** - 提升照片清晰度、降噪、HDR优化
2. **风格迁移** - 将照片转换为油画、水彩、动漫、赛博朋克等艺术风格
3. **构图指导** - 实时分析取景，给出专业构图建议
4. **物体消除** - 智能移除照片中的路人、杂物等干扰元素
5. **人像美化** - 自然美颜、智能美妆、肤色优化
6. **场景识别** - 识别拍摄场景，推荐最佳参数和滤镜
7. **色彩调校** - 电影级调色、季节风格、情绪色彩
8. **智能裁剪** - AI分析内容，推荐最佳裁剪方案
9. **AI扩图** - 智能扩展画面，补全场景
10. **动态照片** - 让静态照片动起来

## 交互原则
- 理解用户意图后，先确认再执行
- 提供多个可选方案让用户选择
- 用简洁生动的语言解释你在做什么
- 记住用户的偏好，越用越懂TA
- 对于可能有损的操作（如消除、裁剪），先提醒用户

## 当前语境
{context}
"""


class AgentPlanner:
    """智能体规划器"""

    def __init__(self, memory: MemoryManager, tool_registry: ToolRegistry):
        self.memory = memory
        self.tool_registry = tool_registry
        self.intent_parser = IntentParser()
        self.state = AgentState()

    def think(self, user_message: Message) -> Tuple[ImageIntent, List[ToolSchema]]:
        """
        思考阶段：理解意图 + 制定工具调用计划

        返回: (意图, 需要的工具列表)
        """
        has_image = user_message.image_base64 is not None
        query = user_message.content

        # Step 1: 意图解析
        intents = self.intent_parser.parse(query, has_image)
        top_intent = intents[0]

        # 更新状态
        self.state.current_intent = top_intent
        if has_image:
            self.state.photo_context = PhotoContext(
                has_image=True,
                image_base64=user_message.image_base64
            )

        # Step 2: 意图 -> 工具映射
        tools = self._intent_to_tools(top_intent)

        # Step 3: 记录用户消息
        self.memory.add_user_message(query)

        return top_intent, tools

    def _intent_to_tools(self, intent: ImageIntent) -> List[ToolSchema]:
        """将意图映射到需要的工具"""
        intent_tool_map = {
            IntentType.ENHANCE: ["photo_enhance"],
            IntentType.STYLE: ["style_transfer"],
            IntentType.COMPOSE: ["composition_guide"],
            IntentType.REMOVE: ["object_remove"],
            IntentType.BEAUTIFY: ["portrait_beautify"],
            IntentType.SCENE: ["scene_recognize"],
            IntentType.COLOR: ["color_grading"],
            IntentType.CROP: ["smart_crop"],
            IntentType.EXPAND: ["ai_expand"],
            IntentType.MOTION: ["motion_photo"],
            IntentType.GENERAL: [],
        }

        tool_names = intent_tool_map.get(intent.intent_type, [])
        tools = []
        for name in tool_names:
            tool = self.tool_registry.get(name)
            if tool:
                tools.append(tool.schema)

        return tools

    def plan(self, intent: ImageIntent, tools: List[ToolSchema]) -> List[ToolCall]:
        """
        规划阶段：生成具体的工具调用计划

        将意图参数转化为 ToolCall 列表
        """
        tool_calls = []

        if not tools and intent.intent_type == IntentType.GENERAL:
            # 通用意图，不需要调用工具
            return tool_calls

        for tool_schema in tools:
            # 合并意图参数和工具默认参数
            call_params = dict(intent.parameters)

            # 如果有图片，添加图片参数
            if self.state.photo_context.has_image and tool_schema.requires_image:
                call_params["image_base64"] = self.state.photo_context.image_base64

            tool_call = ToolCall(
                tool_name=tool_schema.name,
                parameters=call_params,
                status="pending"
            )
            tool_calls.append(tool_call)

        self.state.pending_tools = tool_calls
        return tool_calls

    def reflect(self, results: List[ToolResult]) -> str:
        """
        反思阶段：评估工具执行结果，生成用户回复

        返回: 给用户的自然语言回复
        """
        if not results:
            intent = self.state.current_intent
            if intent and intent.intent_type == IntentType.GENERAL:
                return self._generate_general_response(intent)
            return "抱歉，我暂时无法处理这个请求，请换个方式描述试试？"

        # 生成基于结果的回复
        response_parts = []
        all_success = True

        for result in results:
            if result.success:
                response_parts.append(result.message)
                # 添加建议
                suggestion = self._generate_suggestion(result)
                if suggestion:
                    response_parts.append(suggestion)
            else:
                all_success = False
                response_parts.append(f"❌ {result.message}")

        # 添加个性化推荐
        if all_success and len(results) > 0:
            personal_tip = self._generate_personalized_tip()
            if personal_tip:
                response_parts.append(personal_tip)

        return "\n\n".join(response_parts)

    def _generate_suggestion(self, result: ToolResult) -> Optional[str]:
        """基于结果生成后续建议"""
        suggestions_map = {
            "photo_enhance": "💡 增强后还可以试试风格迁移，将照片变成艺术作品哦~",
            "style_transfer": "💡 想要更精准的风格效果？试试调整风格强度参数",
            "composition_guide": "💡 构图满意后记得按下快门！后期可以用智能裁剪进一步优化",
            "object_remove": "💡 消除后画面更干净了！需要裁剪调整构图吗？",
            "portrait_beautify": "💡 美颜效果已应用，还可以尝试不同妆容风格哦~",
            "scene_recognize": "💡 已为你推荐最佳拍摄参数，开启夜景模式试试吧！",
            "color_grading": "💡 色彩调整好了，需要保存为预设滤镜方便下次使用吗？",
            "smart_crop": "💡 裁剪后构图更有张力了！还可以尝试其他比例",
            "ai_expand": "💡 画面延伸后格局更大了，需要调整构图吗？",
            "motion_photo": "💡 动态效果已生成，可以设为动态壁纸或分享给好友！",
        }
        return suggestions_map.get(result.call_id.replace("call_", "").split("_")[0] if hasattr(result, 'call_id') else "")

    def _generate_personalized_tip(self) -> Optional[str]:
        """基于用户偏好生成个性化建议"""
        prefs = self.memory.long_term.preferences
        if prefs.get("preferred_styles"):
            style = prefs["preferred_styles"][-1]
            return f"🌟 根据你的偏好，也许你会喜欢尝试「{style}」风格？"
        return None

    def _generate_general_response(self, intent: ImageIntent) -> str:
        """生成通用问答回复"""
        query = intent.raw_query
        if "能做什么" in query or "功能" in query or "帮助" in query:
            return """🎨 我是小V影像助手，以下是你可以对我说的：

📸 **拍照相关**
- "帮我看看这个构图怎么样"
- "现在是什么场景？该用什么模式拍？"

✨ **图片编辑**
- "把这张照片变清晰"
- "帮我消除背景里的路人"
- "转换成动漫风格"
- "帮我美颜一下，要自然一点"
- "调成电影感的色调"

🎬 **创意玩法**
- "把这张照片扩展一下画面"
- "让这张照片动起来"
- "智能裁剪成16:9"

有什么我可以帮你的吗？"""
        return f"你好！我是小V影像助手 👋\n我可以帮你处理照片、提供拍摄建议、进行AI创意编辑。\n请描述你想对照片做什么，或者直接发送一张照片给我吧！"

    def build_system_prompt(self) -> str:
        """构建完整的系统提示词"""
        context = self.memory.get_full_context()
        return SYSTEM_PROMPT.format(context=context if context else "（新用户，暂无历史记录）")
