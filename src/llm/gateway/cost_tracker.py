"""Cost tracking for LLM usage."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class UsageRecord:
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    timestamp: datetime = field(default_factory=datetime.now)
    request_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TenantUsage:
    tenant_id: str
    total_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    records: list[UsageRecord] = field(default_factory=list)


MODEL_PRICING: dict[str, dict[str, float]] = {
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    "deepseek-chat": {"input": 0.0001, "output": 0.0002},
    "deepseek-coder": {"input": 0.0001, "output": 0.0002},
    "glm-4": {"input": 0.0001, "output": 0.0001},
    "glm-4-flash": {"input": 0.00001, "output": 0.00001},
}


class CostTracker:
    def __init__(self, storage_path: str = "data/costs"):
        self._storage_path = Path(storage_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._tenants: dict[str, TenantUsage] = {}
        self._default_tenant = "default"

    def record_usage(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        tenant_id: str | None = None,
        request_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> UsageRecord:
        cost = self._calculate_cost(model, input_tokens, output_tokens)

        record = UsageRecord(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            request_id=request_id,
            metadata=metadata or {},
        )

        tid = tenant_id or self._default_tenant
        if tid not in self._tenants:
            self._tenants[tid] = TenantUsage(tenant_id=tid)

        tenant = self._tenants[tid]
        tenant.records.append(record)
        tenant.total_requests += 1
        tenant.total_input_tokens += input_tokens
        tenant.total_output_tokens += output_tokens
        tenant.total_cost += cost

        logger.debug(
            "Recorded usage: %s/%s - %d in, %d out, $%.6f",
            provider,
            model,
            input_tokens,
            output_tokens,
            cost,
        )
        return record

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        model_key = model.lower().replace(".", "-")
        pricing = MODEL_PRICING.get(model_key, {"input": 0.0, "output": 0.0})

        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return input_cost + output_cost

    def get_tenant_usage(self, tenant_id: str | None = None) -> TenantUsage:
        tid = tenant_id or self._default_tenant
        return self._tenants.get(tid, TenantUsage(tenant_id=tid))

    def get_usage_by_period(
        self,
        tenant_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        tenant = self.get_tenant_usage(tenant_id)

        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()

        filtered_records = [
            r for r in tenant.records if start_date <= r.timestamp <= end_date
        ]

        return {
            "tenant_id": tenant.tenant_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "total_requests": len(filtered_records),
            "total_input_tokens": sum(r.input_tokens for r in filtered_records),
            "total_output_tokens": sum(r.output_tokens for r in filtered_records),
            "total_cost": sum(r.cost for r in filtered_records),
        }

    def get_usage_by_model(self, tenant_id: str | None = None) -> dict[str, dict[str, Any]]:
        tenant = self.get_tenant_usage(tenant_id)

        by_model: dict[str, dict[str, Any]] = {}
        for record in tenant.records:
            if record.model not in by_model:
                by_model[record.model] = {
                    "count": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost": 0.0,
                }
            by_model[record.model]["count"] += 1
            by_model[record.model]["input_tokens"] += record.input_tokens
            by_model[record.model]["output_tokens"] += record.output_tokens
            by_model[record.model]["cost"] += record.cost

        return by_model

    def generate_report(self, tenant_id: str | None = None) -> dict[str, Any]:
        tenant = self.get_tenant_usage(tenant_id)

        return {
            "tenant_id": tenant.tenant_id,
            "summary": {
                "total_requests": tenant.total_requests,
                "total_input_tokens": tenant.total_input_tokens,
                "total_output_tokens": tenant.total_output_tokens,
                "total_cost": tenant.total_cost,
            },
            "by_model": self.get_usage_by_model(tenant_id),
            "by_provider": self._get_usage_by_provider(tenant),
            "daily_usage": self._get_daily_usage(tenant),
        }

    def _get_usage_by_provider(self, tenant: TenantUsage) -> dict[str, dict[str, Any]]:
        by_provider: dict[str, dict[str, Any]] = {}
        for record in tenant.records:
            if record.provider not in by_provider:
                by_provider[record.provider] = {"count": 0, "cost": 0.0}
            by_provider[record.provider]["count"] += 1
            by_provider[record.provider]["cost"] += record.cost
        return by_provider

    def _get_daily_usage(self, tenant: TenantUsage) -> dict[str, dict[str, Any]]:
        daily: dict[str, dict[str, Any]] = {}
        for record in tenant.records:
            date_key = record.timestamp.strftime("%Y-%m-%d")
            if date_key not in daily:
                daily[date_key] = {"requests": 0, "cost": 0.0}
            daily[date_key]["requests"] += 1
            daily[date_key]["cost"] += record.cost
        return daily

    def save(self, tenant_id: str | None = None) -> None:
        tid = tenant_id or self._default_tenant
        tenant = self._tenants.get(tid)
        if not tenant:
            return

        filepath = self._storage_path / f"{tid}.json"
        data = {
            "tenant_id": tenant.tenant_id,
            "total_requests": tenant.total_requests,
            "total_input_tokens": tenant.total_input_tokens,
            "total_output_tokens": tenant.total_output_tokens,
            "total_cost": tenant.total_cost,
            "records": [
                {
                    "provider": r.provider,
                    "model": r.model,
                    "input_tokens": r.input_tokens,
                    "output_tokens": r.output_tokens,
                    "cost": r.cost,
                    "timestamp": r.timestamp.isoformat(),
                    "request_id": r.request_id,
                }
                for r in tenant.records
            ],
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, tenant_id: str | None = None) -> None:
        tid = tenant_id or self._default_tenant
        filepath = self._storage_path / f"{tid}.json"
        if not filepath.exists():
            return

        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        tenant = TenantUsage(
            tenant_id=data["tenant_id"],
            total_requests=data["total_requests"],
            total_input_tokens=data["total_input_tokens"],
            total_output_tokens=data["total_output_tokens"],
            total_cost=data["total_cost"],
        )

        for r in data.get("records", []):
            record = UsageRecord(
                provider=r["provider"],
                model=r["model"],
                input_tokens=r["input_tokens"],
                output_tokens=r["output_tokens"],
                cost=r["cost"],
                timestamp=datetime.fromisoformat(r["timestamp"]),
                request_id=r.get("request_id"),
            )
            tenant.records.append(record)

        self._tenants[tid] = tenant


_tracker: CostTracker | None = None


def get_cost_tracker() -> CostTracker:
    global _tracker
    if _tracker is None:
        _tracker = CostTracker()
    return _tracker
