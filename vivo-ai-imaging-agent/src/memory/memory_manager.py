"""
记忆管理系统 - 让AI影像助手越用越懂你

设计理念：
- 短期记忆：当前会话上下文，保持对话连贯
- 长期记忆：用户偏好学习，个性化体验
- 影像记忆：记住用户拍过的场景、喜欢的风格、常用的编辑操作
"""

from typing import List, Dict, Optional, Any
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class MemoryItem:
    """记忆条目"""
    content: str
    memory_type: str  # preference / context / behavior / image
    timestamp: datetime = field(default_factory=datetime.now)
    importance: float = 0.5  # 重要性 0-1
    metadata: Dict[str, Any] = field(default_factory=dict)


class ShortTermMemory:
    """短期记忆 - 滑动窗口管理当前对话上下文"""
    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self._buffer: deque = deque(maxlen=max_size)
        self._image_cache: Dict[str, Any] = {}  # 当前会话的图像缓存

    def add(self, item: MemoryItem) -> None:
        self._buffer.append(item)

    def add_image(self, image_id: str, image_data: Dict[str, Any]) -> None:
        self._image_cache[image_id] = image_data

    def get_recent(self, n: int = 5) -> List[MemoryItem]:
        return list(self._buffer)[-n:]

    def get_context_for_prompt(self) -> str:
        """将短期记忆转换为Prompt上下文"""
        recent = self.get_recent(5)
        if not recent:
            return ""
        lines = ["[近期对话上下文]"]
        for item in recent:
            lines.append(f"- {item.content}")
        return "\n".join(lines)

    def clear(self) -> None:
        self._buffer.clear()
        self._image_cache.clear()


class LongTermMemory:
    """长期记忆 - 用户偏好与习惯的持久化存储"""

    def __init__(self):
        self.preferences: Dict[str, Any] = {
            "preferred_styles": [],       # 偏好的风格
            "common_scenes": [],          # 常拍场景
            "editing_habits": {},         # 编辑习惯
            "favorite_filters": [],       # 收藏滤镜
            "shooting_time_preference": {}, # 拍摄时间偏好
            "aesthetic_score_threshold": 0.6,
        }
        self.behavior_patterns: List[Dict] = []  # 行为模式
        self.image_memory: List[Dict] = []       # 影像记忆

    def update_preference(self, key: str, value: Any) -> None:
        """更新用户偏好"""
        if key in self.preferences:
            if isinstance(self.preferences[key], list):
                if value not in self.preferences[key]:
                    self.preferences[key].append(value)
                    if len(self.preferences[key]) > 20:  # 限制长度
                        self.preferences[key] = self.preferences[key][-20:]
            else:
                self.preferences[key] = value

    def record_behavior(self, action: str, params: Dict[str, Any]) -> None:
        """记录用户行为"""
        self.behavior_patterns.append({
            "action": action,
            "params": params,
            "timestamp": datetime.now().isoformat()
        })
        if len(self.behavior_patterns) > 100:
            self.behavior_patterns = self.behavior_patterns[-100:]

    def record_image_edit(self, original: str, edits: List[str], result: str) -> None:
        """记录一次影像编辑操作"""
        self.image_memory.append({
            "original": original,
            "edits": edits,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        if len(self.image_memory) > 50:
            self.image_memory = self.image_memory[-50:]

    def get_personalized_prompt(self) -> str:
        """生成个性化提示"""
        lines = ["[用户偏好]"]
        if self.preferences["preferred_styles"]:
            lines.append(f"- 偏好风格: {', '.join(self.preferences['preferred_styles'][-5:])}")
        if self.preferences["common_scenes"]:
            lines.append(f"- 常拍场景: {', '.join(self.preferences['common_scenes'][-5:])}")
        if self.preferences["favorite_filters"]:
            lines.append(f"- 收藏滤镜: {', '.join(self.preferences['favorite_filters'][-5:])}")
        return "\n".join(lines) if len(lines) > 1 else ""

    def save(self, filepath: str) -> None:
        """持久化到文件"""
        data = {
            "preferences": self.preferences,
            "behavior_patterns": self.behavior_patterns,
            "image_memory": self.image_memory
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, filepath: str) -> None:
        """从文件加载"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.preferences.update(data.get("preferences", {}))
            self.behavior_patterns = data.get("behavior_patterns", [])
            self.image_memory = data.get("image_memory", [])
        except FileNotFoundError:
            pass


class MemoryManager:
    """记忆管理器 - 统一管理短期和长期记忆"""

    def __init__(self, short_term_size: int = 10):
        self.short_term = ShortTermMemory(max_size=short_term_size)
        self.long_term = LongTermMemory()

    def add_user_message(self, content: str, image_id: Optional[str] = None) -> None:
        """记录用户消息"""
        self.short_term.add(MemoryItem(
            content=f"[用户]: {content}",
            memory_type="context",
            importance=0.7,
            metadata={"image_id": image_id} if image_id else {}
        ))

    def add_assistant_message(self, content: str, actions: List[str] = None) -> None:
        """记录助手消息"""
        self.short_term.add(MemoryItem(
            content=f"[助手]: {content}",
            memory_type="context",
            importance=0.5,
            metadata={"actions": actions or []}
        ))

    def add_tool_execution(self, tool_name: str, result: str) -> None:
        """记录工具执行"""
        self.short_term.add(MemoryItem(
            content=f"[工具 {tool_name}]: {result}",
            memory_type="context",
            importance=0.3
        ))

    def learn_preference(self, key: str, value: Any) -> None:
        """学习用户偏好"""
        self.long_term.update_preference(key, value)

    def record_action(self, action: str, params: Dict[str, Any]) -> None:
        """记录行为"""
        self.long_term.record_behavior(action, params)

    def get_full_context(self) -> str:
        """获取完整上下文（短期+长期）"""
        parts = []
        st_context = self.short_term.get_context_for_prompt()
        if st_context:
            parts.append(st_context)
        lt_context = self.long_term.get_personalized_prompt()
        if lt_context:
            parts.append(lt_context)
        return "\n\n".join(parts)

    def clear_session(self) -> None:
        """清除当前会话"""
        self.short_term.clear()
