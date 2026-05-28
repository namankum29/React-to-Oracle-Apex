"""Universal React project parser - detects pages, forms, reports, dashboards, fields, buttons and table columns."""
import re
import zipfile
from pathlib import Path
from typing import Dict, List, Any


JSX_EXT = {".jsx", ".tsx", ".js", ".ts"}
SKIP_DIRS = {"node_modules", "dist", "build", ".git", ".next", "coverage", "out"}


def extract_zip(zip_path: Path, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(dest)

    for p in dest.rglob("package.json"):
        if not any(part in SKIP_DIRS for part in p.parts):
            return p.parent

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
    combined = []

    for sub in ("dist/assets", "build/static/css", "dist", "build"):
        d = root / sub
        if d.exists():
            for css in d.rglob("*.css"):
                try:
                    combined.append(css.read_text(encoding="utf-8", errors="ignore"))
                except Exception:
                    pass

    if combined:
        return "\n".join(combined)

    raw_parts = []
    for css_path in root.rglob("*.css"):
        if any(part in SKIP_DIRS for part in css_path.relative_to(root).parts):
            continue
        try:
            content = css_path.read_text(encoding="utf-8", errors="ignore")
            if not re.match(r"^\s*@tailwind", content):
                raw_parts.append(content)
        except Exception:
            pass

    return "\n".join(raw_parts)


def clean_text(value: str) -> str:
    value = re.sub(r"<.*?>", "", value or "")
    value = re.sub(r"\{.*?\}", "", value)
    value = value.replace("&amp;", "&")
    return " ".join(value.split()).strip()


def labelize(name: str) -> str:
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name or "")
    name = name.replace("_", " ").replace("-", " ")
    return " ".join(w.capitalize() for w in name.split())


def normalize_field(name: str) -> str:
    name = name.strip()
    name = re.sub(r"[^A-Za-z0-9_]", "_", name)
    return name


BLACKLIST = {
    "const", "let", "var", "true", "false", "null", "undefined",
    "length", "map", "filter", "reduce", "find", "includes",
    "target", "value", "label", "option", "index", "item",
    "data", "prev", "next", "state", "props", "children",
    "className", "onClick", "onChange", "type", "id"
}


INPUT_TAG_RE = re.compile(r"<(input|textarea|select)\b([^>]*)>", re.IGNORECASE | re.DOTALL)
ATTR_RE = re.compile(r"([a-zA-Z_:][-a-zA-Z0-9_:]*)\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|\{([^}]*)\})")
EMPTY_OBJECT_RE = re.compile(
    r"(?:emptyForm|formData|initialForm|defaultValues|initialState|emptyValues|emptyState|empty[A-Z]\w*)"
    r"(?:\s*:\s*[A-Za-z_][A-Za-z0-9_<>\[\],\s]*)?"
    r"\s*=\s*\{([^}]+)\}",
    re.MULTILINE | re.DOTALL,
)
USE_STATE_OBJ_RE = re.compile(r"useState\s*\(\s*\{([^}]+)\}\s*\)", re.MULTILINE | re.DOTALL)
KEY_VALUE_RE = re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*([^,\n}]+)")
CONTROLLED_VALUE_RE = re.compile(r"value\s*=\s*\{[^}]*?\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\}")
ONCHANGE_FIELD_RE = re.compile(r"(?:name|id)\s*:\s*['\"]([a-zA-Z_][a-zA-Z0-9_]*)['\"]")
USESTATE_SINGLE_RE = re.compile(
    r"const\s*\[\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*,\s*set[A-Z][A-Za-z0-9_]*\s*\]\s*=\s*useState\s*\(",
    re.MULTILINE,
)
CLASSNAME_RE = re.compile(r'className\s*=\s*["\']([^"\']+)["\']')
BUTTON_RE = re.compile(r"<button\b([^>]*)>(.*?)</button>", re.IGNORECASE | re.DOTALL)
TH_TEXT_RE = re.compile(r"<th[^>]*>(.*?)</th>", re.IGNORECASE | re.DOTALL)
TABLE_RE = re.compile(r"<table\b", re.IGNORECASE)
MAP_RENDER_RE = re.compile(r"\.map\s*\(", re.IGNORECASE)
RECHARTS_RE = re.compile(r"from\s+['\"]recharts['\"]")
CHART_TAG_RE = re.compile(r"<(LineChart|BarChart|PieChart|AreaChart|RadarChart)\b")
CARD_KEYWORDS_RE = re.compile(r"\b(card|stat|metric|kpi|summary)\b", re.IGNORECASE)
TITLE_RE = re.compile(r"<h[1-3][^>]*>(.*?)</h[1-3]>", re.IGNORECASE | re.DOTALL)


