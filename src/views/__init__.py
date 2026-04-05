"""View system for kanban, table, and filter views."""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


class ViewType(Enum):
    KANBAN = "kanban"
    TABLE = "table"
    LIST = "list"
    CALENDAR = "calendar"
    GALLERY = "gallery"


class FilterOperator(Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    BETWEEN = "between"
    IN = "in"
    NOT_IN = "not_in"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"


@dataclass
class Filter:
    field: str
    operator: FilterOperator
    value: Any = None

    def evaluate(self, item: dict[str, Any]) -> bool:
        field_value = item.get(self.field)

        if self.operator == FilterOperator.EQUALS:
            return field_value == self.value
        elif self.operator == FilterOperator.NOT_EQUALS:
            return field_value != self.value
        elif self.operator == FilterOperator.CONTAINS:
            return self.value in str(field_value) if field_value else False
        elif self.operator == FilterOperator.STARTS_WITH:
            return str(field_value).startswith(self.value) if field_value else False
        elif self.operator == FilterOperator.ENDS_WITH:
            return str(field_value).endswith(self.value) if field_value else False
        elif self.operator == FilterOperator.GREATER_THAN:
            return field_value > self.value if field_value is not None else False
        elif self.operator == FilterOperator.LESS_THAN:
            return field_value < self.value if field_value is not None else False
        elif self.operator == FilterOperator.IN:
            return field_value in self.value if field_value is not None else False
        elif self.operator == FilterOperator.NOT_IN:
            return field_value not in self.value if field_value is not None else True
        elif self.operator == FilterOperator.IS_EMPTY:
            return field_value is None or field_value == "" or field_value == []
        elif self.operator == FilterOperator.IS_NOT_EMPTY:
            return field_value is not None and field_value != "" and field_value != []

        return True


@dataclass
class SortOption:
    field: str
    ascending: bool = True


@dataclass
class ViewGroup:
    id: str
    name: str
    filter: Filter | None = None
    items: list[dict[str, Any]] = field(default_factory=list)
    collapsed: bool = False
    color: str = "#808080"


@dataclass
class ViewColumn:
    id: str
    field: str
    label: str
    width: int = 150
    visible: bool = True
    sortable: bool = True
    editable: bool = True


@dataclass
class View:
    id: str
    name: str
    view_type: ViewType
    filters: list[Filter] = field(default_factory=list)
    sorts: list[SortOption] = field(default_factory=list)
    groups: list[ViewGroup] = field(default_factory=list)
    columns: list[ViewColumn] = field(default_factory=list)
    group_by: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class BaseViewRenderer(ABC):
    @abstractmethod
    def render(self, items: list[dict[str, Any]], view: View) -> dict[str, Any]:
        pass


class KanbanRenderer(BaseViewRenderer):
    def render(self, items: list[dict[str, Any]], view: View) -> dict[str, Any]:
        groups: dict[str, list[dict[str, Any]]] = {}

        if view.group_by:
            for item in items:
                group_key = str(item.get(view.group_by, "Unassigned"))
                if group_key not in groups:
                    groups[group_key] = []
                groups[group_key].append(item)
        else:
            groups["All"] = items

        result_groups = []
        for group_name, group_items in groups.items():
            filtered_items = self._apply_filters(group_items, view.filters)
            sorted_items = self._apply_sorts(filtered_items, view.sorts)

            result_groups.append(
                ViewGroup(
                    id=group_name.lower().replace(" ", "-"),
                    name=group_name,
                    items=sorted_items,
                )
            )

        return {"type": "kanban", "groups": result_groups}

    def _apply_filters(self, items: list[dict[str, Any]], filters: list[Filter]) -> list[dict[str, Any]]:
        result = items
        for f in filters:
            result = [item for item in result if f.evaluate(item)]
        return result

    def _apply_sorts(self, items: list[dict[str, Any]], sorts: list[SortOption]) -> list[dict[str, Any]]:
        if not sorts:
            return items

        def sort_key(item: dict[str, Any]) -> tuple:
            keys = []
            for s in sorts:
                val = item.get(s.field, "")
                if val is None:
                    val = ""
                keys.append(val)
            return tuple(keys)

        return sorted(items, key=sort_key, reverse=not sorts[0].ascending if sorts else False)


class TableRenderer(BaseViewRenderer):
    def render(self, items: list[dict[str, Any]], view: View) -> dict[str, Any]:
        filtered_items = items
        for f in view.filters:
            filtered_items = [item for item in filtered_items if f.evaluate(item)]

        if view.sorts:
            def sort_key(item: dict[str, Any]) -> tuple:
                return tuple(item.get(s.field, "") or "" for s in view.sorts)

            filtered_items = sorted(
                filtered_items,
                key=sort_key,
                reverse=not view.sorts[0].ascending if view.sorts else False,
            )

        visible_columns = [c for c in view.columns if c.visible]
        if not visible_columns:
            all_fields = set()
            for item in filtered_items:
                all_fields.update(item.keys())
            visible_columns = [ViewColumn(id=f, field=f, label=f.title()) for f in sorted(all_fields)]

        rows = []
        for item in filtered_items:
            row = {}
            for col in visible_columns:
                row[col.id] = item.get(col.field)
            rows.append(row)

        return {
            "type": "table",
            "columns": [{"id": c.id, "label": c.label, "width": c.width} for c in visible_columns],
            "rows": rows,
            "total": len(rows),
        }


class ViewManager:
    def __init__(self, storage_path: str = "data/views"):
        self._storage_path = Path(storage_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._views: dict[str, View] = {}
        self._renderers: dict[ViewType, BaseViewRenderer] = {
            ViewType.KANBAN: KanbanRenderer(),
            ViewType.TABLE: TableRenderer(),
        }
        self._load_views()

    def _load_views(self) -> None:
        for view_file in self._storage_path.glob("*.json"):
            try:
                with open(view_file, encoding="utf-8") as f:
                    data = json.load(f)
                view = self._dict_to_view(data)
                self._views[view.id] = view
            except Exception as e:
                logger.warning("Failed to load view %s: %s", view_file, e)

    def _dict_to_view(self, data: dict[str, Any]) -> View:
        filters = [
            Filter(field=f["field"], operator=FilterOperator(f["operator"]), value=f.get("value"))
            for f in data.get("filters", [])
        ]
        sorts = [SortOption(field=s["field"], ascending=s.get("ascending", True)) for s in data.get("sorts", [])]
        columns = [
            ViewColumn(
                id=c["id"],
                field=c["field"],
                label=c["label"],
                width=c.get("width", 150),
                visible=c.get("visible", True),
            )
            for c in data.get("columns", [])
        ]

        return View(
            id=data["id"],
            name=data["name"],
            view_type=ViewType(data["view_type"]),
            filters=filters,
            sorts=sorts,
            columns=columns,
            group_by=data.get("group_by"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
        )

    def create_view(
        self,
        name: str,
        view_type: ViewType,
        filters: list[Filter] | None = None,
        sorts: list[SortOption] | None = None,
        columns: list[ViewColumn] | None = None,
        group_by: str | None = None,
    ) -> View:
        import uuid

        view = View(
            id=str(uuid.uuid4()),
            name=name,
            view_type=view_type,
            filters=filters or [],
            sorts=sorts or [],
            columns=columns or [],
            group_by=group_by,
        )
        self._views[view.id] = view
        self._save_view(view)
        return view

    def update_view(self, view_id: str, **kwargs: Any) -> View | None:
        view = self._views.get(view_id)
        if not view:
            return None

        for key, value in kwargs.items():
            if hasattr(view, key):
                setattr(view, key, value)
        view.updated_at = datetime.now()

        self._save_view(view)
        return view

    def delete_view(self, view_id: str) -> bool:
        if view_id not in self._views:
            return False

        view_file = self._storage_path / f"{view_id}.json"
        if view_file.exists():
            view_file.unlink()

        del self._views[view_id]
        return True

    def get_view(self, view_id: str) -> View | None:
        return self._views.get(view_id)

    def list_views(self, view_type: ViewType | None = None) -> list[View]:
        views = list(self._views.values())
        if view_type:
            views = [v for v in views if v.view_type == view_type]
        return views

    def render_view(self, view_id: str, items: list[dict[str, Any]]) -> dict[str, Any]:
        view = self._views.get(view_id)
        if not view:
            return {"error": "View not found"}

        renderer = self._renderers.get(view.view_type)
        if not renderer:
            return {"error": f"No renderer for view type: {view.view_type}"}

        return renderer.render(items, view)

    def _save_view(self, view: View) -> None:
        view_file = self._storage_path / f"{view.id}.json"
        data = {
            "id": view.id,
            "name": view.name,
            "view_type": view.view_type.value,
            "filters": [{"field": f.field, "operator": f.operator.value, "value": f.value} for f in view.filters],
            "sorts": [{"field": s.field, "ascending": s.ascending} for s in view.sorts],
            "columns": [
                {"id": c.id, "field": c.field, "label": c.label, "width": c.width, "visible": c.visible}
                for c in view.columns
            ],
            "group_by": view.group_by,
            "created_at": view.created_at.isoformat(),
            "updated_at": view.updated_at.isoformat(),
        }
        with open(view_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


_manager: ViewManager | None = None


def get_view_manager() -> ViewManager:
    global _manager
    if _manager is None:
        _manager = ViewManager()
    return _manager
