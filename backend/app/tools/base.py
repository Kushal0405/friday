from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class ToolResult(BaseModel):
    success: bool
    message: str
    data: dict[str, Any] | None = None


class Tool(ABC):
    name: str
    description: str
    parameters: type[BaseModel]
    requires_confirmation: bool = False

    @abstractmethod
    async def execute(self, params: BaseModel) -> ToolResult:
        """Run the tool with validated parameters and return a result."""

    def schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters.model_json_schema(),
            },
        }
