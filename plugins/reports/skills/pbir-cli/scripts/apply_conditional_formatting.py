#!/usr/bin/env python3
"""
Apply measure-based conditional formatting patterns to Power BI visuals.
Implements the preferred pattern: extension measures returning theme colors.
"""

import argparse
import subprocess
import sys


def run_pbir_cmd(cmd: list[str], capture_output=False) -> tuple[bool, str]:
    """Execute pbir command and return success status and output"""
    try:
        result = subprocess.run(["pbir"] + cmd, capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        error_msg = f"Error executing pbir {' '.join(cmd)}: {e.stderr}"
        if not capture_output:
            print(error_msg)
        return False, error_msg


def create_formatting_measure(
    report_path: str, table_name: str, measure_name: str, expression: str, description: str = ""
) -> bool:
    """Create extension measure for conditional formatting"""

    success, _ = run_pbir_cmd(
        [
            "dax",
            "measures",
            "add",
            report_path,
            "-t",
            table_name,
            "-n",
            measure_name,
            "-e",
            expression,
            "--data-type",
            "String",
        ]
    )

    if success:
        print(f"[ok] Created formatting measure: {table_name}.{measure_name}")
        if description:
            print(f"   Purpose: {description}")

    return success


def apply_conditional_formatting_patterns(
    report_path: str, pattern_type: str = "performance", target_visuals: list[str] | None = None
) -> bool:
    """
    Apply common conditional formatting patterns.

    Patterns:
    - performance: good/bad/neutral based on targets
    - variance: positive/negative variance coloring
    - status: categorical status indicators
    - trend: trend direction indicators
    - custom: user-defined expression
    """

    print(f"Applying {pattern_type} conditional formatting pattern...")

    # Define formatting patterns
    patterns = {
        "performance": {
            "measures": [
                {
                    "table": "_Formatting",
                    "name": "Performance Color",
                    "expression": 'IF([Actual] >= [Target], "good", IF([Actual] >= [Target] * 0.9, "neutral", "bad"))',
                    "description": "Color based on performance vs target (good ≥100%, neutral ≥90%, bad <90%)",
                }
            ]
        },
        "variance": {
            "measures": [
                {
                    "table": "_Formatting",
                    "name": "Variance Color",
                    "expression": 'IF([Variance] > 0, "good", IF([Variance] = 0, "neutral", "bad"))',
                    "description": "Positive variance = good, zero = neutral, negative = bad",
                }
            ]
        },
        "status": {
            "measures": [
                {
                    "table": "_Formatting",
                    "name": "Status Color",
                    "expression": """SWITCH([Status],
                        "Complete", "good",
                        "In Progress", "neutral",
                        "Delayed", "bad",
                        "foreground")""",
                    "description": "Status-based coloring (Complete/In Progress/Delayed)",
                }
            ]
        },
        "trend": {
            "measures": [
                {
                    "table": "_Formatting",
                    "name": "Trend Color",
                    "expression": """VAR TrendDirection = [Current Period] - [Previous Period]
                    RETURN IF(TrendDirection > 0, "good", IF(TrendDirection = 0, "neutral", "bad"))""",
                    "description": "Trend direction coloring (up=good, flat=neutral, down=bad)",
                },
                {
                    "table": "_Formatting",
                    "name": "Trend Icon",
                    "expression": """VAR TrendDirection = [Current Period] - [Previous Period]
                    RETURN IF(TrendDirection > 0, "▲", IF(TrendDirection = 0, "●", "▼"))""",
                    "description": "Trend direction icons (▲●▼)",
                },
            ]
        },
    }

    if pattern_type not in patterns:
        print(f"Unknown pattern type: {pattern_type}")
        return False

    pattern = patterns[pattern_type]

    # Create formatting measures
    for measure in pattern["measures"]:
        success = create_formatting_measure(
            report_path=report_path,
            table_name=measure["table"],
            measure_name=measure["name"],
            expression=measure["expression"],
            description=measure["description"],
        )
        if not success:
            return False

    # Apply formatting to visuals if specified
    if target_visuals:
        for visual_path in target_visuals:
            apply_to_visual(report_path, visual_path, pattern)

    return True


def apply_to_visual(report_path: str, visual_path: str, pattern: dict) -> bool:
    """Apply conditional formatting to a specific visual"""

    # For now, provide guidance since visual-specific application
    # requires knowing the visual's data structure
    print(f"\n--> To apply to visual {visual_path}:")

    for measure in pattern["measures"]:
        measure_ref = f"{measure['table']}.{measure['name']}"
        print(f'   pbir visuals cf "{visual_path}" --measure "{measure_ref}"')

    return True


def setup_theme_colors(report_path: str) -> bool:
    """Ensure theme has proper semantic colors defined"""

    print("Setting up semantic theme colors...")

    theme_colors = {
        "good": "#00B050",  # Green for positive/good
        "neutral": "#FFC000",  # Amber for neutral/warning
        "bad": "#FF0000",  # Red for negative/bad
        "accent": "#118DFF",  # Blue for accent/highlight
    }

    for color_name, color_value in theme_colors.items():
        success, _ = run_pbir_cmd(
            ["theme", "set-colors", report_path, "--" + color_name, color_value]
        )
        if success:
            print(f"[ok] Set theme color {color_name}: {color_value}")
        else:
            print(f"[!!]  Warning: Could not set theme color {color_name}")

    return True


def list_available_patterns():
    """Display available formatting patterns"""
    patterns_info = {
        "performance": "Performance vs target (good ≥100%, neutral ≥90%, bad <90%)",
        "variance": "Variance-based coloring (positive=good, zero=neutral, negative=bad)",
        "status": "Status categories (Complete=good, In Progress=neutral, Delayed=bad)",
        "trend": "Trend direction (up=good, flat=neutral, down=bad) with icons",
    }

    print("Available conditional formatting patterns:")
    for pattern, description in patterns_info.items():
        print(f"  {pattern:12} - {description}")


def main():
    parser = argparse.ArgumentParser(description="Apply conditional formatting patterns")
    parser.add_argument("report_path", help="Path to report (e.g., Report.Report)")
    parser.add_argument(
        "--pattern",
        choices=["performance", "variance", "status", "trend"],
        default="performance",
        help="Formatting pattern to apply",
    )
    parser.add_argument(
        "--visual",
        action="append",
        dest="visuals",
        help="Visual paths to apply formatting to (can use multiple times)",
    )
    parser.add_argument("--setup-theme", action="store_true", help="Set up semantic theme colors")
    parser.add_argument(
        "--list-patterns", action="store_true", help="List available patterns and exit"
    )

    # Custom pattern options
    parser.add_argument("--custom-expression", help="Custom DAX expression for formatting")
    parser.add_argument(
        "--custom-name", default="Custom Format", help="Name for custom formatting measure"
    )

    args = parser.parse_args()

    if args.list_patterns:
        list_available_patterns()
        return

    # Setup theme colors if requested
    if args.setup_theme:
        setup_theme_colors(args.report_path)

    # Apply custom pattern if provided
    if args.custom_expression:
        success = create_formatting_measure(
            report_path=args.report_path,
            table_name="_Formatting",
            measure_name=args.custom_name,
            expression=args.custom_expression,
            description="Custom conditional formatting measure",
        )
        if not success:
            sys.exit(1)
        return

    # Apply selected pattern
    success = apply_conditional_formatting_patterns(
        report_path=args.report_path, pattern_type=args.pattern, target_visuals=args.visuals
    )

    if success:
        print(f"\n[ok] Conditional formatting pattern '{args.pattern}' applied successfully!")
        print("\n>> Next steps:")
        print("   1. Bind your data fields to visuals: pbir visuals bind")
        print("   2. Apply formatting to specific visuals: pbir visuals cf")
        print("   3. Validate results: pbir validate")
    else:
        print("[FAIL] Failed to apply conditional formatting pattern")
        sys.exit(1)


if __name__ == "__main__":
    main()
