from __future__ import annotations

import argparse
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = REPO_ROOT / "FridgeFriend_SPEC_filled.xlsx"
DEFAULT_OUTPUT = REPO_ROOT / "SPEC.md"

SPREADSHEET_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

API_ENDPOINTS: tuple[tuple[str, str, str], ...] = (
    ("POST", "/v1/items", "Create an inventory item"),
    ("GET", "/v1/items", "List inventory items"),
    ("GET", "/v1/items/{item_id}", "Read an inventory item"),
    ("PATCH", "/v1/items/{item_id}", "Partially update an inventory item"),
    ("PUT", "/v1/items/{item_id}", "Replace an inventory item"),
    ("DELETE", "/v1/items/{item_id}", "Delete an inventory item"),
    ("POST", "/v1/items/{item_id}/status", "Mark item used, discarded, frozen, or active"),
    ("POST", "/v1/items/{item_id}/undo", "Undo a recent inventory change"),
    ("POST", "/v1/scan/barcode", "Resolve barcode input into an editable product draft"),
    ("POST", "/v1/scan/photo", "Parse a fridge photo into editable draft items"),
    ("POST", "/v1/scan/photo/upload", "Create a signed upload target for photo scanning"),
    ("POST", "/v1/recommendations", "Return ranked recipe recommendations"),
    ("GET", "/v1/recipes/{recipe_id}", "Read recipe details"),
    ("POST", "/v1/plans", "Generate a meal plan and reserve ingredients"),
    ("GET", "/v1/plans/latest", "Read the latest saved meal plan"),
    ("GET", "/v1/shopping-list", "Compute shopping gaps from the active plan"),
    ("DELETE", "/v1/plans/{plan_id}", "Delete a saved meal plan"),
    ("GET", "/v1/households", "List households for the authenticated user"),
    ("POST", "/v1/households", "Create a household"),
    ("GET", "/v1/households/{household_id}", "Read household details"),
    ("PATCH", "/v1/households/{household_id}", "Update household details"),
    ("POST", "/v1/households/join", "Join a household by invite code"),
    ("POST", "/v1/households/{household_id}/leave", "Leave a household"),
    ("DELETE", "/v1/households/{household_id}/members/{user_id}", "Remove a household member"),
    ("GET", "/v1/households/{household_id}/events", "Stream household events"),
    ("GET", "/v1/households/{household_id}/activity", "Read household activity log"),
    ("GET", "/v1/notifications", "Read notification preferences"),
    ("PATCH", "/v1/notifications", "Update notification preferences"),
    ("POST", "/v1/notifications/devices", "Register a push notification device token"),
    ("DELETE", "/v1/notifications/devices/{token_id}", "Unregister a push notification device token"),
    ("POST", "/v1/analytics/events", "Collect product analytics events"),
    ("GET", "/health", "Service health check"),
)


def _shared_strings(workbook: zipfile.ZipFile) -> list[str]:
    root = ElementTree.fromstring(workbook.read("xl/sharedStrings.xml"))
    strings: list[str] = []
    for item in root.findall("m:si", SPREADSHEET_NS):
        text = "".join(node.text or "" for node in item.iter(f"{{{SPREADSHEET_NS['m']}}}t"))
        strings.append(text)
    return strings


def _column_index(cell_ref: str) -> int:
    match = re.match(r"([A-Z]+)", cell_ref)
    if match is None:
        raise ValueError(f"Invalid cell reference: {cell_ref}")

    index = 0
    for char in match.group(1):
        index = index * 26 + ord(char) - ord("A") + 1
    return index


def _cell_text(cell: ElementTree.Element, shared_strings: list[str]) -> str:
    value = cell.find("m:v", SPREADSHEET_NS)
    if value is None or value.text is None:
        return ""
    if cell.attrib.get("t") == "s":
        return shared_strings[int(value.text)]
    return value.text


def _trim_trailing_empty(values: list[str]) -> list[str]:
    while values and not values[-1].strip():
        values.pop()
    return values


def read_xlsx_rows(path: Path) -> list[list[str]]:
    with zipfile.ZipFile(path) as workbook:
        shared_strings = _shared_strings(workbook)
        worksheet = ElementTree.fromstring(workbook.read("xl/worksheets/sheet1.xml"))

    rows: list[list[str]] = []
    for row in worksheet.findall(".//m:sheetData/m:row", SPREADSHEET_NS):
        values_by_column: dict[int, str] = {}
        max_column = 0
        for cell in row.findall("m:c", SPREADSHEET_NS):
            column = _column_index(cell.attrib["r"])
            values_by_column[column] = _cell_text(cell, shared_strings).strip()
            max_column = max(max_column, column)

        values = _trim_trailing_empty([values_by_column.get(column, "") for column in range(1, max_column + 1)])
        if values and any(value for value in values):
            rows.append(values)
    return rows


