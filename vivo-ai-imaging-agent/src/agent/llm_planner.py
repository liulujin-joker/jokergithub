"""
LLM 驱动的智能体规划器

替代原有的正则关键词匹配，使用真实大模型的 Function Calling 能力
来实现意图理解 -> 工具选择 -> 参数提取 -> 结果反思的完整链路。

与原有 planner.py 的区别：
- 原版: 正则匹配意图 -> 硬编码工具映射
- 新版: LLM Function Calling -> 智能选择工具 + 提取参数

兼容性：可通过 --llm 参数切换
"""

import json
from typing import List, Tuple, Optional, Dict, Any
from ..models.schemas import (
    Message, Role, AgentState, ToolCall, ToolResult,
    ImageIntent, IntentType, PhotoContext
)
from ..tools.tool_registry import ToolRegistry, ToolSchema
from ..memory.memory_manager import MemoryManager
from ..llm.client import LLMClient, LLMConfig


# ============================================================
# System Prompt - 定义智能体身份和能力
# ============================================================

AGENT_SYSTEM_PROMPT = """你是小V——vivo手机的AI影像助手。

## 身份
你是专业、友好的AI摄影助手，深度理解摄影美学和AI影像技术。

## 核心规则（最重要）
**当用户的请求匹配任何工具能力时，你必须调用工具，不要只用文字回复。**
即使只是说"帮我看看这张照片"或"分析一下"，也要调用 scene_recognize 工具。

**例外（只用文字回复，不调工具）：**
- 纯问候："你好"、"嗨"、"早上好"、"谢谢"、"辛苦了"、"再见"
- 身份询问："你是谁"、"你能做什么"、"介绍一下自己"（回复能力介绍即可）
- 没有明确影像操作的闲聊（如"今天天气真好"）

**注意：即使用户上传了图片，如果消息是纯问候/感谢/身份询问，仍然只回复文字，不要调工具。**

## 工具触发词（精确匹配）

| 触发词 | 必须调用 |
|--------|---------|
| 增强/优化/更清晰/去噪/修复/HDR/提升画质/变清晰/锐化/还原 | photo_enhance |
| 风格/变成/改成/动漫/赛博朋克/油画/水彩/水墨/素描/复古/黑白/转换 | style_transfer |
| 构图/取景/怎么拍/角度/三分/引导线/分析构图/画面/拍得 | composition_guide |
| 消除/去掉/删除/移除/路人/杂物/水印/抹掉/碍眼/不要 | object_remove |
| 美颜/美妆/瘦脸/美白/磨皮/美化/好看一点/漂亮/P图/修图 | portrait_beautify |
| 什么场景/场景/什么模式/怎么设置参数/拍什么/夜景还是/人像还是/这是什么 | scene_recognize |
| 调色/滤镜/色调/色温/色彩/冷暖/电影感/胶片感/饱和度/白平衡 | color_grading |
| 裁剪/切图/比例/尺寸/横屏/竖屏/正方形/16:9/1:1 | smart_crop |
| 扩图/扩展/补全/延伸/拉远/外扩 | ai_expand |
| 动态/动起来/动画/视差/3D效果/让照片动 | motion_photo |

**优先级规则：当用户说"增强一下"或"变清晰"时，不要调用 scene_recognize，直接调用 photo_enhance。**

## 工具参数说明
- photo_enhance: enhance_level(light/medium/strong), denoise(bool), sharpen(bool), hdr_enhance(bool)
- style_transfer: style(anime/cyberpunk/oil_painting/watercolor/chinese_ink/sketch/minimal_bw/film_retro/emboss), strength(0-1)
- composition_guide: scene_type(auto/portrait/landscape/food/architecture/street)
- object_remove: objects_to_remove(list), auto_detect(bool)
- portrait_beautify: beauty_level(natural/moderate/glamour), skin_smoothing(0-100), whitening(0-100), makeup_style(none/natural/fresh/retro/korean)
- scene_recognize: return_suggestions(bool)
- color_grading: color_preset(auto/cinematic/spring/summer/autumn/winter/moody/vintage/futuristic), temperature(-100~100), saturation(-100~100)
- smart_crop: target_ratio(auto/1:1/4:3/16:9/3:4/9:16)
- ai_expand: expand_direction(all/horizontal/vertical), expand_ratio(float)
- motion_photo: motion_type(parallax_3d/gentle_breeze), duration_seconds(1-10)

## 交互原则
- 每次只调用 1 个最匹配的工具
- 如果用户上传了图片但没有明确说做什么，默认调用 scene_recognize
- 如果用户说了需要图片的操作但没传图片，提醒上传
- 工具执行后，基于返回结果生成简洁专业的回复（不超过120字，口语化）
- 记住用户偏好

## 用户上下文
{context}
"""

REFLECT_SYSTEM_PROMPT = """根据工具执行结果，生成给用户的自然回复。

要求：
- 语气亲切专业，像懂摄影的朋友
- 突出关键数据（评分、置信度、检测到的场景）
- 给出具体的后续建议（如"要不要试试16:9裁剪？"）
- 不超过120字
- 不要用markdown

工具结果：
{results}

用户问题：{user_query}

回复："""


