# Bookmarks

Complete guide to managing bookmarks in Power BI reports: listing, configuring, copying between reports, removing, and updating buttons that reference bookmarks.

## Bookmarks Are Generally Bad Practice

Bookmarks should be avoided unless there is a very specific use-case that justifies them. Common caveats:

- **Fragile state capture**: Bookmarks snapshot filter/slicer state, visual visibility, and page context at a point in time. Any report change (adding visuals, renaming fields, changing filters) can silently break bookmarks without warning.
- **Hidden complexity**: Users and developers lose track of what state each bookmark captures, leading to unexpected behavior when bookmarks interact with slicers or cross-filtering.
- **Maintenance burden**: Every structural report change requires re-testing all bookmarks. Bookmark navigators and action buttons that reference bookmarks add another layer of fragile coupling.
- **Performance**: Reports with many bookmarks load slower due to state serialization.
- **Better alternatives**: Page navigation, drillthrough, and report-level filters often achieve the same goal more robustly.

Only use bookmarks when the use-case genuinely requires capturing and restoring a specific combination of filter state and visual visibility that cannot be achieved through standard navigation. When bookmarks are present in an existing report, audit them carefully (see Recommended Workflows below).

## How Bookmarks Work in PBIR

Each bookmark is stored as an individual JSON file in `definition/bookmarks/`:

```
Report.Report/
  definition/
    bookmarks/
      bookmarks.json                    # Bookmark order and groups
      abc123.bookmark.json              # Individual bookmark state
      def456.bookmark.json
```

A bookmark captures a snapshot of: filter/slicer state (data), visual visibility (display), and which page is active (current page). Each capture dimension can be toggled independently.

## Listing and Inspecting

```bash
pbir bookmarks list "Report.Report"           # All bookmarks in report
pbir bookmarks list                            # All bookmarks across all reports
pbir bookmarks list --all-reports              # All reports in a single table

pbir bookmarks json "Report.Report"            # Raw bookmarks.json content
pbir cat "Report.Report/bookmark:Name"         # Full bookmark JSON (filters, visuals, state)
```

## Configuring Bookmark Capture

Each bookmark captures three independent dimensions. Toggle each on/off:

### Data Capture (Filters and Slicers)

Controls whether the bookmark saves and restores filter/slicer selections.

```bash
pbir bookmarks data "Report.Report" "BookmarkName"          # Show current setting
pbir bookmarks data "Report.Report" "BookmarkName" --on     # Capture filters/slicers
pbir bookmarks data "Report.Report" "BookmarkName" --off    # Don't capture filters
```

### Display Capture (Visual Visibility)

Controls whether the bookmark saves and restores which visuals are visible/hidden.

```bash
pbir bookmarks display "Report.Report" "BookmarkName"          # Show current setting
pbir bookmarks display "Report.Report" "BookmarkName" --on     # Capture visibility
pbir bookmarks display "Report.Report" "BookmarkName" --off    # Don't capture visibility
```

### Current Page Capture

Controls whether the bookmark navigates to a specific page when applied.

```bash
pbir bookmarks current-page "Report.Report" "BookmarkName"          # Show current
pbir bookmarks current-page "Report.Report" "BookmarkName" --on     # Capture page
pbir bookmarks current-page "Report.Report" "BookmarkName" --off    # Don't capture page
```

### Target Visuals

Control which visuals the bookmark affects. By default, bookmarks may target specific visuals only.

```bash
pbir bookmarks visuals "Report.Report" "BookmarkName"                     # Show targeted visuals
pbir bookmarks visuals "Report.Report" "BookmarkName" --all               # Apply to all visuals
pbir bookmarks visuals "Report.Report" "BookmarkName" visual1 visual2     # Target specific visuals
```

## Updating Multiple Bookmarks at Once

Use `pbir script` to batch-update bookmark settings:

