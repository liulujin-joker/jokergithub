"""
工具注册中心 - 管理所有AI影像工具

设计理念：
- 插件化架构，工具可动态注册/卸载
- 每个工具自描述（名称、描述、参数schema）
- 统一的调用接口
"""

from typing import Dict, List, Optional, Type, Any
from dataclasses import dataclass, field


@dataclass
class ToolSchema:
    """工具描述 Schema（用于LLM Function Calling）"""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema 格式
    category: str = "imaging"   # imaging / creative / utility
    requires_image: bool = False
    is_destructive: bool = False
    estimated_time_ms: int = 1000  # 预估执行时间


class BaseTool:
    """工具基类"""
    schema: ToolSchema

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行工具，返回结果字典"""
        raise NotImplementedError

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """参数校验"""
        return True

    def get_preview(self, result: Dict[str, Any]) -> Optional[str]:
        """获取预览图URL/base64"""
        return result.get("preview_url")


class ToolRegistry:
    """工具注册中心 - 单例模式"""

    _instance: Optional["ToolRegistry"] = None
    _tools: Dict[str, BaseTool] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
        return cls._instance

    def register(self, tool: BaseTool) -> None:
        """注册工具"""
        self._tools[tool.schema.name] = tool

    def unregister(self, tool_name: str) -> None:
        """注销工具"""
        self._tools.pop(tool_name, None)

    def get(self, tool_name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self._tools.get(tool_name)

    def list_tools(self) -> List[ToolSchema]:
        """列出所有工具"""
        return [t.schema for t in self._tools.values()]

    def get_tool_schemas_for_llm(self) -> List[Dict[str, Any]]:
        """获取用于LLM Function Calling的工具列表"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.schema.name,
                    "description": tool.schema.description,
                    "parameters": tool.schema.parameters,
                }
            }
            for tool in self._tools.values()
        ]

    def execute(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """执行指定工具"""
        tool = self.get(tool_name)
        if not tool:
            return {"success": False, "error": f"工具 '{tool_name}' 未注册"}
        try:
            return tool.execute(**kwargs)
        except Exception as e:
            return {"success": False, "error": str(e)}
