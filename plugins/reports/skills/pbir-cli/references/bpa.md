# Best Practice Analyzer (BPA)

JSON-driven rule engine for automated report quality checks. Evaluates rules against report objects and reports violations with optional auto-fix.

## Quick Start

Run BPA analysis via `pbir script`:

```bash
# Default analysis (all built-in rules)
pbir script --execute "
from pbir_object_model.bpa import BpaEngine
engine = BpaEngine.default()
result = engine.analyze(context.report)
print(result.summary())
for v in result.violations:
    print(f'  [{v.severity_label}] {v.location}: {v.message}')
" "Report.Report"

# Tiered rules (builtin + user + report-scoped)
pbir script --execute "
from pbir_object_model.bpa import BpaEngine
engine = BpaEngine.with_tiers(context.report)
result = engine.analyze(context.report)
print(result.summary())
" "Report.Report"
```

## Rule Sources

### Built-in Rules

Ship with the package. Cover layout, performance, governance, and accessibility:

| ID | Scope | Sev | Description |
|----|-------|-----|-------------|
| `PBIR_HIDDEN_VISUAL` | Visual | 1 | Hidden visual consuming resources |
| `PBIR_NO_TITLE` | Visual | 2 | Visual without title enabled |
| `PBIR_TOO_MANY_FIELDS` | Visual | 2 | Visual with excessive field bindings |
| `PBIR_DROP_SHADOW` | Visual | 1 | Drop shadow enabled (performance) |
| `PBIR_SHOW_ALL_ITEMS` | Visual | 3 | "Show items with no data" (performance) |
| `PBIR_HARDCODED_COLOR` | Visual | 1 | Hex colors bypassing theme |
| `PBIR_UNUSED_EXTENSION` | Report | 2 | Unused extension measures |
| `PBIR_VISUAL_OFF_CANVAS` | Visual | 2 | Visual outside page bounds |
| `PBIR_TOO_MANY_VISUALS` | Page | 2 | Page exceeds visual count threshold |
| `PBIR_MISSING_ALT_TEXT` | Visual | 1 | Missing alt text (accessibility) |

### User Rules

Personal rules at `~/.config/pbir/bpa-rules.json`. Apply to all reports:

```json
[
  {
    "ID": "TEAM_MAX_PAGES",
    "Name": "Report exceeds page limit",
    "Category": "Governance",
    "Severity": 2,
    "Scope": "Report",
    "Expression": "page_count > {max_pages}",
    "Params": {"max_pages": 10},
    "Description": "Report has %page_count% pages (max %max_pages%)."
  }
]
```

### Report Rules

Rules stored in `<definition>/.bpa.json` alongside `report.json`. Travel with the report:

```python
from pbir_object_model.bpa import BpaRule, RuleScope, Severity

rule = BpaRule(
    id="PROJECT_CARD_TITLES",
    name="Card visuals must have titles",
    category="Project Standards",
    severity=Severity.WARNING,
    scope=RuleScope.VISUAL,
    expression="visual_type == 'card' and has_title == false",
    description="Card '%name%' is missing a title.",
)
report.add_bpa_rule(rule)
report.save()
```

### URL Rules (Centralized Team Rules)

Point to a shared rules file hosted on GitHub, SharePoint, or any HTTP(S) URL:

```python
engine = BpaEngine.from_files(
    "builtin",
    "https://raw.githubusercontent.com/team/repo/main/bpa-rules.json",
    "./local-overrides.json",
)
```

Rules merge in order -- later sources override earlier ones by rule ID.

## Rule Tiers (Priority Order)

Rules merge: **builtin -> user -> report**. Later tiers override earlier by ID.

```python
# Automatic tier merging
engine = BpaEngine.with_tiers(report)

# Manual tier control
from pbir_object_model.bpa import load_tiered_rules
rules = load_tiered_rules(report)  # Merged list

# Individual tiers
from pbir_object_model.bpa import load_user_rules, load_report_rules
user = load_user_rules()           # ~/.config/pbir/bpa-rules.json
report_rules = load_report_rules(report)  # .bpa.json
```

## Rule Scopes

Rules evaluate against specific object types:

| Scope | Target | Context Keys |
|-------|--------|-------------|
| `Report` | Report | `page_count`, `has_theme`, `extension_measure_count`, `filter_count` |
| `Page` | Each page | `visual_count`, `width`, `height`, `page_type`, `overlap_count` |
| `Visual` | Each visual | `visual_type`, `field_count`, `has_title`, `is_hidden`, `x`, `y`, `width`, `height` |
| `Filter` | Each filter | `name`, `type`, `is_hidden` |
| `Bookmark` | Each bookmark | `name`, `display_name` |
| `Measure` | Each extension measure | `name`, `table`, `expression`, `data_type`, `hidden` |
| `VisualCalculation` | Each visual calc | `name`, `expression`, `language`, `role`, `visual_type` |

Multi-scope rules: `"Scope": "Page, Visual"` evaluates against both pages and visuals.

## DSL Expression Language

Rules use a boolean expression that returns `true` for violations:

```
# Comparisons
field_count > 10
visual_type == 'card'
has_title == false

# Logical operators
is_hidden == true and field_count > 0
visual_type == 'textbox' or visual_type == 'shape'
not has_alt_text

# String operations
name contains 'draft'
visual_type startswith 'clustered'
name matches '^[a-f0-9]{16}$'

# Membership
visual_type in ['card', 'multiRowCard', 'kpi']
visual_type not in ['textbox', 'shape', 'image']

# Aggregation (over nested collections)
any(filters, is_hidden == true)
all(fields, name contains 'Revenue')

# Arithmetic
width * height > 500000
x + width > page_width

# Parameters (with defaults from Params)
field_count > {max_fields}
height > {max_height}
```

