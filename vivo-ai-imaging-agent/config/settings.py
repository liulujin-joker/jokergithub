"""
vivo AI 影像助手 - 智能体配置
竞赛赛道：手机AI助手，未来AI影像体验设计
"""

from dataclasses import dataclass, field
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ModelConfig:
    """LLM 模型配置"""
    provider: str = "deepseek"          # deepseek / openai / vivo
    model_name: str = "deepseek-chat"   # deepseek-chat / gpt-4o-mini / blue-heart-vision
    temperature: float = 0.7
    max_tokens: int = 2048
    api_base: str = "https://api.deepseek.com/v1"
    api_key: Optional[str] = None

    @classmethod
    def from_env(cls) -> "ModelConfig":
        provider = os.getenv("LLM_PROVIDER", "deepseek")
        if provider == "deepseek":
            return cls(
                provider="deepseek",
                model_name=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                api_base=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
                api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            )
        elif provider == "vivo":
            return cls(
                provider="vivo",
                model_name=os.getenv("VIVO_MODEL", "blue-heart-vision"),
                api_base=os.getenv("VIVO_BASE_URL", "https://api.vivo.com.cn/llm/v1"),
                api_key=os.getenv("VIVO_API_KEY", ""),
            )
        else:
            return cls(
                provider=provider,
                model_name=os.getenv("LLM_MODEL", "gpt-4o-mini"),
                api_base=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                api_key=os.getenv("OPENAI_API_KEY", ""),
            )


@dataclass
class ToolConfig:
    """工具系统配置"""
    enabled_tools: List[str] = field(default_factory=lambda: [
        "photo_enhance", "style_transfer", "composition_guide",
        "object_remove", "portrait_beautify", "scene_recognize",
        "color_grading", "smart_crop", "ai_expand", "motion_photo",
    ])
    # 有真实实现的工具（不依赖 API key 即可运行）
    local_tools: List[str] = field(default_factory=lambda: [
        "scene_recognize",      # 传统图像分析 + CLIP API
        "composition_guide",    # PIL + numpy 边缘检测
        "photo_enhance",        # PIL ImageEnhance
        "color_grading",        # PIL + numpy 色彩矩阵
    ])
    # 需要云端 API 的工具
    cloud_tools: List[str] = field(default_factory=lambda: [
        "style_transfer",       # Stable Diffusion / Replicate
        "object_remove",        # SAM + LaMa
        "portrait_beautify",    # MediaPipe + BeautyGAN
        "smart_crop",           # 显著性检测 + 美学评分
        "ai_expand",            # SD Outpainting
        "motion_photo",         # Depth-Anything + 视差
    ])
    max_tools_per_turn: int = 3
    tool_timeout_seconds: int = 30
    # 工具实现模式: "local" (本地计算) / "cloud" (云端 API) / "hybrid" (混合)
    tool_mode: str = "hybrid"


@dataclass
class MemoryConfig:
    """记忆系统配置"""
    short_term_size: int = 10
    long_term_enabled: bool = True
    vector_dim: int = 768
    embedding_model: str = "text2vec-base-chinese"


@dataclass
class AgentConfig:
    """智能体总配置"""
    agent_name: str = "小V影像助手"
    agent_description: str = "vivo AI 影像智能助手，为你的每一张照片注入灵感"
    agent_mode: str = "llm"  # "llm" (真实LLM驱动) / "rule" (规则引擎demo)

    model: ModelConfig = field(default_factory=ModelConfig)
    tools: ToolConfig = field(default_factory=ToolConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)

    multi_modal: bool = True
    stream_output: bool = True
    proactive_suggest: bool = True

    on_device_processing: bool = True
    privacy_filter: bool = True
