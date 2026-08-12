from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class CommandResult:
    success: bool
    output: Any
    metadata: Optional[dict[str, Any]] = None

class IBotCommand(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def execute(self, payload: Any, **kwargs) -> CommandResult:
        pass