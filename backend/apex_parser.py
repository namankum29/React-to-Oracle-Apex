"""React project parser - scans .jsx/.tsx files to detect forms, reports, dashboards."""
import re
import zipfile
from pathlib import Path
from typing import Dict, List, Any


JSX_EXT = {".jsx", ".tsx", ".js", ".ts"}
SKIP_DIRS = {"node_modules", "dist", "build", ".git", ".next", "coverage", "out"}


def extract_zip(zip_path: Path, dest: Path) -> Path:
    """Extract ZIP, return the actual project root (handles nested folder case)."""
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(dest)

    # Find project root containing package.json
    for p in dest.rglob("package.json"):
        if not any(part in SKIP_DIRS for part in p.parts):
            return p.parent
    # Fallback: first directory or dest itself
    entries = [p for p in dest.iterdir() if p.is_dir()]
    return entries[0] if len(entries) == 1 else dest


def list_source_files(root: Path) -> List[Path]:
    files = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix not in JSX_EXT:
            continue
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        files.append(p)
    return files


def find_compiled_css(root: Path) -> str:
    """Read compiled CSS from dist/build folder."""
    combined = []
    for sub in ("dist/assets", "build/static/css", "dist", "build"):
        d = root / sub
        if d.exists():
            for css in d.rglob("*.css"):
                try:
                    combined.append(css.read_text(encoding="utf-8", errors="ignore"))
                except Exception:
                    pass
    return "\n".join(combined)


# ----- Detection heuristics -----

FORM_INPUT_RE = re.compile(
    r"<(input|textarea|select)\b[^>]*\bname\s*=\s*[\"']([a-zA-Z0-9_]+)[\"']", re.IGNORECASE
)
CONTROLLED_INPUT_RE = re.compile(
    r"value=\{[^}]*\.([a-zA-Z0-9_]+)\}",
    re.IGNORECASE
)

ONCHANGE_FIELD_RE = re.compile(
    r"onChange=\{[^}]*?([a-zA-Z0-9_]+)\}",
    re.IGNORECASE
)

PLACEHOLDER_RE = re.compile(
    r'placeholder=["\']([a-zA-Z0-9_ ]+)["\']',
    re.IGNORECASE
)
FORM_INPUT_VALUE_RE = re.compile(
    r"value\s*=\s*\{[^}]*?\.([a-zA-Z0-9_]+)\s*\}"
)
USE_STATE_OBJ_RE = re.compile(
    r"useState\s*\(\s*\{([^}]+)\}\s*\)", re.MULTILINE | re.DOTALL
)
EMPTY_FORM_RE = re.compile(
    r"(?:emptyForm|formData|initialForm|defaultValues|initialState|emptyValues|emptyState|empty[A-Z]\w*)"
    r"(?:\s*:\s*[A-Za-z_][A-Za-z0-9_<>\[\],\s]*)?"  # optional TS type annotation
    r"\s*=\s*\{([^}]+)\}",
    re.MULTILINE | re.DOTALL,
)
KEY_NAME_RE = re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*:")
KEY_VALUE_RE = re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*([^,\n}]+)")
CLASSNAME_RE = re.compile(r'className\s*=\s*["\']([^"\']+)["\']')
COMPONENT_NAME_RE = re.compile(
    r"(?:export\s+default\s+(?:function|const)|function|const)\s+([A-Z][A-Za-z0-9_]+)"
)
TABLE_RE = re.compile(r"<table\b", re.IGNORECASE)
TABLE_HEADER_RE = re.compile(r"<th\b", re.IGNORECASE)
TH_TEXT_RE = re.compile(
    r"<th[^>]*>(.*?)</th>",
    re.IGNORECASE | re.DOTALL
)
MAP_RENDER_RE = re.compile(r"\.map\s*\(\s*\(?\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\)?\s*=>\s*[\(\<]")
RECHARTS_RE = re.compile(r"from\s+['\"]recharts['\"]")
CHART_TAG_RE = re.compile(r"<(LineChart|BarChart|PieChart|AreaChart|RadarChart)\b")
STAT_CARD_RE = re.compile(r"\b(stat|statistic|metric|kpi)s?\b", re.IGNORECASE)

BUTTON_RE = re.compile(
    r"<button\b[^>]*>(.*?)</button>",
    re.IGNORECASE | re.DOTALL
)


