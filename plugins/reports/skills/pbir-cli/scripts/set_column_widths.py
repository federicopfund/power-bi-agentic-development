#!/usr/bin/env python3
"""
Set column widths on table/matrix visuals.

Usage with pbir script:
    pbir script set_column_widths.py "Report.Report/Page.Page/Table.Visual"

Demonstrates:
    - Disabling auto-size column width
    - Setting a uniform width for all columns
    - Setting per-column widths using metadata selectors
    - Reading current column widths

Can also be run standalone:
    python3 set_column_widths.py "Report.Report/Page.Page/Table.Visual" --width 150
    python3 set_column_widths.py "Report.Report/Page.Page/Table.Visual" --per-column '{"Sales.Revenue": 200, "Products.Name": 300}'
"""

import argparse
import json
import subprocess
import sys
from typing import Any

# region Functions


def run_pbir(args: list[str], capture: bool = True) -> tuple[bool, str]:
    """Run a pbir CLI command and return (success, output)."""
    try:
        result = subprocess.run(["pbir"] + args, capture_output=True, text=True, check=True)
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()


def get_visual_json(visual_path: str) -> dict[str, Any] | None:
    """Read the visual JSON via pbir cat."""
    ok, output = run_pbir(["cat", visual_path, "--json"])
    if not ok:
        print(f"Error reading visual: {output}", file=sys.stderr)
        return None
    return json.loads(output)


def get_current_widths(visual_path: str) -> dict[str, float]:
    """Read current per-column widths from the visual.

    Returns:
        Dict mapping field names to pixel widths, e.g.:
        {"Customers.Name": 175.4, "Sales.Revenue": 134.0}
    """
    data = get_visual_json(visual_path)
    if not data:
        return {}

    objects = data.get("visual", {}).get("objects", {})
    entries = objects.get("columnWidth", [])

    widths = {}
    for entry in entries:
        selector = entry.get("selector", {})
        field = selector.get("metadata", "")
        value_expr = entry.get("properties", {}).get("value", {}).get("expr", {})
        literal = value_expr.get("Literal", {}).get("Value", "")

        if field and literal:
            # Strip the "D" suffix from the literal value
            width = float(literal.rstrip("D"))
            widths[field] = width

    return widths


def get_bound_fields(visual_path: str) -> list[str]:
    """Get the list of fields bound to the visual."""
    ok, output = run_pbir(["visuals", "bind", visual_path, "--show", "--json"])
    if not ok:
        # Fallback: try to parse from tree
        return []
    try:
        bindings = json.loads(output)
        fields = []
        for role_fields in bindings.values():
            if isinstance(role_fields, list):
                fields.extend(role_fields)
            elif isinstance(role_fields, str):
                fields.append(role_fields)
        return fields
    except (json.JSONDecodeError, AttributeError):
        return []


def disable_auto_size(visual_path: str) -> bool:
    """Disable auto-size column width (required before setting fixed widths)."""
    ok, output = run_pbir(
        [
            "set",
            f"{visual_path}.columnHeaders.autoSizeColumnWidth",
            "--value",
            "false",
        ]
    )
    if not ok:
        print(f"Error disabling auto-size: {output}", file=sys.stderr)
    return ok


def set_uniform_width(visual_path: str, width: int) -> bool:
    """Set the same width for all columns via the default columnWidth.value."""
    ok, output = run_pbir(
        [
            "set",
            f"{visual_path}.columnWidth.value",
            "--value",
            str(width),
        ]
    )
    if not ok:
        print(f"Error setting uniform width: {output}", file=sys.stderr)
    return ok


def set_per_column_width(visual_path: str, field: str, width: int) -> bool:
    """Set width for a specific column using format-field with metadata selector."""
    ok, output = run_pbir(
        [
            "visuals",
            "format-field",
            visual_path,
            "columnWidth",
            "value",
            "--field",
            field,
            "--value",
            str(width),
        ]
    )
    if not ok:
        print(f"Error setting width for {field}: {output}", file=sys.stderr)
    return ok


def show_widths(visual_path: str) -> None:
    """Display current column widths."""
    widths = get_current_widths(visual_path)
    if widths:
        print("Current column widths:")
        max_field_len = max(len(f) for f in widths)
        for field, width in widths.items():
            print(f"  {field:<{max_field_len}}  {width:>7.1f}px")
    else:
        print("No per-column widths set (using auto-size or default).")


# endregion


# region Main


def main():
    parser = argparse.ArgumentParser(description="Set column widths on table/matrix visuals")
    parser.add_argument(
        "visual_path",
        help='Visual path (e.g., "Report.Report/Page.Page/Table.Visual")',
    )
    parser.add_argument(
        "--width",
        "-w",
        type=int,
        help="Uniform width in pixels for all columns",
    )
    parser.add_argument(
        "--per-column",
        type=str,
        help='JSON mapping of field -> width, e.g. \'{"Sales.Revenue": 200, "Products.Name": 300}\'',
    )
    parser.add_argument(
        "--show",
        "-s",
        action="store_true",
        help="Show current column widths and exit",
    )

    args = parser.parse_args()

    if args.show:
        show_widths(args.visual_path)
        return

    if not args.width and not args.per_column:
        parser.error("Specify --width for uniform width or --per-column for per-field widths")

    # Step 1: Disable auto-size (required for fixed widths)
    print("Disabling auto-size column width...")
    if not disable_auto_size(args.visual_path):
        sys.exit(1)

    # Step 2a: Uniform width
    if args.width:
        print(f"Setting all columns to {args.width}px...")
        if not set_uniform_width(args.visual_path, args.width):
            sys.exit(1)
        print(f"Done -- all columns set to {args.width}px")

    # Step 2b: Per-column widths
    if args.per_column:
        try:
            column_widths = json.loads(args.per_column)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON for --per-column: {e}", file=sys.stderr)
            sys.exit(1)

        for field, width in column_widths.items():
            print(f"  {field}: {width}px")
            if not set_per_column_width(args.visual_path, field, int(width)):
                sys.exit(1)

        print(f"Done -- {len(column_widths)} columns configured")

    # Step 3: Validate
    report_path = args.visual_path.split("/")[0]
    print(f"\nValidating {report_path}...")
    ok, output = run_pbir(["validate", report_path])
    if ok:
        print("Validation passed")
    else:
        print(f"Validation issues: {output}", file=sys.stderr)


# endregion


if __name__ == "__main__":
    main()
