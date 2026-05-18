"""APEX SQL generator - emits apex_application PL/SQL helper calls."""
import time
import re
from typing import Dict, List, Any


def _sanitize(value: str) -> str:
    return (value or "").replace("'", "''")


def _label(name: str) -> str:
    """Convert camelCase / snake_case to Title Case."""
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", name or "")
    s = s.replace("_", " ").replace("-", " ")
    return " ".join(w.capitalize() for w in s.split())


def _item_type(field: str) -> str:
    f = field.lower()
    if any(k in f for k in ("email",)):
        return "NATIVE_EMAIL"
    if any(k in f for k in ("password", "secret")):
        return "NATIVE_PASSWORD"
    if any(k in f for k in ("date", "dob", "birth")):
        return "NATIVE_DATE_PICKER_APEX"
    if any(k in f for k in ("description", "comment", "notes", "message", "body")):
        return "NATIVE_TEXTAREA"
    if any(k in f for k in ("amount", "price", "qty", "quantity", "count", "age", "number")):
        return "NATIVE_NUMBER_FIELD"
    return "NATIVE_TEXT_FIELD"


class IdAllocator:
    def __init__(self):
        self._cur = int(time.time())

    def next(self) -> int:
        self._cur += 1
        return self._cur


def _floating_label_supported(version: str) -> bool:
    """floatingLabel template option is available 22.2+."""
    try:
        major = float(version)
        return major >= 22.2
    except ValueError:
        return True


def _version_header(version: str) -> str:
    """Comments documenting which APEX version syntax is targeted."""
    return f"-- Target APEX Version: {version}\n"


def generate_page_form(ids: IdAllocator, page_id: int, comp: Dict[str, Any], version: str) -> str:
    name = comp["name"]
    fields = comp["fields"] or ["name", "email"]
    css_classes = " ".join(comp.get("classnames", [])[:5])
    region_id = ids.next()
    out = []

    item_template = (
        "'#DEFAULT#:t-Form-fieldContainer--floatingLabel'"
        if _floating_label_supported(version)
        else "'#DEFAULT#'"
    )

    out.append(f"-- Page {page_id}: Form - {name}")
    out.append("apex_application.create_page(")
    out.append(f"  p_id => {page_id},")
    out.append(f"  p_name => '{_sanitize(_label(name))}',")
    out.append(f"  p_step_title => '{_sanitize(_label(name))}',")
    out.append("  p_page_mode => 'NORMAL',")
    out.append("  p_step_template => 'STANDARD',")
    out.append(f"  p_page_css_classes => '{_sanitize(css_classes)}',")
    out.append("  p_autocomplete_on_off => 'OFF');")
    out.append("")

    # Form region
    out.append("apex_application.create_page_plug(")
    out.append(f"  p_id => {region_id},")
    out.append("  p_plug_name => 'Form',")
    out.append("  p_region_template_options => '#DEFAULT#',")
    out.append("  p_plug_template => 'STANDARD',")
    out.append("  p_plug_display_sequence => 10,")
    out.append("  p_plug_source_type => 'NATIVE_FORM',")
    out.append(f"  p_plug_css_classes => '{_sanitize(css_classes)}');")
    out.append("")

    # Items
    seq = 10
    for field in fields[:30]:
        item_id = ids.next()
        out.append("apex_application.create_page_item(")
        out.append(f"  p_id => {item_id},")
        out.append(f"  p_name => 'P{page_id}_{field.upper()}',")
        out.append(f"  p_item_sequence => {seq},")
        out.append(f"  p_item_plug_id => {region_id},")
        out.append(f"  p_prompt => '{_sanitize(_label(field))}',")
        out.append(f"  p_display_as => '{_item_type(field)}',")
        out.append(f"  p_item_template_options => {item_template});")
        out.append("")
        seq += 10

    # Buttons (top-right EDIT region position)
    save_btn = ids.next()
    cancel_btn = ids.next()
    out.append("apex_application.create_page_button(")
    out.append(f"  p_id => {save_btn},")
    out.append(f"  p_button_sequence => 10,")
    out.append(f"  p_button_plug_id => {region_id},")
    out.append(f"  p_button_name => 'SAVE',")
    out.append(f"  p_button_action => 'SUBMIT',")
    out.append(f"  p_button_template_options => '#DEFAULT#:t-Button--iconRight',")
    out.append(f"  p_button_template_id => 'HOT',")
    out.append(f"  p_button_position => 'EDIT',")
    out.append(f"  p_button_image_alt => 'Save');")
    out.append("")
    out.append("apex_application.create_page_button(")
    out.append(f"  p_id => {cancel_btn},")
    out.append(f"  p_button_sequence => 20,")
    out.append(f"  p_button_plug_id => {region_id},")
    out.append(f"  p_button_name => 'CANCEL',")
    out.append(f"  p_button_action => 'REDIRECT_PAGE',")
    out.append(f"  p_button_position => 'EDIT',")
    out.append(f"  p_button_image_alt => 'Cancel');")
    out.append("")

    # Process
    proc_id = ids.next()
    out.append("apex_application.create_page_process(")
    out.append(f"  p_id => {proc_id},")
    out.append(f"  p_process_sequence => 10,")
    out.append(f"  p_process_point => 'AFTER_SUBMIT',")
    out.append(f"  p_process_type => 'NATIVE_FORM_DML',")
    out.append(f"  p_process_name => 'Process Form {_label(name)}',")
    out.append(f"  p_process_when_button_id => {save_btn});")
    out.append("")
    return "\n".join(out)