class LLMPlanner:
    """
    LLM 驱动的智能体规划器

    使用真实大模型替代正则匹配，实现：
    - Think: LLM 理解意图 + 通过 Function Calling 选择工具
    - Plan: 解析 LLM 返回的工具调用为 ToolCall 列表
    - Reflect: LLM 根据执行结果生成自然语言回复
    """

    def __init__(
        self,
        memory: MemoryManager,
        tool_registry: ToolRegistry,
        llm_config: Optional[LLMConfig] = None,
    ):
        self.memory = memory
        self.tool_registry = tool_registry
        self.llm = LLMClient(llm_config)
        self.state = AgentState()

    @property
    def llm_available(self) -> bool:
        """Check if LLM is available"""
        try:
            result = self.llm.check_connection()
            return result.get("ok", False)
        except Exception:
            return False

    def build_system_prompt(self) -> str:
        """Build system prompt with memory context"""
        context = self.memory.get_full_context()
        return AGENT_SYSTEM_PROMPT.format(
            context=context if context else "(New user, no history yet)"
        )

    def think_and_plan(self, user_message: Message) -> List[ToolCall]:
        """
        Think + Plan merged: LLM does intent understanding + tool selection + parameter extraction
        via Function Calling in one shot.
        """
        tool_definitions = self.tool_registry.get_tool_schemas_for_llm()
        system_prompt = self.build_system_prompt()
        user_content = user_message.content

        # Image context
        has_image = bool(user_message.image_base64)
        if has_image:
            user_content += "\n[用户已上传图片，请根据意图选择合适的工具处理]"
            self.state.photo_context.has_image = True
            self.state.photo_context.image_base64 = user_message.image_base64

        # Build conversation history for multi-turn context
        messages = [{"role": "system", "content": system_prompt}]

        # Include recent memory as conversation context
        recent_items = self.memory.short_term.get_recent(6)
        for item in recent_items:
            if item.content.startswith("[用户]:"):
                messages.append({"role": "user", "content": item.content[4:]})
            elif item.content.startswith("[助手]:"):
                messages.append({"role": "assistant", "content": item.content[4:]})

        messages.append({"role": "user", "content": user_content})

        # Call LLM with function calling
        try:
            response = self.llm.chat(
                messages=messages,
                tools=tool_definitions,
                tool_choice="auto",
                temperature=0.2,  # Low temp for consistent tool selection
            )
        except Exception as e:
            print(f"[LLMPlanner] LLM call failed: {e}")
            return []

        choice = response.choices[0]
        if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
            llm_tool_calls = []
            for tc in choice.message.tool_calls:
                args = json.loads(tc.function.arguments)
                llm_tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": args,
                })
        else:
            # No tool calls
            self.state._llm_direct_response = choice.message.content
            self.memory.add_user_message(user_message.content)
            return []

        # Convert to ToolCall list
        tool_calls = []
        for tc in llm_tool_calls:
            if tc["name"] == "_text":
                # Pure text response (no tools needed)
                self.state._llm_direct_response = tc["arguments"].get("text", "")
                continue

            params = tc["arguments"]

            # Add image param if tool requires it
            for t in self.tool_registry.list_tools():
                if t.name == tc["name"] and t.requires_image:
                    if self.state.photo_context.has_image:
                        params["image_base64"] = self.state.photo_context.image_base64
                    break

            tool_call = ToolCall(
                id=tc.get("id", ""),
                tool_name=tc["name"],
                parameters=params,
                status="pending",
            )
            tool_calls.append(tool_call)

        # Update state
        self.state.pending_tools = tool_calls
        self.memory.add_user_message(user_message.content)

        return tool_calls

    def reflect(self, results: List[ToolResult], user_query: str) -> str:
        """
        Reflect: LLM generates natural language response from tool results.
        Much more natural than the old hardcoded string concatenation.
        """
        # Handle direct text response (no tool calls needed)
        if not results and hasattr(self.state, '_llm_direct_response'):
            text = self.state._llm_direct_response
            delattr(self.state, '_llm_direct_response')
            if text:
                return text

        if not results:
            return "Sorry, I couldn't process that request. Could you rephrase it?"

        # Format results for the LLM
        results_text = ""
        for i, r in enumerate(results):
            status = "OK" if r.success else "FAILED"
            results_text += f"\nTool {i+1} [{status}]: {r.message}"

        prompt = REFLECT_SYSTEM_PROMPT.format(
            results=results_text,
            user_query=user_query,
        )

        try:
            response = self.llm.simple_chat(
                system_prompt=prompt,
                user_message="Generate reply",
                temperature=0.8,
            )
            return response.strip()
        except Exception as e:
            print(f"[LLMPlanner] Reflect LLM failed, using fallback: {e}")
            return self._fallback_reflect(results)

    def _fallback_reflect(self, results: List[ToolResult]) -> str:
        """Fallback: hardcoded concatenation (same as old planner)"""
        if not results:
            return "Sorry, I couldn't process that request."

        response_parts = []
        for result in results:
            if result.success:
                response_parts.append(f"Done: {result.message}")
            else:
                response_parts.append(f"Failed: {result.message}")

        # Simple follow-up suggestions
        suggestions = {
            "photo_enhance": "Want to try style transfer on the enhanced image?",
            "style_transfer": "Want to adjust the style strength?",
            "object_remove": "Image is cleaner now! Need to crop for better composition?",
            "portrait_beautify": "Want to try different makeup styles?",
            "scene_recognize": "Try shooting with the recommended settings!",
            "color_grading": "Want to save this as a preset filter?",
            "smart_crop": "Want to try other aspect ratios?",
            "ai_expand": "The expanded view has more impact!",
            "motion_photo": "You can set this as a live wallpaper!",
            "composition_guide": "Once satisfied, press the shutter!",
        }

        for r in results:
            for key, tip in suggestions.items():
                if key in r.message.lower():
                    response_parts.append(f"Tip: {tip}")
                    break

        return "\n\n".join(response_parts)