def _heading_level(text: str) -> int:
    if re.match(r"^\d+\.\d+\s", text):
        return 3
    if re.match(r"^\d+\.\s", text):
        return 2
    if text.startswith(("User Story", "Task ")):
        return 3
    if text in {"Functional Requirements", "Non-Functional Requirements", "Subtasks"}:
        return 4
    if text.startswith("Use Case"):
        return 4
    if text.startswith("Mapping:"):
        return 3
    return 3


def _is_heading(row: list[str]) -> bool:
    return len(row) == 1 and bool(row[0])


def _is_table_header(row: list[str]) -> bool:
    return tuple(row[:2]) in {
        ("Section", "Fill In"),
        ("Req ID", "Requirement"),
        ("Use Case", "Task ID"),
        ("Subtask ID", "Description"),
    }


def _escape_table_cell(value: str) -> str:
    return value.replace("\n", "<br>").replace("|", r"\|")


def _render_table(header: list[str], body: list[list[str]]) -> list[str]:
    width = max(len(header), *(len(row) for row in body))
    padded_header = header + [""] * (width - len(header))
    lines = [
        "| " + " | ".join(_escape_table_cell(value) for value in padded_header) + " |",
        "| " + " | ".join("---" for _ in range(width)) + " |",
    ]
    for row in body:
        padded_row = row + [""] * (width - len(row))
        lines.append("| " + " | ".join(_escape_table_cell(value) for value in padded_row) + " |")
    return lines


def _normalize_key_value_rows(block: list[list[str]]) -> list[list[str]]:
    rows: list[list[str]] = []
    index = 0
    while index < len(block):
        current = block[index] + [""] * (2 - len(block[index]))
        key, value = current[0], current[1]
        if not key and value and index + 1 < len(block):
            next_row = block[index + 1] + [""] * (2 - len(block[index + 1]))
            if not next_row[0] and next_row[1]:
                rows.append([value, next_row[1]])
                index += 2
                continue
        rows.append([key, value])
        index += 1
    return rows


def _render_block(block: list[list[str]]) -> list[str]:
    if _is_table_header(block[0]):
        return _render_table(block[0], block[1:])

    max_width = max(len(row) for row in block)
    if max_width <= 2:
        return _render_table(["Field", "Value"], _normalize_key_value_rows(block))

    header = [f"Column {index}" for index in range(1, max_width + 1)]
    return _render_table(header, block)


def _render_api_contract() -> list[str]:
    lines = [
        "## Current API Contract",
        "",
        "This Markdown table is the source used by backend contract tests.",
        "",
        "<!-- api-contract:start -->",
    ]
    lines.extend(_render_table(["Method", "Path", "Purpose"], [list(endpoint) for endpoint in API_ENDPOINTS]))
    lines.append("<!-- api-contract:end -->")
    return lines


def render_markdown(rows: list[list[str]]) -> str:
    lines = [
        "# FridgeFriend Specification",
        "",
        "Source workbook: `FridgeFriend_SPEC_filled.xlsx`.",
        "This Markdown version is the editable product spec for agents and code review.",
        "",
        "Regenerate from the workbook with `python scripts/export_spec_markdown.py`.",
        "",
    ]

    index = 0
    while index < len(rows):
        row = rows[index]
        if row == ["SPEC Template"]:
            index += 1
            continue

        if _is_heading(row):
            lines.append(f"{'#' * _heading_level(row[0])} {row[0]}")
            lines.append("")
            index += 1
            continue

        block: list[list[str]] = []
        while index < len(rows) and not _is_heading(rows[index]):
            block.append(rows[index])
            index += 1

        lines.extend(_render_block(block))
        lines.append("")

    lines.extend(_render_api_contract())
    lines.append("")
    return "\n".join(lines)


def export_markdown(source: Path = DEFAULT_SOURCE, output: Path = DEFAULT_OUTPUT) -> None:
    markdown = render_markdown(read_xlsx_rows(source))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the FridgeFriend Excel spec to editable Markdown.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    export_markdown(args.source, args.output)


if __name__ == "__main__":
    main()
