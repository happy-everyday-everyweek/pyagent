"""Tests for tools.py — validate ORG_NODE_TOOLS constant and handler correspondence."""

from __future__ import annotations

import pytest

from openakita.orgs.tools import ORG_NODE_TOOLS
from openakita.orgs.tool_handler import OrgToolHandler


class TestOrgNodeToolsConstant:
    def test_is_list(self):
        assert isinstance(ORG_NODE_TOOLS, list)
        assert len(ORG_NODE_TOOLS) > 0

    def test_each_tool_has_required_fields(self):
        for tool in ORG_NODE_TOOLS:
            assert "name" in tool, f"Tool missing 'name': {tool}"
            assert "description" in tool, f"Tool {tool.get('name')} missing 'description'"
            assert "input_schema" in tool, f"Tool {tool['name']} missing 'input_schema'"

    def test_tool_names_are_unique(self):
        names = [t["name"] for t in ORG_NODE_TOOLS]
        assert len(names) == len(set(names)), f"Duplicate tool names: {[n for n in names if names.count(n) > 1]}"

    def test_all_tool_names_start_with_org(self):
        for tool in ORG_NODE_TOOLS:
            assert tool["name"].startswith("org_"), f"Tool name should start with 'org_': {tool['name']}"

    def test_parameters_are_valid_json_schema(self):
        for tool in ORG_NODE_TOOLS:
            params = tool["input_schema"]
            assert params.get("type") == "object", f"{tool['name']}: params type should be 'object'"
            assert "properties" in params, f"{tool['name']}: missing 'properties'"

    def test_required_fields_exist_in_properties(self):
        for tool in ORG_NODE_TOOLS:
            params = tool["input_schema"]
            props = params.get("properties", {})
            required = params.get("required", [])
            for req_field in required:
                assert req_field in props, (
                    f"{tool['name']}: required field '{req_field}' not in properties"
                )


class TestToolHandlerCorrespondence:
    """Verify every tool defined in ORG_NODE_TOOLS has a handler method."""

    def test_all_tools_have_handlers(self):
        handler_cls = OrgToolHandler
        tool_names = {t["name"] for t in ORG_NODE_TOOLS}

        for name in tool_names:
            method_name = f"_handle_{name}"
            assert hasattr(handler_cls, method_name), (
                f"Tool '{name}' has no handler method '{method_name}' in OrgToolHandler"
            )

    def test_handler_methods_are_callable(self):
        handler_cls = OrgToolHandler
        for tool in ORG_NODE_TOOLS:
            method_name = f"_handle_{tool['name']}"
            method = getattr(handler_cls, method_name, None)
            assert callable(method), f"Handler '{method_name}' is not callable"