def generate_page_report(ids: IdAllocator, page_id: int, comp: Dict[str, Any]) -> str:
    name = comp["name"]
    region_id = ids.next()
    css_classes = " ".join(comp.get("classnames", [])[:5])
    out = []
    out.append(f"-- Page {page_id}: Interactive Report - {name}")
    out.append("apex_application.create_page(")
    out.append(f"  p_id => {page_id},")
    out.append(f"  p_name => '{_sanitize(_label(name))}',")
    out.append(f"  p_step_title => '{_sanitize(_label(name))}',")
    out.append("  p_page_mode => 'NORMAL',")
    out.append("  p_step_template => 'STANDARD',")
    out.append(f"  p_page_css_classes => '{_sanitize(css_classes)}');")
    out.append("")

    out.append("apex_application.create_page_plug(")
    out.append(f"  p_id => {region_id},")
    out.append(f"  p_plug_name => '{_sanitize(_label(name))} Report',")
    out.append("  p_region_template_options => '#DEFAULT#',")
    out.append("  p_plug_template => 'STANDARD',")
    out.append("  p_plug_display_sequence => 10,")
    out.append("  p_plug_source_type => 'NATIVE_IR',")
    out.append("  p_plug_source => 'select rownum as id, ''Sample Row '' || rownum as label, sysdate as created_at from dual connect by level <= 25',")
    out.append(f"  p_plug_css_classes => '{_sanitize(css_classes)}');")
    out.append("")
    return "\n".join(out)


def generate_page_dashboard(ids: IdAllocator, page_id: int, comp: Dict[str, Any]) -> str:
    name = comp["name"]
    css_classes = " ".join(comp.get("classnames", [])[:5])
    out = []
    out.append(f"-- Page {page_id}: Dashboard - {name}")
    out.append("apex_application.create_page(")
    out.append(f"  p_id => {page_id},")
    out.append(f"  p_name => '{_sanitize(_label(name))}',")
    out.append(f"  p_step_title => '{_sanitize(_label(name))}',")
    out.append("  p_page_mode => 'NORMAL',")
    out.append("  p_step_template => 'STANDARD',")
    out.append(f"  p_page_css_classes => '{_sanitize(css_classes)}');")
    out.append("")

    # Stat cards row
    for i, metric in enumerate(("Total", "Active", "Pending", "Completed"), start=1):
        rid = ids.next()
        out.append("apex_application.create_page_plug(")
        out.append(f"  p_id => {rid},")
        out.append(f"  p_plug_name => '{metric}',")
        out.append("  p_region_template_options => '#DEFAULT#:t-Region--scrollBody',")
        out.append("  p_plug_template => 'BLANK_WITH_ATTRIBUTES',")
        out.append(f"  p_plug_display_sequence => {i * 10},")
        out.append("  p_plug_display_column => " + str(((i - 1) % 4) + 1) + ",")
        out.append("  p_plug_source_type => 'NATIVE_HTML',")
        out.append(f"  p_plug_source => '<div class=\"stat-card\"><h3>{metric}</h3><p class=\"stat-value\">{i * 124}</p></div>');")
        out.append("")

    # Chart region
    chart_id = ids.next()
    out.append("apex_application.create_page_plug(")
    out.append(f"  p_id => {chart_id},")
    out.append("  p_plug_name => 'Trend Chart',")
    out.append("  p_region_template_options => '#DEFAULT#',")
    out.append("  p_plug_template => 'STANDARD',")
    out.append("  p_plug_display_sequence => 100,")
    out.append("  p_plug_source_type => 'NATIVE_JET_CHART',")
    out.append(f"  p_plug_css_classes => '{_sanitize(css_classes)}');")
    out.append("")
    return "\n".join(out)