```bash
# Disable data capture on all bookmarks
pbir script --execute "
import json
from pathlib import Path

report = context.report
bm_dir = Path(report.path) / 'definition' / 'bookmarks'

for bm_file in bm_dir.glob('*.bookmark.json'):
    with open(bm_file) as f:
        bm = json.load(f)
    bm.setdefault('options', {})['suppressData'] = True
    with open(bm_file, 'w') as f:
        json.dump(bm, f, indent=2)
    print(f'Updated: {bm.get(\"displayName\", bm_file.stem)}')
" "Report.Report"

# Rename bookmarks matching a pattern
pbir script --execute "
import json
from pathlib import Path

report = context.report
bm_dir = Path(report.path) / 'definition' / 'bookmarks'

for bm_file in bm_dir.glob('*.bookmark.json'):
    with open(bm_file) as f:
        bm = json.load(f)
    name = bm.get('displayName', '')
    if name.startswith('BM_'):
        bm['displayName'] = name.replace('BM_', '').replace('_', ' ').title()
        with open(bm_file, 'w') as f:
            json.dump(bm, f, indent=2)
        print(f'Renamed: {name} -> {bm[\"displayName\"]}')
" "Report.Report"
```

## Renaming Bookmarks

```bash
pbir bookmarks rename "Report.Report" "Old Name" "New Name"
```

Renaming updates the `displayName` in the bookmark JSON. The internal `name` (filename) remains the same.

## Removing Bookmarks

```bash
# Remove a single bookmark
pbir rm "Report.Report/bookmark:BookmarkName" -f

# Remove all bookmarks, filters, and annotations
pbir rm "Report.Report" --all -f
```

After removing bookmarks, check for buttons that still reference them (see "Finding Buttons" below).

## Copying Bookmarks Between Reports

PBIR stores each bookmark as a separate file, making cross-report copying straightforward:

```bash
# Copy a single bookmark file
pbir cp "Source.Report/bookmark:BookmarkName" "Target.Report/bookmark:BookmarkName"
```

### Manual Copy (for Bulk or Custom)

For bulk copying or when bookmark names need adjustment:

```bash
pbir script --execute "
import json, shutil
from pathlib import Path

source_dir = Path('Source.Report/definition/bookmarks')
target_dir = Path('Target.Report/definition/bookmarks')
target_dir.mkdir(parents=True, exist_ok=True)

# Copy all bookmark files
for bm_file in source_dir.glob('*.bookmark.json'):
    shutil.copy2(bm_file, target_dir / bm_file.name)
    print(f'Copied: {bm_file.name}')

# Update bookmarks.json to include new entries
source_meta = json.loads((source_dir / 'bookmarks.json').read_text())
target_meta_path = target_dir / 'bookmarks.json'

if target_meta_path.exists():
    target_meta = json.loads(target_meta_path.read_text())
else:
    target_meta = {'\$schema': 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/bookmarksMetadata/1.0.0/schema.json', 'items': []}

existing_names = {item['name'] for item in target_meta['items']}
for item in source_meta['items']:
    if item['name'] not in existing_names:
        target_meta['items'].append(item)

target_meta_path.write_text(json.dumps(target_meta, indent=2))
print('Updated bookmarks.json')
" "Report.Report"
```

**Important**: When copying bookmarks between reports, the bookmark's `explorationState` contains references to page IDs (`activeSection`) and visual IDs (`targetVisualNames`). If the target report has different page/visual IDs, these references must be updated or the bookmark will not work correctly. Use `AskUserQuestion` to confirm which pages and visuals the copied bookmarks should target.

## Comparing Bookmarks Between Reports

```bash
pbir diff "Report1.Report" "Report2.Report" --bookmarks
```

## Finding Buttons That Use Bookmarks

Action buttons and bookmark navigators reference bookmarks by name. After renaming or removing bookmarks, find and update these references.

### Action Buttons (visualLink.type = "Bookmark")

Action buttons store bookmark references in `visualLink.bookmark` and `visualLink.type`:

```bash
# Find all action buttons in the report
pbir find "Report.Report/**/actionButton*.Visual"

# Check a button's action configuration
pbir visuals format "Report.Report/Page.Page/Button.Visual" -p visualLink

# Get the bookmark reference
pbir get "Report.Report/Page.Page/Button.Visual.visualLink.bookmark"
pbir get "Report.Report/Page.Page/Button.Visual.visualLink.type"
```

