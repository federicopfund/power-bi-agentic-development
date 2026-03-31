#!/usr/bin/env python3
"""
Audit slicer usage across report pages.

Usage with pbir script:
    pbir script audit_slicers.py "Report.Report"

Checks:
    - Which fields have slicers on multiple pages (sync risk)
    - Which fields have slicers on only one page (coverage gap)
    - Slicer count per page

Can also be run standalone:
    python3 audit_slicers.py "Report.Report"
"""

import argparse
import json
import subprocess
import sys

# region Functions


def run_pbir(args: list[str]) -> tuple[bool, str]:
    """Run a pbir CLI command and return (success, output)."""
    try:
        result = subprocess.run(["pbir"] + args, capture_output=True, text=True, check=True)
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()


def get_report_tree(report_path: str) -> dict | None:
    """Get report tree as JSON."""
    ok, output = run_pbir(["tree", report_path, "-v", "--json"])
    if not ok:
        print(f"Error reading report: {output}", file=sys.stderr)
        return None
    return json.loads(output)


def audit_slicers(report_path: str) -> None:
    """Audit slicer fields across all pages."""
    ok, output = run_pbir(
        [
            "script",
            "--execute",
            """
from collections import defaultdict

field_pages = defaultdict(list)
page_slicers = {}

for page in context.report.pages:
    slicers = []
    for v in page.visuals:
        if 'slicer' not in v.visual_type.lower():
            continue
        slicers.append(v)
        bindings = v.get_field_bindings()
        for role, fields in bindings.items():
            for f in (fields if isinstance(fields, list) else [fields]):
                field_pages[f].append(page.display_name)
    page_slicers[page.display_name] = slicers

# Page summary
print("=== Slicer Count Per Page ===")
for page_name, slicers in page_slicers.items():
    count = len(slicers)
    status = "OK" if count <= 3 else "HIGH" if count <= 5 else "CRITICAL"
    if count > 0:
        print(f"  {page_name}: {count} slicers ({status})")
        for s in slicers:
            print(f"    {s.name} ({s.visual_type})")
    else:
        print(f"  {page_name}: no slicers")

# Field sync analysis
multi_page = {f: p for f, p in field_pages.items() if len(p) > 1}
single_page = {f: p for f, p in field_pages.items() if len(p) == 1}

if multi_page:
    print()
    print("=== Fields On Multiple Pages (sync risk) ===")
    for field, pages in sorted(multi_page.items()):
        print(f"  {field}: {len(pages)} pages -- {', '.join(pages)}")

if single_page:
    print()
    print("=== Fields On Single Page Only ===")
    for field, pages in sorted(single_page.items()):
        print(f"  {field}: {pages[0]}")

if not field_pages:
    print()
    print("No slicers found in report.")
""",
            report_path,
        ]
    )

    if ok:
        print(output)
    else:
        print(f"Error: {output}", file=sys.stderr)
        sys.exit(1)


# endregion


# region Main


def main():
    parser = argparse.ArgumentParser(description="Audit slicer usage across report pages")
    parser.add_argument(
        "report_path",
        help='Report path (e.g., "Report.Report")',
    )

    args = parser.parse_args()
    audit_slicers(args.report_path)


# endregion


if __name__ == "__main__":
    main()
