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
FORM_INPUT_VALUE_RE = re.compile(
    r"value\s*=\s*\{[^}]*?\.([a-zA-Z0-9_]+)\s*\}"
)
USE_STATE_OBJ_RE = re.compile(
    r"useState\s*\(\s*\{([^}]+)\}\s*\)", re.MULTILINE | re.DOTALL
)
EMPTY_FORM_RE = re.compile(
    r"(?:emptyForm|formData|initialForm|defaultValues)\s*=\s*\{([^}]+)\}",
    re.MULTILINE | re.DOTALL,
)
KEY_NAME_RE = re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*:")
CLASSNAME_RE = re.compile(r'className\s*=\s*["\']([^"\']+)["\']')
COMPONENT_NAME_RE = re.compile(
    r"(?:export\s+default\s+(?:function|const)|function|const)\s+([A-Z][A-Za-z0-9_]+)"
)
TABLE_RE = re.compile(r"<table\b", re.IGNORECASE)
MAP_RENDER_RE = re.compile(r"\.map\s*\(\s*\(?\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\)?\s*=>\s*[\(\<]")
RECHARTS_RE = re.compile(r"from\s+['\"]recharts['\"]")
CHART_TAG_RE = re.compile(r"<(LineChart|BarChart|PieChart|AreaChart|RadarChart)\b")
STAT_CARD_RE = re.compile(r"\b(stat|statistic|metric|kpi)s?\b", re.IGNORECASE)


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


def parse_component(path: Path, root: Path) -> Dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    name_match = COMPONENT_NAME_RE.search(text)
    name = name_match.group(1) if name_match else path.stem

    has_form_tag = "<form" in text.lower() or bool(FORM_INPUT_RE.search(text))
    has_table = bool(TABLE_RE.search(text))
    has_map_render = bool(MAP_RENDER_RE.search(text))
    has_recharts = bool(RECHARTS_RE.search(text)) or bool(CHART_TAG_RE.search(text))
    has_stat_cards = bool(STAT_CARD_RE.search(text))

    fields = extract_field_names(text) if has_form_tag else []
    classnames = extract_classnames(text)

    page_type = None
    if has_recharts or (has_stat_cards and "card" in text.lower()):
        page_type = "dashboard"
    elif has_form_tag and fields:
        page_type = "form"
    elif has_table or has_map_render:
        page_type = "report"
    else:
        return None  # Skip non-page components

    return {
        "name": name,
        "file": str(path.relative_to(root)),
        "type": page_type,
        "fields": fields,
        "classnames": classnames[:20],
        "has_chart": has_recharts,
    }


def parse_project(root: Path) -> Dict[str, Any]:
    files = list_source_files(root)
    components = []
    seen_names = set()
    for f in files:
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

    return {
        "components": components,
        "css": css_compiled,
        "file_count": len(files),
    }
