"""
工具执行器 - 负责按计划调用AI影像工具

设计理念：
- 支持并行/串行工具调用
- 完善的错误处理与重试机制
- 执行过程可视化（进度反馈）
- 安全性检查（隐私、权限）
"""

import asyncio
from typing import List, Dict, Any, Optional
from ..models.schemas import ToolCall, ToolResult
from ..tools.tool_registry import ToolRegistry
from ..memory.memory_manager import MemoryManager


class ToolExecutor:
    """工具执行器"""

    def __init__(self, tool_registry: ToolRegistry, memory: MemoryManager):
        self.registry = tool_registry
        self.memory = memory
        self.max_retries = 2

    def execute(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """
        执行工具调用列表

        根据工具依赖关系决定串行/并行执行
        """
        results = []

        for tool_call in tool_calls:
            result = self._execute_single(tool_call)
            results.append(result)

            # 记录到记忆
            self.memory.add_tool_execution(
                tool_call.tool_name,
                result.message
            )

        return results

    def _execute_single(self, tool_call: ToolCall) -> ToolResult:
        """执行单个工具调用，带重试"""
        for attempt in range(self.max_retries + 1):
            try:
                # 更新状态
                tool_call.status = "running"

                # 执行工具
                result_data = self.registry.execute(
                    tool_call.tool_name,
                    **tool_call.parameters
                )

                if result_data.get("success"):
                    tool_call.status = "done"
                    tool_call.result = result_data
                    return ToolResult(
                        call_id=tool_call.id,
                        success=True,
                        data=result_data,
                        preview_url=result_data.get("preview_url"),
                        message=result_data.get("message", "执行完成")
                    )
                else:
                    raise Exception(result_data.get("error", "未知错误"))

            except Exception as e:
                tool_call.status = "error"
                tool_call.error = str(e)

                if attempt == self.max_retries:
                    return ToolResult(
                        call_id=tool_call.id,
                        success=False,
                        message=f"执行失败: {str(e)}"
                    )

                # 重试前等待
                import time
                time.sleep(0.5 * (attempt + 1))

        return ToolResult(
            call_id=tool_call.id,
            success=False,
            message="已达到最大重试次数"
        )

    async def execute_async(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """异步并行执行多个工具调用"""
        tasks = []
        for tc in tool_calls:
            tasks.append(self._execute_async_single(tc))
        results = await asyncio.gather(*tasks, return_exceptions=True)

        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(ToolResult(
                    call_id=tool_calls[i].id,
                    success=False,
                    message=f"异步执行异常: {str(result)}"
                ))
            else:
                final_results.append(result)

        return final_results

    async def _execute_async_single(self, tool_call: ToolCall) -> ToolResult:
        """异步执行单个工具"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._execute_single, tool_call)