## Suppressing Rules (bpa-ignore)

Suppress rules at any level using annotations:

### Python API

```python
# Suppress on a specific visual
visual.add_bpa_ignore("PBIR_DROP_SHADOW")
visual.save()

# Suppress all rules on a page
page.add_bpa_ignore("*")
page.save()

# Suppress at report level
report.add_bpa_ignore("PBIR_UNUSED_EXTENSION")
report.save()

# List/remove suppressions
visual.list_bpa_ignores()        # ["PBIR_DROP_SHADOW"]
visual.remove_bpa_ignore("PBIR_DROP_SHADOW")
visual.save()
```

### Via pbir script

```bash
pbir script --execute "
p = context.report.pages[0]
for v in p.visuals:
    if v.visual_type == 'shape':
        v.add_bpa_ignore('PBIR_HARDCODED_COLOR')
        v.save()
print('done')
" "Report.Report"
```

Annotations persist as `{"name": "bpa-ignore", "value": "RULE1, RULE2"}` in the object's JSON file.

## Filtering Analysis

```python
# By category
result = engine.analyze(report, categories=["Performance", "Layout"])

# By minimum severity (1=info, 2=warning, 3=error)
result = engine.analyze(report, severity_min=2)

# Specific rules only
result = engine.analyze(report, rule_ids=["PBIR_SHOW_ALL_ITEMS", "PBIR_DROP_SHADOW"])

# Single page
result = engine.analyze(report, page_name="Dashboard")
```

## Auto-Fix

Rules with `FixExpression` can be auto-fixed:

```python
from pbir_object_model.bpa import apply_fix, apply_fixes

# Single fix
for v in result.violations:
    if v.has_fix:
        change = apply_fix(v, visual_obj)
        # Caller must call visual_obj.save() after

# Batch fix (dry-run first)
objects = {"Page.Page/card.Visual": visual_obj, ...}
dry = apply_fixes(result.violations, objects, dry_run=True)
for c in dry.changes:
    print(f"  {c.property_path}: {c.old_value} -> {c.new_value}")

# Apply for real
fix_result = apply_fixes(result.violations, objects)
```

Fix expressions are simple property assignments: `is_hidden = false`, `title.show = true`, `width = {max_width}`.

## Report-Scoped Rule Management

```python
# List report rules
for rule in report.bpa_rules:
    print(f"{rule.id}: {rule.name}")

# Add a report rule
report.add_bpa_rule(rule)

# Remove a report rule
report.remove_bpa_rule("PROJECT_CARD_TITLES")
```

## Engine Configuration

```python
engine = BpaEngine.default()

# Disable specific rules
engine.disable_rules(["PBIR_DROP_SHADOW", "PBIR_HARDCODED_COLOR"])

# Override parameters globally
engine.set_params({"max_fields": 20, "max_visuals": 30})

# Add custom rules at runtime
engine.add_rules([custom_rule1, custom_rule2])

# List/filter rules
engine.list_rules(category="Performance")
engine.list_rules(scope="Visual", severity=3)
engine.get_rule("PBIR_HIDDEN_VISUAL")
```

## Result Inspection

```python
result = engine.analyze(report)

# Summary
print(result.summary())        # "Failed (2 errors, 5 warnings, 3 info)"
print(result.is_valid)          # False (has severity-3 violations)
print(result.total_count)       # 10
print(result.error_count)       # 2 (severity 3)
print(result.warning_count)     # 5 (severity 2)

# Filter violations
errors = result.by_severity(3)
perf = result.by_category("Performance")
visual_issues = result.by_scope("Visual")
hidden = result.by_rule("PBIR_HIDDEN_VISUAL")

# JSON output
import json
print(json.dumps(result.to_dict(), indent=2))
```

## Writing Custom Rules

### Rule JSON Format

```json
{
  "ID": "CUSTOM_RULE_ID",
  "Name": "Human-readable name",
  "Category": "Category Name",
  "Severity": 2,
  "Scope": "Visual",
  "Expression": "boolean DSL expression",
  "FixExpression": "property = value",
  "Description": "Message with %placeholder% interpolation.",
  "Params": {"threshold": 10},
  "Tags": ["tag1", "tag2"],
  "Enabled": true
}
```

### Context Keys Reference

**Report scope**: `name`, `display_name`, `page_count`, `has_theme`, `has_custom_theme`, `filter_count`, `extension_measure_count`, `unused_extension_measure_count`, `unused_custom_visual_count`, `active_page_is_first`

**Page scope**: `name`, `display_name`, `width`, `height`, `is_hidden`, `page_type` (regular/tooltip/drillthrough), `page_visibility`, `visual_count`, `visible_visual_count`, `hidden_visual_count`, `overlap_count`, `filter_count`, `show_all_items_count`, `hardcoded_color_count`

**Visual scope**: `name`, `visual_type`, `x`, `y`, `width`, `height`, `z`, `is_hidden`, `field_count`, `hidden_field_count`, `has_title`, `has_alt_text`, `has_sort`, `has_show_all_items`, `has_hardcoded_colors`, `bespoke_override_count`, `tab_order`, `page_width`, `page_height`

**Measure scope**: `name`, `table`, `full_name`, `expression`, `data_type`, `hidden`, `has_expression`, `has_description`, `has_format_string`, `format_string`, `description`, `data_category`, `display_folder`

**VisualCalculation scope**: `name`, `expression`, `language`, `role`, `has_expression`, `visual_name`, `visual_type`, `page_name`
