"""APEX SQL generator - emits wwv_flow_imp_page.* PL/SQL via import_begin/import_end.

The internal `apex_application.create_*` procedures are NOT publicly callable in
APEX 22.2+. The real APEX export format uses the wwv_flow_imp_* family wrapped
in an import context, which is what we emit here.

Region source types used:
  NATIVE_HTML       — static HTML containers (form region, dashboard cards)
  NATIVE_SQL_REPORT — Classic Reports (reports & dashboard trend table)

We deliberately avoid:
  NATIVE_IR         — needs accompanying create_worksheet/_column/_rpt records
  NATIVE_JET_CHART  — needs create_jet_chart_attributes/_series records
  p_plug_template   — referencing a template id without first creating it
                       produces a dangling reference (ORA-01403 at render);
                       omitting lets APEX fall back to the application's
                       default Universal Theme region template.
"""
import re
import time
from typing import Dict, List, Any


def _sanitize(value: str) -> str:
    return (value or "").replace("'", "''")


def _label(name: str) -> str:
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", name or "")
    s = s.replace("_", " ").replace("-", " ")
    return " ".join(w.capitalize() for w in s.split())


def _item_type(field: str) -> str:
    f = field.lower()
    if "email" in f:
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


APEX_VERSION_META = {
    "22.2": ("22.2.0", "2022.10.07"),
    "23.1": ("23.1.0", "2023.04.18"),
    "23.2": ("23.2.0", "2023.10.31"),
    "24.1": ("24.1.0", "2024.05.22"),
    "24.2": ("24.2.0", "2024.11.05"),
    "26.1": ("26.1.0", "2026.04.30"),
}


def _release(version: str):
    return APEX_VERSION_META.get(version, APEX_VERSION_META["24.2"])


def _floating_label_supported(version: str) -> bool:
    try:
        return float(version) >= 22.2
    except ValueError:
        return True


def _emit_import_begin(workspace: str, app_id: int, version: str) -> str:
    release, date = _release(version)
    return (
        "wwv_flow_imp.import_begin(\n"
        f"  p_version_yyyy_mm_dd => '{date}',\n"
        f"  p_release => '{release}',\n"
        f"  p_default_workspace_id => apex_util.find_security_group_id('{_sanitize(workspace)}'),\n"
        f"  p_default_application_id => {app_id},\n"
        "  p_default_id_offset => 0,\n"
        f"  p_default_owner => '{_sanitize(workspace)}');\n"
    )


def _emit_import_end() -> str:
    return (
        "wwv_flow_imp.import_end(\n"
        "  p_auto_install_sup_obj => nvl(wwv_flow_application_install.get_auto_install_sup_obj, false));\n"
        "commit;\n"
    )


