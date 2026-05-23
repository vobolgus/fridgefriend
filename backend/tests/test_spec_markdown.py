from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from types import ModuleType


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = REPO_ROOT / "SPEC.md"
EXCEL_SPEC_PATH = REPO_ROOT / "FridgeFriend_SPEC_filled.xlsx"
EXPORTER_PATH = REPO_ROOT / "scripts" / "export_spec_markdown.py"


def _load_exporter() -> ModuleType:
    spec = importlib.util.spec_from_file_location("export_spec_markdown", EXPORTER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _ids_for(pattern: str, rows: list[list[str]]) -> set[str]:
    regex = re.compile(pattern)
    return {match for row in rows for cell in row for match in regex.findall(cell)}


def test_markdown_spec_exists_and_points_to_excel_source() -> None:
    markdown = SPEC_PATH.read_text(encoding="utf-8")

    assert "# FridgeFriend Specification" in markdown
    assert "Source workbook: `FridgeFriend_SPEC_filled.xlsx`." in markdown
    assert "python scripts/export_spec_markdown.py" in markdown
    assert "<!-- api-contract:start -->" in markdown
    assert "<!-- api-contract:end -->" in markdown


def test_markdown_spec_carries_excel_requirement_ids() -> None:
    exporter = _load_exporter()
    rows = exporter.read_xlsx_rows(EXCEL_SPEC_PATH)
    markdown = SPEC_PATH.read_text(encoding="utf-8")

    expected_ids = set()
    for pattern in (r"\bUS-\d+\b", r"\bUC-\d+\.\d+\b", r"\bFR-\d+\b", r"\bNFR-\d+\b", r"\bT-\d+\b", r"\bST-\d+\b"):
        expected_ids.update(_ids_for(pattern, rows))

    missing_ids = sorted(identifier for identifier in expected_ids if identifier not in markdown)
    assert not missing_ids, f"Markdown spec is missing Excel IDs: {missing_ids}"


def test_excel_exporter_renders_editable_markdown() -> None:
    exporter = _load_exporter()
    rendered = exporter.render_markdown(exporter.read_xlsx_rows(EXCEL_SPEC_PATH))

    assert rendered.startswith("# FridgeFriend Specification")
    assert "## 1. Feature Context" in rendered
    assert "## 3. Architecture / Solution" in rendered
    assert "## Current API Contract" in rendered
    assert "FR-12" in rendered
    assert "ST-12" in rendered
