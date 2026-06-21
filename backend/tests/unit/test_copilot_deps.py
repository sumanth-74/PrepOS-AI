from __future__ import annotations

import ast
from pathlib import Path


def _isinstance_assert_issues(function_name: str) -> list[tuple[int, str]]:
    deps_path = Path(__file__).resolve().parents[2] / "src" / "prepos" / "api" / "deps.py"
    tree = ast.parse(deps_path.read_text())

    def collect_imports(nodes: list[ast.stmt]) -> set[str]:
        names: set[str] = set()
        for node in nodes:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names.add(alias.asname or alias.name.split(".")[-1])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    names.add(alias.asname or alias.name)
        return names

    module_imports = collect_imports(tree.body)
    issues: list[tuple[int, str]] = []

    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or node.name != function_name:
            continue
        func_imports = set(module_imports)
        for child in node.body:
            if isinstance(child, (ast.Import, ast.ImportFrom)):
                func_imports |= collect_imports([child])
        for child in ast.walk(node):
            if (
                isinstance(child, ast.Assert)
                and isinstance(child.test, ast.Call)
                and isinstance(child.test.func, ast.Name)
                and child.test.func.id == "isinstance"
                and len(child.test.args) >= 2
                and isinstance(child.test.args[1], ast.Name)
            ):
                name = child.test.args[1].id
                if name not in func_imports:
                    issues.append((child.lineno, name))
    return issues


def test_get_copilot_service_isinstance_symbols_are_imported() -> None:
    issues = _isinstance_assert_issues("get_copilot_service")
    assert issues == [], f"Missing imports for isinstance checks: {issues}"


def test_get_agent_orchestrator_isinstance_symbols_are_imported() -> None:
    issues = _isinstance_assert_issues("get_agent_orchestrator")
    assert issues == [], f"Missing imports for isinstance checks: {issues}"
