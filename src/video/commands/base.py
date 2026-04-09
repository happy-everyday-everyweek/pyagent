from abc import ABC, abstractmethod


class Command(ABC):
    @abstractmethod
    def execute(self) -> None:
        pass

    def undo(self) -> None:
        raise NotImplementedError("Undo not implemented for this command")

    def redo(self) -> None:
        self.execute()

    @property
    def description(self) -> str | None:
        return None
