#!/usr/bin/env python3
"""
================================================================================
  vivo AI 影像助手 智能体 - 手机AI助手，未来AI影像体验设计
================================================================================

中国高校计算机大赛·AIGC创新赛 参赛作品

赛道: 手机AI助手，未来AI影像体验设计

这是一个面向未来手机 AI 影像体验的智能体（Agent）系统。
它不仅仅是调用单个AI模型，而是一个具备"感知-思考-规划-行动-反思"
完整链路的智能助手。

核心理念:
  - 从"用户操作工具" 到 "AI理解意图并主动服务"
  - 从"单一功能调用" 到"多工具协同编排"
  - 从"一次性交互" 到"持续学习用户偏好"

运行方式:
  python main.py                    # 交互式对话
  python main.py --demo             # 演示模式
  python main.py --query "帮我把这张照片变成动漫风格"
================================================================================
"""

import sys
import os
import io

# 强制 UTF-8 输出（解决 Windows GBK 编码问题）
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.models.schemas import Message, Role, ImageIntent, IntentType
from src.tools.tool_registry import ToolRegistry
from src.tools.imaging_tools import (
    PhotoEnhanceTool, StyleTransferTool, CompositionGuideTool,
    ObjectRemoveTool, PortraitBeautifyTool, SceneRecognizeTool,
    ColorGradingTool, SmartCropTool, AIExpandTool, MotionPhotoTool
)
from src.memory.memory_manager import MemoryManager
from src.agent.planner import AgentPlanner
from src.agent.executor import ToolExecutor
from src.agent.intent_parser import IntentParser
from src.utils.logger import AgentLogger


class VivoImagingAgent:
    """
    vivo AI 影像助手 智能体

    这是整个系统的核心类，负责:
    1. 初始化所有组件（工具、记忆、规划器、执行器）
    2. 处理用户输入（文字/图片）
    3. 编排 Think -> Plan -> Execute -> Reflect 完整链路
    4. 生成自然语言回复
    """

    def __init__(self):
        self.logger = AgentLogger("VivoImagingAgent")

        # 1. 初始化工具注册中心
        self.tool_registry = ToolRegistry()
        self._register_all_tools()

        # 2. 初始化记忆系统
        self.memory = MemoryManager(short_term_size=10)

        # 3. 初始化规划器（含意图解析）
        self.planner = AgentPlanner(
            memory=self.memory,
            tool_registry=self.tool_registry
        )

        # 4. 初始化执行器
        self.executor = ToolExecutor(
            tool_registry=self.tool_registry,
            memory=self.memory
        )

        self.logger.info("🚀 vivo AI 影像助手智能体初始化完成！")

    def _register_all_tools(self):
        """注册所有AI影像工具"""
        tools = [
            PhotoEnhanceTool(),
            StyleTransferTool(),
            CompositionGuideTool(),
            ObjectRemoveTool(),
            PortraitBeautifyTool(),
            SceneRecognizeTool(),
            ColorGradingTool(),
            SmartCropTool(),
            AIExpandTool(),
            MotionPhotoTool(),
        ]
        for tool in tools:
            self.tool_registry.register(tool)

        self.logger.info(f"已注册 {len(tools)} 个AI影像工具")

    def chat(self, user_input: str, image_path: str = None) -> str:
        """
        核心对话接口

        Args:
            user_input: 用户文字输入
            image_path: 可选的图片路径

        Returns:
            智能体的回复文本
        """
        self.logger.info(f"用户: {user_input}")

        # 加载图片（如果有）
        image_base64 = None
        if image_path:
            from src.utils.image_utils import ImageProcessor
            image_base64 = ImageProcessor.load_as_base64(image_path)
            if image_base64:
                self.logger.info(f"已加载图片: {image_path}")

        # 构建消息
        user_message = Message(
            role=Role.USER,
            content=user_input,
            image_base64=image_base64
        )

        # === Think: 理解意图 ===
        intent, tools = self.planner.think(user_message)
        self.logger.info(f"意图: {intent.intent_type.value} (置信度: {intent.confidence:.0%})")

        # === Plan: 制定计划 ===
        tool_calls = self.planner.plan(intent, tools)
        self.logger.info(f"计划调用 {len(tool_calls)} 个工具")

        # === Execute: 执行工具 ===
        results = self.executor.execute(tool_calls)

        # === Reflect: 反思 & 生成回复 ===
        response = self.planner.reflect(results)

        # 记录助手消息
        self.memory.add_assistant_message(
            response,
            actions=[tc.tool_name for tc in tool_calls]
        )

        self.logger.info(f"助手: {response[:100]}...")
        return response

    def chat_with_image(self, image_path: str, user_input: str = "") -> str:
        """带图片的对话（便捷方法）"""
        if not user_input:
            user_input = "帮我分析一下这张照片"
        return self.chat(user_input, image_path)

    def show_capabilities(self) -> str:
        """展示智能体能力清单"""
        tools = self.tool_registry.list_tools()
        lines = [
            "╔══════════════════════════════════════════╗",
            "║     🎨 vivo AI 影像助手 - 能力清单      ║",
            "╠══════════════════════════════════════════╣",
        ]
        for i, tool in enumerate(tools, 1):
            emoji_map = {
                "photo_enhance": "📸", "style_transfer": "🎨",
                "composition_guide": "📐", "object_remove": "🧹",
                "portrait_beautify": "✨", "scene_recognize": "🔍",
                "color_grading": "🎬", "smart_crop": "✂️",
                "ai_expand": "🔲", "motion_photo": "🎬"
            }
            emoji = emoji_map.get(tool.name, "🔧")
            lines.append(f"║  {i:2d}. {emoji} {tool.name:<20s} - {tool.description[:30]}... ║")
        lines.append("╚══════════════════════════════════════════╝")
        return "\n".join(lines)


