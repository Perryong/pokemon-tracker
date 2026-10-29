"""Scripted model transport for offline demos; no model reasoning is simulated as live.

The transport emits tool requests. Only the actual Deep Agents graph executes them.
"""
from typing import Any
from pydantic import Field
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class ControlledModel(BaseChatModel):
    responses: list[AIMessage]
    cursor: int = 0
    seen_tool_names: set[str] = Field(default_factory=set)

    @property
    def _llm_type(self) -> str:
        return 'controlled-offline-sales-fixture'

    def bind_tools(self, tools, *, tool_choice=None, **kwargs):
        self.seen_tool_names.update(t.name if hasattr(t, 'name') else t['name'] for t in tools)
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs: Any):
        if self.cursor >= len(self.responses):
            raise RuntimeError('Controlled model fixture exhausted; no implicit success')
        response = self.responses[self.cursor]
        self.cursor += 1
        return ChatResult(generations=[ChatGeneration(message=response)])
