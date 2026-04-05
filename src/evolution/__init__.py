"""Self-evolution mechanism for continuous improvement."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class LearningRecord:
    id: str
    timestamp: datetime
    event_type: str
    context: dict[str, Any]
    outcome: str
    feedback: str | None = None
    improvement_suggestions: list[str] = field(default_factory=list)
    applied: bool = False


@dataclass
class PerformanceMetric:
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class EvolutionState:
    generation: int = 1
    total_learning_events: int = 0
    successful_adaptations: int = 0
    failed_adaptations: int = 0
    last_evolution: datetime | None = None
    active_improvements: list[str] = field(default_factory=list)


class SelfEvolution:
    """Self-evolution system for continuous improvement."""

    def __init__(self, storage_path: str = "data/evolution"):
        self._storage_path = Path(storage_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._learning_records: list[LearningRecord] = []
        self._metrics: dict[str, list[PerformanceMetric]] = {}
        self._state = EvolutionState()
        self._improvement_handlers: dict[str, Callable] = {}
        self._feedback_handlers: list[Callable] = []
        self._load_state()

    def _load_state(self) -> None:
        state_file = self._storage_path / "state.json"
        if state_file.exists():
            with open(state_file, encoding="utf-8") as f:
                data = json.load(f)
            self._state = EvolutionState(
                generation=data.get("generation", 1),
                total_learning_events=data.get("total_learning_events", 0),
                successful_adaptations=data.get("successful_adaptations", 0),
                failed_adaptations=data.get("failed_adaptations", 0),
                last_evolution=datetime.fromisoformat(data["last_evolution"]) if data.get("last_evolution") else None,
                active_improvements=data.get("active_improvements", []),
            )

        records_file = self._storage_path / "records.json"
        if records_file.exists():
            with open(records_file, encoding="utf-8") as f:
                data = json.load(f)
            self._learning_records = [
                LearningRecord(
                    id=r["id"],
                    timestamp=datetime.fromisoformat(r["timestamp"]),
                    event_type=r["event_type"],
                    context=r.get("context", {}),
                    outcome=r["outcome"],
                    feedback=r.get("feedback"),
                    improvement_suggestions=r.get("improvement_suggestions", []),
                    applied=r.get("applied", False),
                )
                for r in data.get("records", [])
            ]

    def _save_state(self) -> None:
        state_file = self._storage_path / "state.json"
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "generation": self._state.generation,
                    "total_learning_events": self._state.total_learning_events,
                    "successful_adaptations": self._state.successful_adaptations,
                    "failed_adaptations": self._state.failed_adaptations,
                    "last_evolution": self._state.last_evolution.isoformat() if self._state.last_evolution else None,
                    "active_improvements": self._state.active_improvements,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        records_file = self._storage_path / "records.json"
        with open(records_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "records": [
                        {
                            "id": r.id,
                            "timestamp": r.timestamp.isoformat(),
                            "event_type": r.event_type,
                            "context": r.context,
                            "outcome": r.outcome,
                            "feedback": r.feedback,
                            "improvement_suggestions": r.improvement_suggestions,
                            "applied": r.applied,
                        }
                        for r in self._learning_records[-100:]
                    ]
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

    def record_event(
        self,
        event_type: str,
        context: dict[str, Any],
        outcome: str,
        feedback: str | None = None,
    ) -> LearningRecord:
        import uuid

        record = LearningRecord(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            event_type=event_type,
            context=context,
            outcome=outcome,
            feedback=feedback,
        )

        suggestions = self._generate_improvements(record)
        record.improvement_suggestions = suggestions

        self._learning_records.append(record)
        self._state.total_learning_events += 1
        self._save_state()

        logger.info("Recorded learning event: %s - %s", event_type, outcome)
        return record

    def _generate_improvements(self, record: LearningRecord) -> list[str]:
        suggestions = []

        if record.outcome == "failure":
            suggestions.append(f"Analyze failure pattern for {record.event_type}")
            suggestions.append("Consider adding error handling")

        if record.outcome == "success" and record.feedback:
            if "slow" in record.feedback.lower():
                suggestions.append("Optimize performance for this operation")
            if "unclear" in record.feedback.lower():
                suggestions.append("Improve clarity of responses")

        return suggestions

    def register_improvement_handler(self, improvement_type: str, handler: Callable) -> None:
        self._improvement_handlers[improvement_type] = handler

    def register_feedback_handler(self, handler: Callable) -> None:
        self._feedback_handlers.append(handler)

    async def evolve(self) -> dict[str, Any]:
        results = {"improvements_applied": 0, "improvements_failed": 0, "details": []}

        pending_records = [r for r in self._learning_records if not r.applied and r.improvement_suggestions]

        for record in pending_records[:10]:
            for suggestion in record.improvement_suggestions:
                try:
                    handler = self._improvement_handlers.get(suggestion)
                    if handler:
                        await handler(record.context)
                        record.applied = True
                        self._state.successful_adaptations += 1
                        results["improvements_applied"] += 1
                        results["details"].append({"record_id": record.id, "suggestion": suggestion, "status": "applied"})
                    else:
                        results["details"].append({"record_id": record.id, "suggestion": suggestion, "status": "no_handler"})

                except Exception as e:
                    self._state.failed_adaptations += 1
                    results["improvements_failed"] += 1
                    results["details"].append({"record_id": record.id, "suggestion": suggestion, "status": "failed", "error": str(e)})

        self._state.last_evolution = datetime.now()
        if results["improvements_applied"] > 0:
            self._state.generation += 1

        self._save_state()
        return results

    def record_metric(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        metric = PerformanceMetric(name=name, value=value, tags=tags or {})
        if name not in self._metrics:
            self._metrics[name] = []
        self._metrics[name].append(metric)

        self._check_metric_thresholds(name, value)

    def _check_metric_thresholds(self, name: str, value: float) -> None:
        thresholds = {
            "response_time": {"max": 5.0, "suggestion": "Response time too high, consider caching"},
            "error_rate": {"max": 0.1, "suggestion": "Error rate too high, review error handling"},
            "user_satisfaction": {"min": 0.8, "suggestion": "User satisfaction low, review feedback"},
        }

        threshold = thresholds.get(name)
        if not threshold:
            return

        if "max" in threshold and value > threshold["max"]:
            self.record_event("metric_threshold_exceeded", {"metric": name, "value": value}, "warning", threshold["suggestion"])
        elif "min" in threshold and value < threshold["min"]:
            self.record_event("metric_threshold_exceeded", {"metric": name, "value": value}, "warning", threshold["suggestion"])

    def get_metrics(self, name: str | None = None, limit: int = 100) -> dict[str, list[dict[str, Any]]]:
        if name:
            metrics = {name: self._metrics.get(name, [])[-limit:]}
        else:
            metrics = {k: v[-limit:] for k, v in self._metrics.items()}

        return {
            k: [{"value": m.value, "timestamp": m.timestamp.isoformat(), "tags": m.tags} for m in v]
            for k, v in metrics.items()
        }

    def get_state(self) -> EvolutionState:
        return self._state

    def get_learning_summary(self) -> dict[str, Any]:
        event_types: dict[str, int] = {}
        outcomes: dict[str, int] = {}

        for record in self._learning_records:
            event_types[record.event_type] = event_types.get(record.event_type, 0) + 1
            outcomes[record.outcome] = outcomes.get(record.outcome, 0) + 1

        return {
            "total_events": len(self._learning_records),
            "event_types": event_types,
            "outcomes": outcomes,
            "pending_improvements": len([r for r in self._learning_records if not r.applied]),
            "generation": self._state.generation,
            "success_rate": self._state.successful_adaptations / max(1, self._state.successful_adaptations + self._state.failed_adaptations),
        }


_evolution: SelfEvolution | None = None


def get_evolution() -> SelfEvolution:
    global _evolution
    if _evolution is None:
        _evolution = SelfEvolution()
    return _evolution