def generate_page_form(ids: IdAllocator, page_id: int, comp: Dict[str, Any], version: str) -> str:
    name = comp["name"]
    fields = comp["fields"] or ["name", "email"]
    region_id = ids.next()
    list_region_id = ids.next() if comp.get("has_table") else None
    out = []

    item_template = (
        "'#DEFAULT#:t-Form-fieldContainer--floatingLabel'"
        if _floating_label_supported(version)
        else "'#DEFAULT#'"
    )

    out.append(f"-- Page {page_id}: Form - {name}")
    out.append("wwv_flow_imp_page.create_page(")
    out.append(f"  p_id => {page_id},")
    out.append(f"  p_name => '{_sanitize(_label(name))}',")
    out.append(f"  p_step_title => '{_sanitize(_label(name))}',")
    out.append("  p_autocomplete_on_off => 'OFF',")
    out.append("  p_page_template_options => '#DEFAULT#');")
    out.append("")

    # Form region (Static HTML container — always renders without sub-records)
    out.append("wwv_flow_imp_page.create_page_plug(")
    out.append(f"  p_id => {region_id},")
    out.append(f"  p_plug_name => '{_sanitize(_label(name))} Form',")
    out.append("  p_region_template_options => '#DEFAULT#',")
    out.append("  p_plug_display_sequence => 10,")
    out.append("  p_plug_display_point => 'BODY',")
    out.append("  p_plug_source_type => 'NATIVE_HTML',")
    out.append("  p_plug_source => '<!-- Form region for " + _sanitize(_label(name)) + " -->');")
    out.append("")

    seq = 10
    for field in fields[:30]:
        item_id = ids.next()
        out.append("wwv_flow_imp_page.create_page_item(")
        out.append(f"  p_id => {item_id},")
        out.append(f"  p_name => 'P{page_id}_{field.upper()}',")
        out.append(f"  p_item_sequence => {seq},")
        out.append(f"  p_item_plug_id => {region_id},")
        out.append(f"  p_prompt => '{_sanitize(_label(field))}',")
        out.append(f"  p_display_as => '{_item_type(field)}',")
        out.append(f"  p_item_template_options => {item_template});")
        out.append("")
        seq += 10

    save_btn = ids.next()
    cancel_btn = ids.next()
    out.append("wwv_flow_imp_page.create_page_button(")
    out.append(f"  p_id => {save_btn},")
    out.append("  p_button_sequence => 10,")
    out.append(f"  p_button_plug_id => {region_id},")
    out.append("  p_button_name => 'SAVE',")
    out.append("  p_button_action => 'SUBMIT',")
    out.append("  p_button_template_options => '#DEFAULT#:t-Button--iconRight',")
    out.append("  p_button_position => 'EDIT',")
    out.append("  p_button_image_alt => 'Save');")
    out.append("")
    out.append("wwv_flow_imp_page.create_page_button(")
    out.append(f"  p_id => {cancel_btn},")
    out.append("  p_button_sequence => 20,")
    out.append(f"  p_button_plug_id => {region_id},")
    out.append("  p_button_name => 'CANCEL',")
    out.append("  p_button_action => 'REDIRECT_PAGE',")
    out.append("  p_button_position => 'EDIT',")
    out.append("  p_button_image_alt => 'Cancel');")
    out.append("")

    proc_id = ids.next()
    out.append("wwv_flow_imp_page.create_page_process(")
    out.append(f"  p_id => {proc_id},")
    out.append("  p_process_sequence => 10,")
    out.append("  p_process_point => 'AFTER_SUBMIT',")
    out.append("  p_process_type => 'NATIVE_PLSQL',")
    out.append(f"  p_process_name => 'Process Form {_label(name)}',")
    out.append("  p_process_sql_clob => 'begin null; end;',")
    out.append(f"  p_process_when_button_id => {save_btn});")
    out.append("")

    if list_region_id is not None:
        out.append("wwv_flow_imp_page.create_page_plug(")
        out.append(f"  p_id => {list_region_id},")
        out.append(f"  p_plug_name => '{_sanitize(_label(name))} List',")
        out.append("  p_region_template_options => '#DEFAULT#',")
        out.append("  p_plug_display_sequence => 20,")
        out.append("  p_plug_display_point => 'BODY',")
        out.append("  p_query_type => 'SQL',")
        out.append("  p_plug_source_type => 'NATIVE_SQL_REPORT',")
        out.append("  p_plug_source => 'select rownum as id, ''Row '' || rownum as label from dual connect by level <= 10');")
        out.append("")

    return "\n".join(out)


def generate_page_report(ids: IdAllocator, page_id: int, comp: Dict[str, Any]) -> str:
    name = comp["name"]
    region_id = ids.next()
    out = []
    out.append(f"-- Page {page_id}: Report - {name}")
    out.append("wwv_flow_imp_page.create_page(")
    out.append(f"  p_id => {page_id},")
    out.append(f"  p_name => '{_sanitize(_label(name))}',")
    out.append(f"  p_step_title => '{_sanitize(_label(name))}',")
    out.append("  p_autocomplete_on_off => 'OFF',")
    out.append("  p_page_template_options => '#DEFAULT#');")
    out.append("")

    out.append("wwv_flow_imp_page.create_page_plug(")
    out.append(f"  p_id => {region_id},")
    out.append(f"  p_plug_name => '{_sanitize(_label(name))}',")
    out.append("  p_region_template_options => '#DEFAULT#',")
    out.append("  p_plug_display_sequence => 10,")
    out.append("  p_plug_display_point => 'BODY',")
    out.append("  p_query_type => 'SQL',")
    out.append("  p_plug_source_type => 'NATIVE_SQL_REPORT',")
    out.append("  p_plug_source => 'select rownum as id, ''Sample '' || rownum as label, sysdate as created_at from dual connect by level <= 25');")
    out.append("")
    return "\n".join(out)


def generate_page_dashboard(ids: IdAllocator, page_id: int, comp: Dict[str, Any]) -> str:
    name = comp["name"]
    out = []
    out.append(f"-- Page {page_id}: Dashboard - {name}")
    out.append("wwv_flow_imp_page.create_page(")
    out.append(f"  p_id => {page_id},")
    out.append(f"  p_name => '{_sanitize(_label(name))}',")
    out.append(f"  p_step_title => '{_sanitize(_label(name))}',")
    out.append("  p_autocomplete_on_off => 'OFF',")
    out.append("  p_page_template_options => '#DEFAULT#');")
    out.append("")

    for i, metric in enumerate(("Total", "Active", "Pending", "Completed"), start=1):
        rid = ids.next()
        out.append("wwv_flow_imp_page.create_page_plug(")
        out.append(f"  p_id => {rid},")
        out.append(f"  p_plug_name => '{metric}',")
        out.append("  p_region_template_options => '#DEFAULT#',")
        out.append(f"  p_plug_display_sequence => {i * 10},")
        out.append("  p_plug_display_point => 'BODY',")
        out.append("  p_plug_source_type => 'NATIVE_HTML',")
        out.append(f"  p_plug_source => '<div class=\"t-Card t-Card--stat\"><h3>{metric}</h3><p class=\"stat-value\" style=\"font-size:2rem;font-weight:600;\">{i * 124}</p></div>');")
        out.append("")

    trend_id = ids.next()
    out.append("wwv_flow_imp_page.create_page_plug(")
    out.append(f"  p_id => {trend_id},")
    out.append("  p_plug_name => 'Trend',")
    out.append("  p_region_template_options => '#DEFAULT#',")
    out.append("  p_plug_display_sequence => 100,")
    out.append("  p_plug_display_point => 'BODY',")
    out.append("  p_query_type => 'SQL',")
    out.append("  p_plug_source_type => 'NATIVE_SQL_REPORT',")
    out.append("  p_plug_source => 'select to_char(sysdate - level + 1, ''YYYY-MM-DD'') as day, round(dbms_random.value(50, 150)) as value from dual connect by level <= 12');")
    out.append("")
    return "\n".join(out)