def extract_field_defaults(text: str) -> Dict[str, str]:
    """Map fieldName -> default literal from emptyForm/formData/initialForm.

    Only used as a deterministic source for APEX computations and session-state
    item defaulting. Strings are stripped of surrounding quotes.
    """
    defaults: Dict[str, str] = {}
    for m in EMPTY_FORM_RE.finditer(text):
        body = m.group(1)
        for km in KEY_VALUE_RE.finditer(body):
            key = km.group(1)
            val = km.group(2).strip()
            # Strip trailing comma/whitespace artifacts
            val = val.rstrip(",").strip()
            # Unwrap simple string literals
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            if val in ("true", "false", "null", "undefined"):
                val = "" if val in ("null", "undefined") else val
            defaults[key] = val
    return defaults


def extract_field_names(text: str) -> List[str]:
    fields = set()
    for m in EMPTY_FORM_RE.finditer(text):
        for k in KEY_NAME_RE.finditer(m.group(1)):
            fields.add(k.group(1))
    for m in USE_STATE_OBJ_RE.finditer(text):
        body = m.group(1)
        if ":" in body and len(body) < 600:
            for k in KEY_NAME_RE.finditer(body):
                fields.add(k.group(1))
    for m in FORM_INPUT_RE.finditer(text):
        fields.add(m.group(2))
    for m in FORM_INPUT_VALUE_RE.finditer(text):
        fields.add(m.group(1))
    for m in CONTROLLED_INPUT_RE.finditer(text):
        fields.add(m.group(1))
    for m in ONCHANGE_FIELD_RE.finditer(text):
        fields.add(m.group(1))
    # Filter false positives
    blacklist = {"const", "let", "var", "true", "false", "null", "undefined"}
    return sorted([f for f in fields if f.lower() not in blacklist and len(f) <= 40])


def extract_classnames(text: str) -> List[str]:
    classes = set()
    for m in CLASSNAME_RE.finditer(text):
        for cls in m.group(1).split():
            if len(cls) < 80:
                classes.add(cls)
    return sorted(classes)

def extract_table_columns(text: str) -> List[str]:
    cols = []

    for m in TH_TEXT_RE.finditer(text):
        label = re.sub(r"<.*?>", "", m.group(1)).strip()

        if label and len(label) < 40:
            cols.append(
                label.upper().replace(" ", "_")
            )

    return sorted(list(set(cols)))


    def extract_buttons(text: str) -> List[str]:
        buttons = []

    for m in BUTTON_RE.finditer(text):
        label = re.sub(r"<.*?>", "", m.group(1)).strip()

        if label and len(label) < 40:
            buttons.append(label)

    return sorted(list(set(buttons)))


# def extract_classnames(text: str) -> List[str]:
#     classes = set()

#     for m in CLASSNAME_RE.finditer(text):
#         for cls in m.group(1).split():
#             if len(cls) < 80:
#                 classes.add(cls)

#     return sorted(classes)


def extract_buttons(text: str) -> List[str]:
    buttons = []

    for m in BUTTON_RE.finditer(text):
        label = re.sub(r"<.*?>", "", m.group(1)).strip()

        if label and len(label) < 40:
            buttons.append(label)

    return sorted(list(set(buttons)))

# corrected till UI with page but only one page is coming 
# def parse_component(path: Path, root: Path) -> Dict[str, Any]:
#     try:
#         text = path.read_text(encoding="utf-8", errors="ignore")
#     except Exception:
#         return None

#     name = path.stem

#     rel = path.relative_to(root).as_posix().lower()
#     file_base = path.stem.lower()

#     has_form_tag = "<form" in text.lower() or bool(FORM_INPUT_RE.search(text))
#     has_empty_form = bool(EMPTY_FORM_RE.search(text))
#     has_table = bool(TABLE_RE.search(text))
#     has_real_table = has_table and bool(TABLE_HEADER_RE.search(text))
#     has_map_render = bool(MAP_RENDER_RE.search(text))
#     has_recharts = bool(RECHARTS_RE.search(text)) or bool(CHART_TAG_RE.search(text))

#     charts = []

#     if "LineChart" in text:
#         charts.append("line")

#     if "BarChart" in text:
#         charts.append("bar")

#     if "PieChart" in text:
#         charts.append("pie")