### Updating Button Bookmark References

```bash
# Change which bookmark a button triggers
pbir set "Report.Report/Page.Page/Button.Visual.visualLink.bookmark" --value "NewBookmarkName"

# Change button action type (Back, Bookmark, Drillthrough, PageNavigation, WebUrl, QnA)
pbir set "Report.Report/Page.Page/Button.Visual.visualLink.type" --value "Bookmark"
```

### Bookmark Navigators

Bookmark navigators display a group of bookmarks as a tab strip:

```bash
# Find all bookmark navigators
pbir find "Report.Report/**/bookmarkNavigator*.Visual"

# Check which bookmark group it displays
pbir get "Report.Report/Page.Page/Nav.Visual.bookmarks.bookmarkGroup"
pbir get "Report.Report/Page.Page/Nav.Visual.bookmarks.selectedBookmark"
```

### Bulk Audit: Find All Bookmark References

```bash
pbir script --execute "
for page in context.report.pages:
    for v in page.visuals:
        if v.visual_type == 'actionButton':
            link_type = v.get_property('visualLink', 'type') if hasattr(v, 'visualLink') else None
            bookmark = v.get_property('visualLink', 'bookmark') if hasattr(v, 'visualLink') else None
            if link_type == 'Bookmark' or bookmark:
                print(f'Button: {page.display_name}/{v.name} -> bookmark: {bookmark}')
        elif v.visual_type == 'bookmarkNavigator':
            print(f'Navigator: {page.display_name}/{v.name}')
" "Report.Report"
```

## Bookmark JSON Structure

Key fields in a `*.bookmark.json` file:

| Field | Purpose |
|-------|---------|
| `displayName` | User-visible bookmark name |
| `name` | Internal ID (matches filename) |
| `options.targetVisualNames` | Array of visual IDs this bookmark targets |
| `options.suppressData` | When `true`, bookmark does not capture filter/slicer state |
| `explorationState.activeSection` | Page ID the bookmark navigates to |
| `explorationState.filters` | Captured filter state (slicer values, page filters) |
| `explorationState.sections` | Per-page visual states (visibility, visual-level filters, object overrides) |

## Validation

After any bookmark operation:

```bash
pbir validate "Report.Report"
```

## Recommended Workflows

### Removing Stale Bookmarks

1. **List**: `pbir bookmarks list "Report.Report"` to see all bookmarks
2. **Audit buttons**: Find buttons referencing the bookmark (see "Finding Buttons" above)
3. **Remove**: `pbir rm "Report.Report/bookmark:Name" -f`
4. **Update buttons**: Change or remove bookmark references on affected buttons
5. **Validate**: `pbir validate "Report.Report"`

### Standardizing Bookmarks Across Reports

1. **Export**: Copy bookmarks from the "gold standard" report
2. **Adjust**: Update page IDs and visual IDs for the target report
3. **Import**: Copy bookmark files to target report's `definition/bookmarks/`
4. **Wire up**: Create or update action buttons to reference the new bookmarks
5. **Validate**: `pbir validate "Report.Report"` on each target report

## Creating Bookmarks via CLI

```bash
# Basic bookmark (captures all state)
pbir add bookmark "Report.Report" "Q1 View"

# Skip display state capture
pbir add bookmark "Report.Report" "Data Only" --no-display --no-current-page

# Skip data state capture
pbir add bookmark "Report.Report" "Page View" --no-data

# List bookmarks
pbir bookmarks list "Report.Report"

# Remove bookmark
pbir rm "Report.Report/bookmark:Q1 View" -f
```

Bookmarks created via CLI have empty explorationState -- Power BI Desktop populates the captured state when the bookmark is first applied or updated in the UI. The CLI configures what state the bookmark *will* capture (filters, visibility, current page).

## Changing Bookmark Type

To change a bookmark's capture settings, remove and recreate:

```bash
pbir rm "Report.Report/bookmark:Old" -f
pbir add bookmark "Report.Report" "Old" --no-display
```
