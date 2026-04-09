"""
PyAgent 垂类智能体模块 - 智能体注册中心
"""

from dataclasses import dataclass
from typing import Any

from .base import BaseVerticalAgent


@dataclass
class AgentInfo:
    name: str
    description: str
    capabilities: list[str]
    status: str


class AgentRegistry:
    """智能体注册中心"""

    _instance: "AgentRegistry | None" = None

    def __new__(cls) -> "AgentRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._agents: dict[str, BaseVerticalAgent] = {}
            cls._instance._capability_index: dict[str, list[str]] = {}
        return cls._instance

    def register_agent(self, agent: BaseVerticalAgent) -> bool:
        if agent.name in self._agents:
            return False

        self._agents[agent.name] = agent

        for capability in agent.get_capabilities():
            cap_name = capability.name
            if cap_name not in self._capability_index:
                self._capability_index[cap_name] = []
            self._capability_index[cap_name].append(agent.name)

        return True

    def unregister_agent(self, name: str) -> bool:
        if name not in self._agents:
            return False

        agent = self._agents[name]

        for capability in agent.get_capabilities():
            cap_name = capability.name
            if cap_name in self._capability_index:
                if name in self._capability_index[cap_name]:
                    self._capability_index[cap_name].remove(name)
                if not self._capability_index[cap_name]:
                    del self._capability_index[cap_name]

        del self._agents[name]
        return True

    def get_agent(self, name: str) -> BaseVerticalAgent | None:
        return self._agents.get(name)

    def list_agents(self) -> list[AgentInfo]:
        return [
            AgentInfo(
                name=agent.name,
                description=agent.description,
                capabilities=[c.name for c in agent.get_capabilities()],
                status=agent.status.value,
            )
            for agent in self._agents.values()
        ]

    def get_agents_by_capability(self, capability: str) -> list[BaseVerticalAgent]:
        agent_names = self._capability_index.get(capability, [])
        return [self._agents[name] for name in agent_names if name in self._agents]

    def get_capabilities(self) -> list[str]:
        return list(self._capability_index.keys())

    def get_agent_count(self) -> int:
        return len(self._agents)

    def initialize_all(self) -> dict[str, bool]:
        results: dict[str, bool] = {}
        for name, agent in self._agents.items():
            results[name] = agent.initialize()
        return results

    def shutdown_all(self) -> None:
        for agent in self._agents.values():
            agent.shutdown()

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_count": len(self._agents),
            "agents": [agent.to_dict() for agent in self._agents.values()],
            "capabilities": list(self._capability_index.keys()),
        }


agent_registry = AgentRegistry()
