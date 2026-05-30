#!/usr/bin/env python3
"""
vivo AI 影像助手 智能体 - 手机AI助手，未来AI影像体验设计

中国高校计算机大赛·AIGC创新赛 参赛作品
赛道: 手机AI助手，未来AI影像体验设计

Modes:
  python main.py                      # Interactive (rule-based demo)
  python main.py --llm                # Interactive (LLM-driven, needs DEEPSEEK_API_KEY)
  python main.py --demo               # Demo mode
  python main.py --query "xxx"        # Single query
  python main.py --check              # Check LLM & tools status
"""

import sys
import os
import io

# Force UTF-8 output (fix Windows GBK encoding issues)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.models.schemas import Message, Role
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
    vivo AI 影像助手智能体 - 核心 Agent 类

    Two planner modes:
    - "rule": Regex-based intent parsing (demo/concept)
    - "llm":  LLM-driven with Function Calling (real AI)
    """

    def __init__(self, use_llm: bool = False):
        self.logger = AgentLogger("VivoImagingAgent")
        self.use_llm = use_llm

        # 1. Tool registry
        self.tool_registry = ToolRegistry()
        self._register_all_tools()

        # 2. Memory system
        self.memory = MemoryManager(short_term_size=10)

        # 3. Planner (LLM or rule-based)
        if use_llm:
            from src.agent.llm_planner import LLMPlanner
            self.planner = LLMPlanner(
                memory=self.memory,
                tool_registry=self.tool_registry,
            )
            self.logger.info("Using LLM-driven planner (DeepSeek)")
        else:
            self.planner = AgentPlanner(
                memory=self.memory,
                tool_registry=self.tool_registry,
            )
            self.logger.info("Using rule-based planner (demo mode)")

        # 4. Executor
        self.executor = ToolExecutor(
            tool_registry=self.tool_registry,
            memory=self.memory,
        )

        self.logger.info("vivo AI Imaging Agent initialized!")

    def _register_all_tools(self):
        tools = [
            PhotoEnhanceTool(), StyleTransferTool(), CompositionGuideTool(),
            ObjectRemoveTool(), PortraitBeautifyTool(), SceneRecognizeTool(),
            ColorGradingTool(), SmartCropTool(), AIExpandTool(), MotionPhotoTool(),
        ]
        for tool in tools:
            self.tool_registry.register(tool)
        self.logger.info(f"Registered {len(tools)} AI imaging tools")

    def _load_image(self, image_path: str):
        """Load image from path, return base64"""
        from src.utils.image_utils import ImageProcessor
        return ImageProcessor.load_as_base64(image_path)

    def chat(self, user_input: str, image_path: str = None) -> str:
        """Core chat interface"""
        self.logger.info(f"User: {user_input}")

        # Load image if provided
        image_base64 = None
        if image_path:
            image_base64 = self._load_image(image_path)
            if image_base64:
                self.logger.info(f"Loaded image: {image_path}")

        # Build message
        user_message = Message(
            role=Role.USER,
            content=user_input,
            image_base64=image_base64,
        )

        if self.use_llm:
            return self._chat_llm(user_message)
        else:
            return self._chat_rule(user_message)

    def _chat_llm(self, user_message: Message) -> str:
        """LLM-driven chat pipeline"""
        # Think + Plan: LLM selects tools via Function Calling
        tool_calls = self.planner.think_and_plan(user_message)
        self.logger.info(f"LLM planned {len(tool_calls)} tool call(s)")

        if not tool_calls:
            # No tools needed (pure text response)
            response = self.planner.reflect([], user_message.content)
            self.memory.add_assistant_message(response, actions=[])
            return response

        # Execute tools
        results = self.executor.execute(tool_calls)
        self.logger.info(f"Executed {len(results)} tool(s)")

        # Reflect: LLM generates response from results
        response = self.planner.reflect(results, user_message.content)

        self.memory.add_assistant_message(
            response,
            actions=[tc.tool_name for tc in tool_calls],
        )
        return response

    def _chat_rule(self, user_message: Message) -> str:
        """Rule-based chat pipeline (original demo)"""
        intent, tools = self.planner.think(user_message)
        self.logger.info(f"Intent: {intent.intent_type.value} (confidence: {intent.confidence:.0%})")

        tool_calls = self.planner.plan(intent, tools)
        self.logger.info(f"Planned {len(tool_calls)} tool call(s)")

        results = self.executor.execute(tool_calls)
        response = self.planner.reflect(results)

        self.memory.add_assistant_message(
            response,
            actions=[tc.tool_name for tc in tool_calls],
        )
        return response

    def chat_with_image(self, image_path: str, user_input: str = "") -> str:
        if not user_input:
            user_input = "Analyze this photo for me"
        return self.chat(user_input, image_path)

    def show_capabilities(self) -> str:
        tools = self.tool_registry.list_tools()
        # Check which have real implementations
        try:
            from src.tools.real_tools import has_real_implementation
            real = {t.name: has_real_implementation(t.name) for t in tools}
        except ImportError:
            real = {}

        lines = [
            "=" * 55,
            "  vivo AI Imaging Assistant - Capabilities",
            "=" * 55,
        ]
        for i, tool in enumerate(tools, 1):
            is_real = real.get(tool.name, False)
            badge = "[REAL]" if is_real else "[DEMO]"
            emoji = {
                "photo_enhance": "enhance", "style_transfer": "style",
                "composition_guide": "compose", "object_remove": "remove",
                "portrait_beautify": "beautify", "scene_recognize": "scene",
                "color_grading": "color", "smart_crop": "crop",
                "ai_expand": "expand", "motion_photo": "motion",
            }.get(tool.name, "tool")
            lines.append(f"  {i:2d}. {badge:7s} {tool.name:<20s} {tool.description[:40]}")
        lines.append("=" * 55)
        lines.append(f"  Mode: {'LLM (DeepSeek)' if self.use_llm else 'Rule-based (Demo)'}")
        lines.append(f"  Total: {len(tools)} tools | Real: {sum(1 for v in real.values() if v)} | Demo: {sum(1 for v in real.values() if not v)}")
        return "\n".join(lines)

    def check_status(self) -> str:
        """Check system status"""
        lines = ["=" * 55, "  System Status Check", "=" * 55]

        # LLM status
        if self.use_llm:
            result = self.planner.llm.check_connection()
            if result["ok"]:
                lines.append(f"  LLM: OK ({result['provider']}/{result['model']})")
            else:
                lines.append(f"  LLM: FAILED - {result.get('error', 'unknown')}")
        else:
            lines.append("  LLM: DISABLED (rule-based mode)")

        # Tools status
        try:
            from src.tools.real_tools import has_real_implementation
            tools = self.tool_registry.list_tools()
            real_count = sum(1 for t in tools if has_real_implementation(t.name))
            lines.append(f"  Tools: {len(tools)} total, {real_count} real, {len(tools)-real_count} demo")
        except ImportError:
            lines.append("  Tools: 10 demo (real_tools.py not found)")

        # HF API status
        import os
        from dotenv import load_dotenv
        load_dotenv()
        hf_token = os.getenv("HF_API_TOKEN", "")
        lines.append(f"  HuggingFace API: {'OK (token set)' if hf_token else 'NOT SET (scene recognition uses traditional analysis)'}")

        lines.append("=" * 55)
        return "\n".join(lines)


# ============================================================
# CLI
# ============================================================

def interactive_mode(use_llm: bool = False):
    agent = VivoImagingAgent(use_llm=use_llm)

    mode_label = "LLM (DeepSeek)" if use_llm else "Rule-based"
    print("=" * 55)
    print(f"  vivo AI Imaging Assistant - XiaoV [{mode_label}]")
    print("  Type 'help' | 'demo' | 'check' | 'quit'")
    print("=" * 55)
    print()

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("XiaoV: Goodbye!")
                break

            if user_input.lower() == 'help':
                print(agent.show_capabilities())
                print("\nTry saying:")
                print('  "What scene is this?" (with image)')
                print('  "Enhance this photo"')
                print('  "Convert to anime style"')
                print('  "Check my composition"')
                print('  "Remove passersby from background"')
                continue

            if user_input.lower() == 'demo':
                demo_mode(use_llm)
                continue

            if user_input.lower() == 'check':
                print(agent.check_status())
                continue

            # Handle image path prefix
            image_path = None
            if user_input.startswith("img:"):
                parts = user_input.split(" ", 1)
                image_path = parts[0][4:]
                user_input = parts[1] if len(parts) > 1 else "Analyze this photo"

            response = agent.chat(user_input, image_path)
            print(f"\nXiaoV: {response}\n")

        except KeyboardInterrupt:
            print("\nXiaoV: Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


def demo_mode(use_llm: bool = False):
    agent = VivoImagingAgent(use_llm=use_llm)

    mode_label = "LLM (DeepSeek)" if use_llm else "Rule-based"
    print("=" * 55)
    print(f"  vivo AI Imaging Assistant - Demo [{mode_label}]")
    print("=" * 55)
    print()

    print(agent.show_capabilities())
    print()

    demos = [
        ("Scene Recognition", "What kind of scene is this? What mode should I use?"),
        ("Composition Help", "I'm shooting a city night scene, how's my composition?"),
        ("Style Transfer", "Convert this photo to cyberpunk style"),
        ("Object Removal", "Remove the passersby from the background"),
        ("Portrait Beautify", "Beautify this portrait naturally"),
        ("Enhancement", "What can you help me with?"),
    ]

    for title, query in demos:
        print(f"\n{'='*50}")
        print(f"  [{title}]")
        print(f"  User: {query}")
        print(f"{'='*50}")

        response = agent.chat(query)
        print(f"\n  XiaoV: {response}")
        print()

        import time
        time.sleep(0.3)

    print("\n" + "=" * 55)
    print("  Demo complete! Agent showcased Think-Plan-Execute-Reflect pipeline")
    print("=" * 55)


if __name__ == "__main__":
    use_llm = "--llm" in sys.argv

    if "--check" in sys.argv:
        agent = VivoImagingAgent(use_llm=use_llm)
        print(agent.check_status())
    elif "--demo" in sys.argv:
        demo_mode(use_llm)
    elif "--query" in sys.argv:
        query_idx = sys.argv.index("--query")
        if query_idx + 1 < len(sys.argv):
            query = sys.argv[query_idx + 1]
            agent = VivoImagingAgent(use_llm=use_llm)
            print(agent.chat(query))
        else:
            print("Usage: --query 'your question'")
    else:
        interactive_mode(use_llm)