def parse_attrs(attr_text: str) -> Dict[str, str]:
    attrs = {}
    for m in ATTR_RE.finditer(attr_text or ""):
        key = m.group(1)
        val = m.group(2) or m.group(3) or m.group(4) or ""
        attrs[key] = val.strip()
    return attrs


def guess_field_type(field_name: str, tag: str = "input", attrs: Dict[str, str] = None) -> str:
    attrs = attrs or {}
    f = field_name.lower()
    html_type = (attrs.get("type") or "").lower()

    if tag.lower() == "select":
        return "select"
    if tag.lower() == "textarea":
        return "textarea"
    if html_type in ("number", "email", "password", "date", "datetime-local", "tel"):
        return html_type
    if any(k in f for k in ("amount", "price", "qty", "quantity", "total", "rate", "count", "age")):
        return "number"
    if any(k in f for k in ("date", "dob", "birth", "time")):
        return "date"
    if "email" in f:
        return "email"
    if any(k in f for k in ("password", "secret")):
        return "password"
    if any(k in f for k in ("description", "comment", "notes", "message", "body", "address")):
        return "textarea"
    if "status" in f or "type" in f or "category" in f:
        return "select"
    return "text"


def add_field(fields_map: Dict[str, Dict[str, Any]], name: str, label: str = None, field_type: str = None, default: str = ""):
    name = normalize_field(name)
    if not name or name.lower() in BLACKLIST or len(name) > 40:
        return

    existing = fields_map.get(name)
    if existing:
        if label and not existing.get("label"):
            existing["label"] = label
        if field_type and existing.get("type") == "text":
            existing["type"] = field_type
        return

    fields_map[name] = {
        "name": name,
        "label": label or labelize(name),
        "type": field_type or guess_field_type(name),
        "default": default or "",
        "required": any(k in name.lower() for k in ("name", "email", "code", "no", "title")),
    }


def extract_fields(text: str) -> List[Dict[str, Any]]:
    fields_map: Dict[str, Dict[str, Any]] = {}

    for m in INPUT_TAG_RE.finditer(text):
        tag = m.group(1)
        attrs = parse_attrs(m.group(2))
        name = attrs.get("name") or attrs.get("id")
        if not name:
            value_expr = attrs.get("value") or ""
            vm = re.search(r"\.([a-zA-Z_][a-zA-Z0-9_]*)", value_expr)
            name = vm.group(1) if vm else None

        if name:
            label = attrs.get("aria-label") or attrs.get("placeholder") or labelize(name)
            add_field(fields_map, name, label, guess_field_type(name, tag, attrs))

    for regex in (EMPTY_OBJECT_RE, USE_STATE_OBJ_RE):
        for m in regex.finditer(text):
            body = m.group(1)
            for km in KEY_VALUE_RE.finditer(body):
                key = km.group(1)
                val = km.group(2).strip().strip("'\"")
                add_field(fields_map, key, labelize(key), guess_field_type(key), val)

    for m in CONTROLLED_VALUE_RE.finditer(text):
        add_field(fields_map, m.group(1))

    for m in USESTATE_SINGLE_RE.finditer(text):
        field = m.group(1)
        if field.lower() not in ("loading", "error", "search", "searchterm", "sortby", "filter"):
            add_field(fields_map, field)

    return list(fields_map.values())


def extract_field_names(text: str) -> List[str]:
    return [f["name"] for f in extract_fields(text)]


def extract_field_defaults(text: str) -> Dict[str, str]:
    return {f["name"]: f.get("default", "") for f in extract_fields(text) if f.get("default")}


def extract_classnames(text: str) -> List[str]:
    classes = set()
    for m in CLASSNAME_RE.finditer(text):
        for cls in m.group(1).split():
            if len(cls) < 80:
                classes.add(cls)
    return sorted(classes)


