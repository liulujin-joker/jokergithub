"""
LLM Client - Unified large model calling interface

Supports:
- DeepSeek (OpenAI-compatible protocol, Function Calling)
- vivo BlueHeart (for semifinals)
- Extensible to other providers
"""

import os
import json
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class LLMConfig:
    provider: str = "deepseek"
    model: str = "deepseek-chat"
    api_key: str = ""
    base_url: str = "https://api.deepseek.com/v1"
    temperature: float = 0.7
    max_tokens: int = 2048
    max_retries: int = 3
    timeout: int = 60


class LLMClient:
    """Unified LLM calling client"""

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or self._load_config_from_env()
        self._client = None

    def _load_config_from_env(self) -> LLMConfig:
        provider = os.getenv("LLM_PROVIDER", "deepseek")

        if provider == "deepseek":
            return LLMConfig(
                provider="deepseek",
                model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                api_key=os.getenv("DEEPSEEK_API_KEY", ""),
                base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            )
        elif provider == "vivo":
            return LLMConfig(
                provider="openai",
                model=os.getenv("VIVO_MODEL", "blue-heart-vision"),
                api_key=os.getenv("VIVO_API_KEY", ""),
                base_url=os.getenv("VIVO_BASE_URL", "https://api.vivo.com.cn/llm/v1"),
            )
        else:
            return LLMConfig(
                provider=provider,
                model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
                api_key=os.getenv("OPENAI_API_KEY", ""),
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            )

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=0,
            )
        return self._client

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> Any:
        client = self._get_client()
        kwargs = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            "stream": stream,
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                response = client.chat.completions.create(**kwargs)
                return response
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    wait = 0.5 * (2 ** attempt)
                    time.sleep(wait)
                else:
                    raise RuntimeError(
                        f"LLM call failed after {self.config.max_retries} retries: {last_error}"
                    ) from last_error

    def function_call(
        self,
        system_prompt: str,
        user_message: str,
        tools: List[Dict[str, Any]],
        tool_choice: str = "auto",
    ) -> List[Dict[str, Any]]:
        """
        Convenience method: send message and return tool call results.
        Returns list of {"id": ..., "name": ..., "arguments": {...}}
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        response = self.chat(
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            temperature=0.3,
        )

        choice = response.choices[0]
        if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
            result = []
            for tc in choice.message.tool_calls:
                args = json.loads(tc.function.arguments)
                result.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": args,
                })
            return result

        # No tool calls, return text response
        return [{"id": "text", "name": "_text", "arguments": {"text": choice.message.content}}]

    def simple_chat(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
    ) -> str:
        """Convenience: simple text chat"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        response = self.chat(messages=messages, temperature=temperature)
        return response.choices[0].message.content

    def check_connection(self) -> Dict[str, Any]:
        """Check LLM connectivity"""
        try:
            response = self.simple_chat(
                system_prompt="You are a helpful assistant.",
                user_message='Reply with just "OK"',
            )
            return {
                "ok": True,
                "provider": self.config.provider,
                "model": self.config.model,
                "response": response[:100],
            }
        except Exception as e:
            return {
                "ok": False,
                "provider": self.config.provider,
                "model": self.config.model,
                "error": str(e),
            }