# ----- CSS static file helpers -----

def _pick_q_delim(text: str):
    candidates = [("[", "]"), ("{", "}"), ("<", ">"), ("!", "!"), ("#", "#"), ("~", "~")]
    for opn, cls in candidates:
        if f"{cls}'" not in text:
            return opn, cls
    return "#", "#"


def _chunk_css(css: str, max_bytes: int = 16000) -> List[str]:
    if not css:
        return ["/* empty */"]
    chunks = []
    remaining = css
    while remaining:
        if len(remaining.encode("utf-8")) <= max_bytes:
            chunks.append(remaining)
            break
        cut = max_bytes
        slice_ = remaining[:cut]
        while len(slice_.encode("utf-8")) > max_bytes and cut > 0:
            cut -= 128
            slice_ = remaining[:cut]
        nl = slice_.rfind("\n")
        if nl > max_bytes // 2:
            cut = nl + 1
            slice_ = remaining[:cut]
        chunks.append(slice_)
        remaining = remaining[cut:]
    return chunks


def generate_css_block(css_content: str, app_id: int, workspace: str, version: str) -> str:
    css = css_content if css_content else "/* react theme placeholder */"
    chunks = _chunk_css(css, max_bytes=16000)

    out = []
    out.append("declare")
    out.append("  l_blob blob;")
    out.append("  l_raw raw(32767);")
    out.append("begin")
    out.append("  " + _emit_import_begin(workspace, app_id, version).replace("\n", "\n  ").rstrip())
    out.append("  dbms_lob.createtemporary(l_blob, true);")
    for chunk in chunks:
        opn, cls = _pick_q_delim(chunk)
        out.append(f"  l_raw := utl_raw.cast_to_raw(q'{opn}{chunk}{cls}');")
        out.append("  dbms_lob.writeappend(l_blob, utl_raw.length(l_raw), l_raw);")
    out.append("  wwv_flow_imp_shared.create_app_static_file(")
    out.append(f"    p_flow_id => {app_id},")
    out.append("    p_file_name => 'react_theme.css',")
    out.append("    p_mime_type => 'text/css',")
    out.append("    p_file_charset => 'utf-8',")
    out.append("    p_file_content => l_blob);")
    out.append("  dbms_lob.freetemporary(l_blob);")
    out.append("  " + _emit_import_end().replace("\n", "\n  ").rstrip())
    out.append("end;")
    out.append("/")
    return "\n".join(out)


def generate_sql(parsed: Dict[str, Any], workspace: str, app_id: int, version: str) -> Dict[str, Any]:
    ids = IdAllocator()
    release, _ = _release(version)

    header = []
    header.append(f"-- Target APEX Version: {version} (release {release})")
    header.append("-- ============================================================")
    header.append("-- React → Oracle APEX SQL Migration Script")
    header.append(f"-- Workspace: {workspace}")
    header.append(f"-- Application ID: {app_id}")
    header.append(f"-- Detected components: {len(parsed['components'])}")
    header.append("-- ============================================================")
    header.append("")

    body = []
    body.append("begin")
    body.append(_emit_import_begin(workspace, app_id, version))

    page_summary: List[Dict[str, Any]] = []
    page_seq = 100
    for comp in parsed["components"][:40]:
        page_seq += 1
        if comp["type"] == "form":
            body.append(generate_page_form(ids, page_seq, comp, version))
        elif comp["type"] == "report":
            body.append(generate_page_report(ids, page_seq, comp))
        elif comp["type"] == "dashboard":
            body.append(generate_page_dashboard(ids, page_seq, comp))
        page_summary.append({
            "page_id": page_seq,
            "name": comp["name"],
            "type": comp["type"],
            "fields": len(comp.get("fields", [])),
        })

    body.append(_emit_import_end())
    body.append("end;")
    body.append("/")
    body.append("")

    body.append("-- ============================================================")
    body.append("-- Static Application File: react_theme.css")
    body.append("-- ============================================================")
    body.append(generate_css_block(parsed.get("css", ""), app_id, workspace, version))

    sql = "\n".join(header + body)
    return {"sql": sql, "pages": page_summary, "component_count": len(parsed["components"])}
