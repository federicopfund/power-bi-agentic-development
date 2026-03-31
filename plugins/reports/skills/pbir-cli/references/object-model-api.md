# Object Model API - Python Integration

**Load this when users need to write Python scripts, use pbir script, or work programmatically with reports.**

## Quick Start

```python
from pbir_object_model import Report, Page, Visual, Theme, Filter

# Load report
report = Report.load("Report.Report")

# Iterate and modify
for page in report.pages:
    for visual in page.visuals:
        visual.title.text = f"Updated: {visual.title.text}"
        visual.title.show = True
        visual.save()

report.save()
```

## Core Classes

### Report
```python
# Loading
report = Report.load("Report.Report")
report = Report.new("Sales Report")     # Create new

# Properties
report.name                          # Folder name
report.display_name                  # Display name
report.export_data_mode             # None, AllowSummarized, AllowSummarizedAndUnderlying
report.model_id                     # Semantic model ID

# Collections
report.pages                        # List[Page]
report.filters                      # List[Filter] (report-level)
report.extension_measures           # List of DAX measures
report.bookmarks                   # List of bookmarks
report.theme                       # Theme object

# Find visuals across all pages
report.find_visuals(visual_type="card")          # list[Visual]
report.find_visuals(title_contains="revenue")    # list[Visual]

# QuerySets (Django-like)
report.query_pages().filter(is_hidden=False)
report.query_filters()
report.query_bookmarks()

# Page management
report.add_page(page)
report.delete_page("PageName")       # Immediate, destructive
report.rename_page("OldName", "NewName")

# Model connection
report.set_model_connection("byPath", path="../Model.SemanticModel")
report.set_model_connection("byConnection", connectionString="...")

# Save
report.save()
```

### Page
```python
# Properties
page.name                           # Internal name
page.display_name                   # Display title
page.width, page.height            # Dimensions
page.visibility                     # AlwaysVisible, HiddenInViewMode
page.ordinal                       # Page order

# Collections
page.visuals                       # List[Visual]
page.filters                       # List[Filter] (page-level)

# Create visual directly
visual = page.create_visual("card", x=100, y=100, width=200, height=150, title="Revenue")

# Background
from pathlib import Path
page.set_background_image(Path("bg.png"), scaling="Fill", transparency=0)
page.clear_background_image()

# Visibility helpers
page.hide()                        # Set to HiddenInViewMode
page.show()                        # Set to AlwaysVisible

# Bulk field replacement
page.replace_fields("OldTable", "Column", "NewTable", "Column")

# Clone
page.clone("Copy of Page")
```

### Visual
```python
# Creating new
visual = Visual.new("card", x=100, y=100, width=200, height=150, title="Revenue")

# Loading with theme cascade
visual = Visual.load(path, apply_theme=True)   # Default
visual = Visual.load(path, apply_theme=False)  # Raw, no theme

# Universal properties (all visuals have these)
visual.title.text = "KPI Title"
visual.title.show = True
visual.title.fontSize = 14
visual.title.fontColor = "#333333"
visual.title.alignment = "center"

visual.background.color = "#FFFFFF"
visual.background.transparency = 0

visual.border.show = True
visual.border.color = "#E0E0E0"
visual.border.radius = 5

visual.padding.top = 10
visual.padding.left = 15

# Visual-specific properties (depends on type)
# Charts: legend, categoryAxis, valueAxis, labels, dataPoint
# Tables: grid, columnHeaders, values
# Cards: categoryLabels, labels

# Example: Chart formatting
visual.legend.show = True
visual.legend.position = "Right"
visual.categoryAxis.titleText = "Category"
visual.valueAxis.gridlineShow = True
visual.labels.show = True

# Save changes
visual.save()
visual.save("new/path")  # Save to different location
```

## Data Binding

```python
# Bind field to visual role (field as "Table.Field" string, then role)
visual.bind_field(
    "Sales.Revenue",             # "Table.Field" format
    "Values",                    # Role name
    aggregation="Sum",           # Sum, Avg, Count, Min, Max, etc.
    field_type="Column",         # Column, Measure (auto-detected if None)
)

# Bind measure (no aggregation needed)
visual.bind_field("Sales.Total Revenue", "Values", field_type="Measure")

# Unbind field (role, then "Table.Field")
visual.unbind_field("Values", "Sales.Revenue")

# Get available roles for this visual type
roles = visual.get_available_roles()  # {"Values": {...}, "Category": {...}}

# Get currently bound fields
visual.get_bound_fields()  # {"Values": [Field("Sales.Revenue")]}

# Field properties
visual.set_field_hidden("Values", "Sales.Revenue", hidden=True)
visual.set_field_display_name("Values", "Sales.Revenue", "Total Sales")

# Bulk replace fields
visual.replace_fields("OldTable", "OldField", "NewTable", "NewField")
```

## Conditional Formatting