def demo_mode():
    """演示模式 - 展示智能体的各种能力"""
    agent = VivoImagingAgent()

    print("=" * 70)
    print("  vivo AI 影像助手 - 智能体演示")
    print("  赛道: 手机AI助手，未来AI影像体验设计")
    print("=" * 70)
    print()

    # 展示能力
    print(agent.show_capabilities())
    print()

    # 演示场景
    demos = [
        ("📸 场景1: 摄影帮助", "我在拍城市夜景，帮我看看构图怎么样"),
        ("🎨 场景2: 风格转换", "帮我把这张照片变成赛博朋克风格"),
        ("🧹 场景3: 物体消除", "帮我把背景里的路人都消掉"),
        ("✨ 场景4: 人像美化", "帮我美颜一下，要自然一点的"),
        ("🔍 场景5: 场景识别", "看看这是什么场景，该用什么模式拍？"),
        ("🆘 场景6: 功能询问", "你能帮我做些什么？"),
    ]

    for title, query in demos:
        print(f"\n{'='*50}")
        print(f"  {title}")
        print(f"  用户: {query}")
        print(f"{'='*50}")

        response = agent.chat(query)
        print(f"\n  小V: {response}")
        print()

        import time
        time.sleep(0.5)

    print("\n" + "=" * 70)
    print("  演示完成！智能体已展示了感知-思考-规划-执行-反思全链路")
    print("=" * 70)


def interactive_mode():
    """交互模式 - 与智能体实时对话"""
    agent = VivoImagingAgent()

    print("=" * 60)
    print("  🎨 vivo AI 影像助手 - 小V")
    print("  输入 'help' 查看帮助 | 'demo' 演示 | 'quit' 退出")
    print("=" * 60)
    print()

    while True:
        try:
            user_input = input("👤 你: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'q', '退出']:
                print("👋 小V: 再见！期待下次为你服务~")
                break

            if user_input.lower() == 'help':
                print(agent.show_capabilities())
                print("\n试试对我说：")
                print('  "帮我把照片变清晰"')
                print('  "转换成动漫风格"')
                print('  "帮我看看构图"')
                print('  "消除照片里的路人"')
                print('  "帮我美颜一下"')
                continue

            if user_input.lower() == 'demo':
                demo_mode()
                continue

            # 检查是否包含图片路径
            image_path = None
            if user_input.startswith("img:"):
                parts = user_input.split(" ", 1)
                image_path = parts[0][4:]
                user_input = parts[1] if len(parts) > 1 else "帮我分析一下这张照片"

            response = agent.chat(user_input, image_path)
            print(f"\n🤖 小V: {response}\n")

        except KeyboardInterrupt:
            print("\n👋 小V: 再见！")
            break
        except Exception as e:
            print(f"\n❌ 出错了: {e}")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo_mode()
    elif "--query" in sys.argv:
        query_idx = sys.argv.index("--query")
        if query_idx + 1 < len(sys.argv):
            query = sys.argv[query_idx + 1]
            agent = VivoImagingAgent()
            print(agent.chat(query))
        else:
            print("请提供查询内容: --query '你的问题'")
    else:
        interactive_mode()