def generate_css_static_file(css_content: str, app_id: int) -> str:
    """Generate wwv_flow_imp_shared.create_app_static_file call."""
    # Limit content to safe size
    safe_css = css_content[:200_000] if css_content else "/* react theme placeholder */"
    # Escape single quotes
    safe_css = safe_css.replace("'", "''")
    # Build the SQL with q-quoted string for safety
    out = []
    out.append("-- React theme static application file")
    out.append("declare")
    out.append("  l_clob clob;")
    out.append("begin")
    out.append("  l_clob := q'[")
    out.append(safe_css.replace("]'", "] '"))
    out.append("  ]';")
    out.append("  wwv_flow_imp_shared.create_app_static_file(")
    out.append(f"    p_flow_id => {app_id},")
    out.append("    p_file_name => 'react_theme.css',")
    out.append("    p_mime_type => 'text/css',")
    out.append("    p_file_charset => 'utf-8',")
    out.append("    p_file_content => utl_raw.cast_to_raw(l_clob));")
    out.append("end;")
    out.append("/")
    return "\n".join(out)


def generate_sql(parsed: Dict[str, Any], workspace: str, app_id: int, version: str) -> Dict[str, Any]:
    ids = IdAllocator()
    blocks = []
    blocks.append(_version_header(version))
    blocks.append("-- ============================================================")
    blocks.append("-- React → Oracle APEX SQL Migration Script")
    blocks.append(f"-- Workspace: {workspace}")
    blocks.append(f"-- Application ID: {app_id}")
    blocks.append(f"-- Detected components: {len(parsed['components'])}")
    blocks.append("-- ============================================================")
    blocks.append("")
    blocks.append("begin")
    blocks.append("  apex_util.set_security_group_id(")
    blocks.append(f"    apex_util.find_security_group_id('{_sanitize(workspace)}')")
    blocks.append("  );")
    blocks.append(f"  apex_application.g_flow_id := {app_id};")
    blocks.append("end;")
    blocks.append("/")
    blocks.append("")

    page_summary: List[Dict[str, Any]] = []
    page_seq = 100
    for comp in parsed["components"][:40]:
        page_seq += 1
        blocks.append("begin")
        if comp["type"] == "form":
            blocks.append(generate_page_form(ids, page_seq, comp, version))
        elif comp["type"] == "report":
            blocks.append(generate_page_report(ids, page_seq, comp))
        elif comp["type"] == "dashboard":
            blocks.append(generate_page_dashboard(ids, page_seq, comp))
        blocks.append("commit;")
        blocks.append("end;")
        blocks.append("/")
        blocks.append("")
        page_summary.append({
            "page_id": page_seq,
            "name": comp["name"],
            "type": comp["type"],
            "fields": len(comp.get("fields", [])),
        })

    # CSS static file
    blocks.append("-- ============================================================")
    blocks.append("-- Static Application File: react_theme.css")
    blocks.append("-- ============================================================")
    blocks.append(generate_css_static_file(parsed.get("css", ""), app_id))

    sql = "\n".join(blocks)
    return {"sql": sql, "pages": page_summary, "component_count": len(parsed["components"])}
