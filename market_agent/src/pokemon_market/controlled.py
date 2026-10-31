"""Credential-free model transport; the graph and domain tools remain real."""

import json
from pydantic import Field
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class ControlledModel(BaseChatModel):
    model_name: str = "market:controlled"
    bound_tools: list[str] = Field(default_factory=list)
    called_tools: list[str] = Field(default_factory=list)

    @property
    def _llm_type(self):
        return "market-controlled"

    def get_num_tokens(self, text):
        return max(1, len(text) // 4)

    def bind_tools(self, tools, **kwargs):
        self.bound_tools = [
            t.name
            if hasattr(t, "name")
            else t.get("name", t.get("function", {}).get("name"))
            for t in tools
        ]
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        request = json.loads(
            next(m.content for m in messages if isinstance(m, HumanMessage))
        )
        previous = next(
            (m for m in reversed(messages) if isinstance(m, ToolMessage)), None
        )
        operation = request["operation"]
        if previous is None:
            name = (
                "read_listing"
                if operation in ("assess_opportunity", "reassess_opportunity")
                else operation
            )
            args = (
                {"listing_id": request["correlation_id"]}
                if name == "read_listing"
                else {}
            )
        elif previous.name == "read_listing":
            name = operation
            args = {}
        elif previous.name == "assess_opportunity":
            name = "issue_mandate"
            args = {}
        elif previous.name == "assess_owned_unit":
            name = "summarize_inventory"
            args = {}
        else:
            artifact = json.loads(previous.content)
            name = "FinalReference"
            args = {"request_id": artifact["request_id"]}
        self.called_tools.append(name)
        message = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": name,
                    "args": args,
                    "id": f"call-{len(messages)}",
                    "type": "tool_call",
                }
            ],
        )
        return ChatResult(generations=[ChatGeneration(message=message)])
