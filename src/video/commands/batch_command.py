from typing import List
from .base import Command


class BatchCommand(Command):
    def __init__(self, commands: List[Command], description: str = None):
        self._commands = commands
        self._description = description

    def execute(self) -> None:
        for command in self._commands:
            command.execute()

    def undo(self) -> None:
        for command in reversed(self._commands):
            command.undo()

    def redo(self) -> None:
        for command in self._commands:
            command.redo()

    @property
    def description(self) -> str:
        return self._description or f"Batch command ({len(self._commands)} commands)"

    @property
    def commands(self) -> List[Command]:
        return self._commands.copy()

    def add_command(self, command: Command) -> None:
        self._commands.append(command)