**Preferred Pattern**: Extension measures returning theme colors

```python
# Step 1: Add extension measure (at report level)
report.add_extension_measure(
    table="_Formatting",
    name="Performance Color",
    expression='IF([Sales] > [Target], "good", "bad")',
    data_type="String"
)

# Step 2: Apply to visual
visual.set_data_point_color("_Formatting", "Performance Color")

# Advanced: Generic conditional format with selectors
visual.add_conditional_format(
    object_name="dataPoint",
    property_name="fill",
    measure_entity="_Formatting",
    measure_property="Performance Color",
    selector=Visual.dataview_wildcard_selector(1)  # Per data point
)
```

**Builder pattern** (via `visual.cf` proxy):

```python
from pbir_object_model import Field

# Gradient
visual.cf.gradient \
    .field(Field("Sales", "Revenue")) \
    .min_color("#FF0000").max_color("#00FF00") \
    .apply()

# Rules-based
visual.cf.rules \
    .when(Field("Sales", "Variance")).greater_than(0).then_color("good") \
    .when(Field("Sales", "Variance")).less_than(0).then_color("bad") \
    .apply()

# Also available: visual.cf.icons, visual.cf.data_bars
```

### Selector Helpers
```python
# Per data point (most common for conditional formatting)
Visual.dataview_wildcard_selector(1)

# Series level (all points same color)
Visual.dataview_wildcard_selector(0)

# Totals only
Visual.dataview_wildcard_selector(2)

# Target specific field/measure
Visual.metadata_selector("Sales.Revenue")

# Target specific data value
Visual.scope_id_selector("Products", "Category", "Electronics")
```

## Theme Management

```python
theme = report.theme

# Color properties
theme.good = "#00B050"
theme.neutral = "#FFC000"
theme.bad = "#FF0000"
theme.accent = "#118DFF"
theme.background = "#FFFFFF"
theme.foreground = "#323232"

# Data colors (series palette)
theme.data_colors = ["#118DFF", "#12239E", "#E66C37", "#6B007B"]

# Save theme changes
theme.save()
```

## Filters

```python
from pbir_object_model import Filter, Field

# Basic categorical filter (with values)
f = Filter.create_basic(Field("Products", "Category"), values=["Electronics", "Clothing"])

# Generic filter
f = Filter.create(Field("Sales", "Amount"), filter_type="Advanced")

# Specialized factory methods
f = Filter.create_advanced(Field("Sales", "Amount"), operator="GreaterThan", values=[1000])
f = Filter.create_topn(Field("Products", "Product"), n=10, by_field=Field("Sales", "Revenue"))
f = Filter.create_relative_date(Field("Date", "Date"), period="Last12Months")

# Properties and methods
filter.hide()                       # Hide in view mode
filter.lock()                       # Prevent user changes
filter.clear()                      # Clear selections
filter.save()
```

## Bookmarks

```python
from pbir_object_model import Bookmark

bm = Bookmark.create("Filtered View")
bm.captures_data = True
bm.captures_display = True
report.add_bookmark(bm)
```

## Advanced Patterns

### Bulk Visual Formatting
```python
# Apply consistent formatting to all charts
for page in report.pages:
    for visual in page.visuals:
        if visual.visual_type in ['clusteredBarChart', 'lineChart', 'columnChart']:
            visual.title.show = True
            visual.title.fontSize = 14
            visual.border.show = True
            visual.border.color = "#E0E0E0"

            visual.legend.show = True
            visual.legend.position = "Right"
            visual.labels.show = False

            visual.save()

report.save()
```

### Dynamic Visual Creation
```python
# Create KPI cards programmatically
measures = ["Revenue", "Profit", "Orders", "Customers"]
kpi_width = 280
kpi_height = 140

page = report.get_page("Dashboard")
for i, measure in enumerate(measures):
    x = 40 + (i * (kpi_width + 20))
    visual = page.create_visual("card", x=x, y=40, width=kpi_width, height=kpi_height, title=measure)
page.save()
```

## Reference Tables

### Aggregation Types
- **Sum** (0): Numeric sum
- **Avg** (1): Average
- **Count** (2): Row count
- **Min** (3): Minimum value
- **Max** (4): Maximum value
- **CountNonNull** (5): Non-empty count
- **Median** (6): Median value

### Common Visual Types
- **Charts**: `clusteredBarChart`, `lineChart`, `pieChart`, `columnChart`, `donutChart`
- **Tables**: `tableEx`, `pivotTable`, `matrix`
- **Cards**: `card`, `multiRowCard`, `kpi`, `gauge`
- **Filters**: `slicer`
- **Containers**: `textbox`, `image`, `shape`

### Theme Color Names
- **good**: Positive/success color
- **bad**: Negative/error color
- **neutral**: Warning/neutral color
- **accent**: Highlight/accent color
- **foreground**: Text color
- **background**: Background color
