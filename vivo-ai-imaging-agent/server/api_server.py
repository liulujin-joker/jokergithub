"""
小V影像助手 - FastAPI 后端服务

将 VivoImagingAgent 暴露为 REST API，供 Web/Flutter 前端调用。

启动: python server/api_server.py
端口: 8000
"""

import sys
import os
import io
import json
import base64
import uuid
from pathlib import Path
from typing import Optional

# Fix encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.models.schemas import Message, Role
from src.tools.tool_registry import ToolRegistry
from src.tools.imaging_tools import (
    PhotoEnhanceTool, StyleTransferTool, CompositionGuideTool,
    ObjectRemoveTool, PortraitBeautifyTool, SceneRecognizeTool,
    ColorGradingTool, SmartCropTool, AIExpandTool, MotionPhotoTool
)
from src.memory.memory_manager import MemoryManager
from src.agent.llm_planner import LLMPlanner
from src.agent.executor import ToolExecutor
from src.utils.image_utils import ImageProcessor

# ---- FastAPI App ----
app = FastAPI(
    title="小V影像助手 API",
    description="vivo AI 影像智能体后端服务",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Models ----
class ChatRequest(BaseModel):
    content: str


class ChatResponse(BaseModel):
    id: str
    content: str
    tool_calls: list = []
    preview_url: Optional[str] = None


# ---- Agent Singleton ----
_agent = None
_agent_instance = None


def get_agent():
    """懒初始化 Agent（含 LLM Planner）"""
    global _agent, _agent_instance
    if _agent is None:
        registry = ToolRegistry()
        tools = [
            PhotoEnhanceTool(), StyleTransferTool(), CompositionGuideTool(),
            ObjectRemoveTool(), PortraitBeautifyTool(), SceneRecognizeTool(),
            ColorGradingTool(), SmartCropTool(), AIExpandTool(), MotionPhotoTool(),
        ]
        for t in tools:
            registry.register(t)

        memory = MemoryManager(short_term_size=10)
        planner = LLMPlanner(memory=memory, tool_registry=registry)
        executor = ToolExecutor(tool_registry=registry, memory=memory)

        _agent_instance = {
            "registry": registry,
            "memory": memory,
            "planner": planner,
            "executor": executor,
        }
        _agent = True
    return _agent_instance


# ---- Routes ----

@app.get("/")
async def root():
    """返回聊天界面"""
    web_path = PROJECT_ROOT / "server" / "chat.html"
    if web_path.exists():
        return HTMLResponse(web_path.read_text(encoding="utf-8"))
    return {"message": "小V影像助手 API v2.0", "docs": "/docs"}


@app.get("/health")
async def health():
    """健康检查"""
    agent = get_agent()
    llm_status = agent["planner"].llm.check_connection()
    return {
        "status": "ok",
        "version": "2.0.0",
        "llm": llm_status,
        "tools": len(agent["registry"].list_tools()),
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """文字对话"""
    if not request.content.strip():
        raise HTTPException(status_code=400, detail="Empty message")

    agent = get_agent()
    user_msg = Message(role=Role.USER, content=request.content)

    try:
        # Think + Plan
        tool_calls = agent["planner"].think_and_plan(user_msg)

        if not tool_calls:
            # Pure text response
            response_text = agent["planner"].reflect([], request.content)
            agent["memory"].add_assistant_message(response_text, actions=[])
            return ChatResponse(
                id=str(uuid.uuid4())[:8],
                content=response_text,
            )

        # Execute
        results = agent["executor"].execute(tool_calls)

        # Reflect
        response_text = agent["planner"].reflect(results, request.content)
        agent["memory"].add_assistant_message(
            response_text,
            actions=[tc.tool_name for tc in tool_calls],
        )

        # Extract preview if any
        preview_url = None
        for r in results:
            if r.success and r.preview_url:
                preview_url = r.preview_url
                break

        return ChatResponse(
            id=str(uuid.uuid4())[:8],
            content=response_text,
            tool_calls=[
                {"name": tc.tool_name, "status": "done"}
                for tc in tool_calls
            ],
            preview_url=preview_url,
        )

    except Exception as e:
        return ChatResponse(
            id=str(uuid.uuid4())[:8],
            content=f"抱歉，处理请求时出错了：{str(e)}\n\n请检查 LLM 连接状态。",
        )


@app.post("/chat/image", response_model=ChatResponse)
async def chat_with_image(
    content: str = Form(default="分析一下这张照片"),
    image: UploadFile = File(...),
):
    """带图片的对话"""
    agent = get_agent()

    # Read and encode image
    image_bytes = await image.read()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    user_msg = Message(
        role=Role.USER,
        content=content,
        image_base64=image_b64,
    )

    try:
        # Set photo context
        agent["planner"].state.photo_context.has_image = True
        agent["planner"].state.photo_context.image_base64 = image_b64

        tool_calls = agent["planner"].think_and_plan(user_msg)

        if not tool_calls:
            response_text = agent["planner"].reflect([], content)
            return ChatResponse(id=str(uuid.uuid4())[:8], content=response_text)

        results = agent["executor"].execute(tool_calls)
        response_text = agent["planner"].reflect(results, content)

        preview_url = None
        for r in results:
            if r.success and r.preview_url:
                preview_url = r.preview_url
                break

        return ChatResponse(
            id=str(uuid.uuid4())[:8],
            content=response_text,
            tool_calls=[
                {"name": tc.tool_name, "status": "done"}
                for tc in tool_calls
            ],
            preview_url=preview_url,
        )

    except Exception as e:
        return ChatResponse(
            id=str(uuid.uuid4())[:8],
            content=f"图片处理出错：{str(e)}",
        )


@app.get("/tools")
async def list_tools():
    """列出所有工具及状态"""
    try:
        from src.tools.real_tools import has_real_implementation
    except ImportError:
        has_real_implementation = lambda _: False

    agent = get_agent()
    tools = agent["registry"].list_tools()

    return {
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "requires_image": t.requires_image,
                "is_real": has_real_implementation(t.name),
            }
            for t in tools
        ],
        "total": len(tools),
        "real_count": sum(1 for t in tools if has_real_implementation(t.name)),
    }


@app.get("/capabilities")
async def capabilities():
    """能力清单"""
    agent = get_agent()
    try:
        from src.tools.real_tools import has_real_implementation
        real_count = sum(1 for t in agent["registry"].list_tools() if has_real_implementation(t.name))
    except ImportError:
        real_count = 0

    return {
        "agent": "小V影像助手",
        "version": "2.0.0",
        "llm_provider": agent["planner"].llm.config.provider,
        "llm_model": agent["planner"].llm.config.model,
        "tools_total": len(agent["registry"].list_tools()),
        "tools_real": real_count,
        "tools_demo": len(agent["registry"].list_tools()) - real_count,
    }


# ---- 静态文件 ----
static_dir = PROJECT_ROOT / "server" / "static"
static_dir.mkdir(exist_ok=True)


# ---- 启动 ----
if __name__ == "__main__":
    import uvicorn
    print("=" * 55)
    print("  小V影像助手 API Server v2.0")
    print("  http://localhost:8000 - 聊天界面")
    print("  http://localhost:8000/docs - API 文档")
    print("=" * 55)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