def extract_buttons(text: str) -> List[Dict[str, Any]]:
    buttons = []

    for m in BUTTON_RE.finditer(text):
        attrs = parse_attrs(m.group(1))
        label = clean_text(m.group(2))

        if not label or len(label) > 60:
            continue

        low = label.lower()
        action = "button"

        if any(k in low for k in ("create", "add", "new")):
            action = "open_modal"
        elif any(k in low for k in ("save", "submit")):
            action = "submit"
        elif "cancel" in low:
            action = "cancel"
        elif any(k in low for k in ("edit", "view")):
            action = "navigate"

        buttons.append({
            "label": label,
            "name": re.sub(r"[^A-Za-z0-9]+", "_", label).upper().strip("_"),
            "action": action,
            "classes": attrs.get("className", ""),
        })

    return buttons


def extract_table_columns(text: str) -> List[Dict[str, str]]:
    cols = []

    for m in TH_TEXT_RE.finditer(text):
        label = clean_text(m.group(1))
        if label and len(label) < 60:
            name = re.sub(r"[^A-Za-z0-9]+", "_", label).upper().strip("_")
            if name and name.lower() not in BLACKLIST:
                cols.append({"name": name, "label": label})

    seen = set()
    out = []
    for c in cols:
        if c["name"] not in seen:
            out.append(c)
            seen.add(c["name"])

    return out


def extract_title(text: str, fallback: str) -> str:
    m = TITLE_RE.search(text)
    if m:
        title = clean_text(m.group(1))
        if title and len(title) < 80:
            return title
    return labelize(fallback)


def detect_charts(text: str) -> List[str]:
    charts = []
    for chart in ("LineChart", "BarChart", "PieChart", "AreaChart", "RadarChart"):
        if chart in text:
            charts.append(chart.replace("Chart", "").lower())
    return charts


def parse_component(path: Path, root: Path) -> Dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    name = path.stem
    file_base = path.stem.lower()

    fields_meta = extract_fields(text)
    fields = [f["name"] for f in fields_meta]
    buttons = extract_buttons(text)
    table_columns = extract_table_columns(text)
    classnames = extract_classnames(text)
    charts = detect_charts(text)

    has_table = bool(TABLE_RE.search(text)) or bool(MAP_RENDER_RE.search(text))
    has_chart = bool(RECHARTS_RE.search(text)) or bool(CHART_TAG_RE.search(text)) or bool(charts)
    has_cards = bool(CARD_KEYWORDS_RE.search(text)) or any("card" in c.lower() for c in classnames)

    create_buttons = [b for b in buttons if b["action"] == "open_modal"]

    if file_base == "dashboard" or file_base.endswith("dashboard") or (has_chart and has_cards):
        page_type = "dashboard"
    elif file_base.startswith("report") or (has_table and not create_buttons and not fields_meta):
        page_type = "report"
    elif create_buttons or fields_meta:
        page_type = "form"
    elif has_table:
        page_type = "report"
    else:
        return None

    return {
        "name": name,
        "title": extract_title(text, name),
        "file": str(path.relative_to(root)),
        "type": page_type,
        "fields": fields,
        "fields_meta": fields_meta,
        "defaults": extract_field_defaults(text),
        "classnames": classnames[:80],
        "buttons": buttons,
        "create_buttons": create_buttons,
        "has_chart": has_chart,
        "has_cards": has_cards,
        "has_table": has_table,
        "charts": charts,
        "table_columns": table_columns,
        "layout": {
            "has_create_modal": bool(create_buttons),
            "has_table": has_table,
            "has_dashboard_cards": has_cards,
        },
    }


def parse_project(root: Path) -> Dict[str, Any]:
    all_files = list_source_files(root)

    page_dirs = ("pages", "views", "screens", "routes")
    scoped = [
        f for f in all_files
        if any(part.lower() in page_dirs for part in f.relative_to(root).parts)
    ]

    target_files = scoped if scoped else all_files

    components = []
    seen = set()

    for f in target_files:
        comp = parse_component(f, root)
        if comp and comp["name"] not in seen:
            components.append(comp)
            seen.add(comp["name"])

    css_compiled = find_compiled_css(root)

    print("Detected components:")
    for c in components:
        print(
            c["name"],
            c["type"],
            c["file"],
            "fields:",
            c.get("fields"),
            "columns:",
            c.get("table_columns"),
            "buttons:",
            [b["label"] for b in c.get("buttons", [])],
        )

    return {
        "components": components,
        "css": css_compiled,
        "file_count": len(all_files),
    }