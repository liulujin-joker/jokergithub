"""
数据模型定义 - 智能体核心消息与状态

设计理念：
- 所有消息类型统一为 Message 结构
- AgentState 维护对话上下文与工具执行状态
- ImageIntent 封装用户对影像操作的意图理解
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid


class Role(str, Enum):
    """对话角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class IntentType(str, Enum):
    """用户意图类型"""
    ENHANCE = "enhance"           # 增强优化
    STYLE = "style"               # 风格转换
    COMPOSE = "compose"           # 构图指导
    REMOVE = "remove"             # 物体消除
    BEAUTIFY = "beautify"         # 人像美化
    SCENE = "scene"               # 场景识别
    COLOR = "color"               # 色彩调校
    CROP = "crop"                 # 裁剪构图
    EXPAND = "expand"             # AI扩图
    MOTION = "motion"             # 动态照片
    GENERAL = "general"           # 通用问答
    UNKNOWN = "unknown"           # 未识别


@dataclass
class ImageIntent:
    """用户影像意图 - 从自然语言中解析"""
    intent_type: IntentType
    confidence: float             # 置信度 0-1
    target_description: str       # 目标描述
    parameters: Dict[str, Any] = field(default_factory=dict)
    reference_images: List[str] = field(default_factory=list)  # 参考图base64或路径
    raw_query: str = ""


@dataclass
class PhotoContext:
    """当前照片上下文"""
    has_image: bool = False
    image_path: Optional[str] = None
    image_base64: Optional[str] = None
    exif_info: Dict[str, Any] = field(default_factory=dict)  # 拍摄参数
    scene_label: Optional[str] = None       # 场景标签
    detected_objects: List[str] = field(default_factory=list)
    quality_score: Optional[float] = None   # 图像质量分


@dataclass
class ToolCall:
    """工具调用"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    tool_name: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"       # pending/running/done/error
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class ToolResult:
    """工具执行结果"""
    call_id: str
    success: bool
    data: Optional[Any] = None
    preview_url: Optional[str] = None  # 预览图URL
    message: str = ""


@dataclass
class Message:
    """统一消息结构"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    role: Role = Role.USER
    content: str = ""
    image_base64: Optional[str] = None   # 图片输入
    tool_calls: List[ToolCall] = field(default_factory=list)
    intent: Optional[ImageIntent] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class UserPreference:
    """用户偏好 - 用于长期记忆"""
    user_id: str
    preferred_styles: List[str] = field(default_factory=list)   # 偏好的风格
    common_scenes: List[str] = field(default_factory=list)      # 常拍场景
    editing_habits: Dict[str, Any] = field(default_factory=dict) # 编辑习惯
    favorite_filters: List[str] = field(default_factory=list)   # 收藏滤镜
    interaction_count: int = 0
    last_active: Optional[datetime] = None


@dataclass
class AgentState:
    """智能体运行状态"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    messages: List[Message] = field(default_factory=list)
    current_intent: Optional[ImageIntent] = None
    photo_context: PhotoContext = field(default_factory=PhotoContext)
    pending_tools: List[ToolCall] = field(default_factory=list)
    user_preference: Optional[UserPreference] = None
    phase: str = "idle"  # idle/listening/thinking/acting/responding