#     if "AreaChart" in text:
#         charts.append("area")

#     has_stat_cards = "<statcard" in text.lower() or "stat-card" in text.lower()

#     fields = extract_field_names(text) if (has_form_tag or has_empty_form) else []
#     defaults = extract_field_defaults(text) if has_empty_form else {}
#     classnames = extract_classnames(text)

#     buttons = extract_buttons(text)
#     table_columns = extract_table_columns(text)

#     # Classification
#     page_type = None

#     if file_base.startswith("dashboard") or file_base.endswith("dashboard"):
#         page_type = "dashboard"

#     elif file_base.startswith("report") or file_base.endswith("report") or file_base.endswith("reports"):
#         page_type = "report"

#     elif has_recharts and has_stat_cards:
#         page_type = "dashboard"

#     elif has_empty_form and (has_table or has_map_render):
#         page_type = "form"

#     elif has_empty_form or (has_form_tag and fields):
#         page_type = "form"

#     elif has_real_table or has_map_render:
#         page_type = "report"

#     else:
#         return None

#     return {
#         "name": name,
#         "file": str(path.relative_to(root)),
#         "type": page_type,
#         "fields": fields,
#         "defaults": defaults,
#         "classnames": classnames[:20],
#         "has_chart": has_recharts,
#         "has_table": has_table or has_map_render,
#         "buttons": buttons,
#         "charts": charts,
#         "table_columns": table_columns,
#     }

def parse_component(path: Path, root: Path) -> Dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    name = path.stem
    file_base = path.stem.lower()

    has_form_tag = "<form" in text.lower()
    has_empty_form = bool(EMPTY_FORM_RE.search(text)) or "useState" in text
    has_table = bool(TABLE_RE.search(text)) or ".map(" in text
    has_recharts = bool(RECHARTS_RE.search(text)) or bool(CHART_TAG_RE.search(text))

    fields = extract_field_names(text)
    defaults = extract_field_defaults(text)
    classnames = extract_classnames(text)
    buttons = extract_buttons(text)
    table_columns = extract_table_columns(text)

    # Strong filename-based detection
    if file_base == "dashboard" or file_base.endswith("dashboard"):
        page_type = "dashboard"

    elif file_base.startswith("report"):
        page_type = "report"

    elif has_form_tag or has_empty_form or file_base in (
        "customers",
        "orders",
        "purchaseorders",
        "salesorders",
        "purchase_orders",
        "sales_orders"
    ):
        page_type = "form"

    elif has_table:
        page_type = "report"

    else:
        return None

    return {
        "name": name,
        "file": str(path.relative_to(root)),
        "type": page_type,
        "fields": fields,
        "defaults": defaults,
        "classnames": classnames[:50],
        "has_chart": has_recharts,
        "has_table": has_table,
        "buttons": buttons,
        "charts": [],
        "table_columns": table_columns,
    }

def parse_project(root: Path) -> Dict[str, Any]:
    all_files = list_source_files(root)

    # Prefer files under a "pages" or "views" or "screens" directory if one
    # exists — those are the real navigable pages. Otherwise fall back to all.
    page_dirs = ("pages", "views", "screens", "routes")
    scoped = [f for f in all_files
              if any(part.lower() in page_dirs for part in f.relative_to(root).parts)]
    target_files = scoped if scoped else all_files

    components = []
    seen_names = set()
    for f in target_files:
        comp = parse_component(f, root)
        if comp and comp["name"] not in seen_names:
            components.append(comp)
            seen_names.add(comp["name"])

    css_compiled = find_compiled_css(root)
    # Fallback: read App.css / index.css as raw if no build
    if not css_compiled:
        raw_parts = []
        for css_path in root.rglob("*.css"):
            if any(part in SKIP_DIRS for part in css_path.relative_to(root).parts):
                continue
            try:
                content = css_path.read_text(encoding="utf-8", errors="ignore")
                # Skip tailwind directive-only files
                if not re.match(r"^\s*@tailwind", content):
                    raw_parts.append(content)
            except Exception:
                pass
        css_compiled = "\n".join(raw_parts)

        print("Detected components:")
    for c in components:
        print(c["name"], c["type"], c["file"])

    return {
        "components": components,
        "css": css_compiled,
        "file_count": len(all_files),
    }
