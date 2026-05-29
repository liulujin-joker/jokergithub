"""
vivo AI 影像助手 - 智能体配置
竞赛赛道：手机AI助手，未来AI影像体验设计
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ModelConfig:
    """LLM 模型配置"""
    provider: str = "vivo"  # vivo 蓝心大模型 / 可替换为 OpenAI 等
    model_name: str = "blue-heart-vision"
    temperature: float = 0.7
    max_tokens: int = 2048
    api_base: str = "https://api.vivo.com.cn/llm/v1"
    api_key: Optional[str] = None


@dataclass
class ToolConfig:
    """工具系统配置"""
    # 影像工具
    enabled_tools: List[str] = field(default_factory=lambda: [
        "photo_enhance",       # 智能增强
        "style_transfer",      # 风格迁移
        "composition_guide",   # 构图指导
        "object_remove",       # 物体消除
        "portrait_beautify",   # 人像美化
        "scene_recognize",     # 场景识别
        "color_grading",       # 色彩调校
        "smart_crop",          # 智能裁剪
        "ai_expand",           # AI扩图
        "motion_photo",        # 动态照片
    ])
    max_tools_per_turn: int = 3
    tool_timeout_seconds: int = 30


@dataclass
class MemoryConfig:
    """记忆系统配置"""
    short_term_size: int = 10     # 短期记忆（最近对话轮次）
    long_term_enabled: bool = True  # 长期记忆（用户偏好）
    vector_dim: int = 768
    embedding_model: str = "text2vec-base-chinese"


@dataclass
class AgentConfig:
    """智能体总配置"""
    # 智能体身份
    agent_name: str = "小V影像助手"
    agent_description: str = "vivo AI 影像智能助手，为你的每一张照片注入灵感"

    # 核心组件
    model: ModelConfig = field(default_factory=ModelConfig)
    tools: ToolConfig = field(default_factory=ToolConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)

    # 交互模式
    multi_modal: bool = True     # 多模态（支持语音/文字/图像输入）
    stream_output: bool = True   # 流式输出
    proactive_suggest: bool = True  # 主动建议

    # 安全与隐私
    on_device_processing: bool = True  # 端侧处理优先
    privacy_filter: bool = True        # 隐私过滤
