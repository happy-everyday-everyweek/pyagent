from abc import ABC, abstractmethod
from typing import Optional


class Command(ABC):
    @abstractmethod
    def execute(self) -> None:
        pass

    def undo(self) -> None:
        raise NotImplementedError("Undo not implemented for this command")

    def redo(self) -> None:
        self.execute()

    @property
    def description(self) -> Optional[str]:
        return None
