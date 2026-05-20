"""APEX 24.2 SQL generator — template-driven, based on real f100 exports.

This generator clones the exact structure of two real APEX 24.2 page exports
(form + interactive report) and substitutes only dynamic values:
  - page id, page name, alias, step title
  - region/plug names
  - item names, prompts, display types
  - button names
  - IR column names + labels + display order
  - report SQL source

Hardcoded reference IDs (template_id, field_template, button_template_id, menu_id,
plug_template, menu_template_id) are preserved verbatim from the source export.
If the target workspace uses different IDs, set the WORKSPACE_TEMPLATE_IDS dict
below or query them once and replace.
"""
import re
import time
from typing import Dict, List, Any


# Reference IDs harvested from /app/backend/templates/real_*_page.sql exports.
# These belong to APEX 24.2 Universal Theme. If your workspace uses different
# template IDs, override them here.
WORKSPACE_TEMPLATE_IDS = {
    # Region templates
    "REGION_STANDARD":   4072358936313175081,
    "REGION_IRR":        2100526641005906379,
    "REGION_BREADCRUMB": 2531463326621247859,
    # Field & button templates
    "FIELD_TEMPLATE":    1609121967514267634,
    "BUTTON_TEMPLATE":   2082829544945815391,
    "BUTTON_TEMPLATE_TOP": 4072362960822175091,
    # Menu
    "MENU_ID":           40672399510259321,
    "MENU_TEMPLATE_ID":  4072363345357175094,
}


def _sanitize(value: str) -> str:
    return (value or "").replace("'", "''")


def _label(name: str) -> str:
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", name or "")
    s = s.replace("_", " ").replace("-", " ")
    return " ".join(w.capitalize() for w in s.split())


def _alias(name: str) -> str:
    """Generate an APEX page alias (UPPER-DASH-CASE)."""
    s = re.sub(r"([a-z])([A-Z])", r"\1-\2", name or "")
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").upper()
    return s[:30] or "PAGE"


def _item_display_as(field: str) -> str:
    f = field.lower()
    if "email" in f:
        return "NATIVE_TEXT_FIELD"  # email uses TEXT_FIELD with subtype=EMAIL in attributes
    if any(k in f for k in ("password", "secret")):
        return "NATIVE_PASSWORD"
    if any(k in f for k in ("date", "dob", "birth")):
        return "NATIVE_DATE_PICKER_APEX"
    if any(k in f for k in ("description", "comment", "notes", "message", "body")):
        return "NATIVE_TEXTAREA"
    if any(k in f for k in ("amount", "price", "qty", "quantity", "count", "age", "phone")):
        return "NATIVE_NUMBER_FIELD"
    return "NATIVE_TEXT_FIELD"


def _column_type(field: str) -> str:
    f = field.lower()
    if any(k in f for k in ("amount", "price", "qty", "quantity", "count", "age", "phone", "number")):
        return "NUMBER"
    if any(k in f for k in ("date", "dob", "birth", "_at", "time")):
        return "DATE"
    return "STRING"


class IdAllocator:
    """Allocates synthetic workspace-scoped IDs used inside wwv_flow_imp.id()."""
    def __init__(self):
        # Start in a range comparable to the real exports (17–18 digit)
        self._cur = int(time.time() * 1000) * 100000

    def next(self) -> int:
        self._cur += 1
        return self._cur


# ---- import_begin / import_end ----

APEX_VERSION_META = {
    "22.2": ("22.2.0", "2022.10.07"),
    "23.1": ("23.1.0", "2023.04.18"),
    "23.2": ("23.2.0", "2023.10.31"),
    "24.1": ("24.1.0", "2024.05.22"),
    "24.2": ("24.2.0", "2024.11.30"),
    "26.1": ("26.1.0", "2026.04.30"),
}


def _release(version: str):
    return APEX_VERSION_META.get(version, APEX_VERSION_META["24.2"])


def _emit_import_begin(workspace: str, app_id: int, version: str) -> str:
    release, date = _release(version)
    return (
        "begin\n"
        "wwv_flow_imp.import_begin (\n"
        f" p_version_yyyy_mm_dd=>'{date}'\n"
        f",p_release=>'{release}'\n"
        f",p_default_workspace_id=>apex_util.find_security_group_id('{_sanitize(workspace)}')\n"
        f",p_default_application_id=>{app_id}\n"
        ",p_default_id_offset=>0\n"
        f",p_default_owner=>'{_sanitize(workspace)}'\n"
        ");\n"
        "end;\n"
        "/\n"
    )


def _emit_import_end() -> str:
    return (
        "begin\n"
        "wwv_flow_imp.import_end(p_auto_install_sup_obj => nvl(wwv_flow_application_install.get_auto_install_sup_obj, false)\n"
        ");\n"
        "commit;\n"
        "end;\n"
        "/\n"
    )


# =============================================================================
#   FORM PAGE TEMPLATE  (cloned from real_form_page.sql)
# =============================================================================

def generate_form_page(ids: IdAllocator, page_id: int, comp: Dict[str, Any]) -> str:
    name = comp["name"]
    fields = comp.get("fields") or ["name", "email"]
    page_name = _label(name)
    page_alias = _alias(name)

    plug_id = ids.next()
    save_btn_id = ids.next()
    cancel_btn_id = ids.next()

    out = []
    out.append(f"prompt --application/pages/page_{page_id:05d}")
    out.append("begin")
    out.append("wwv_flow_imp_page.create_page(")
    out.append(f" p_id=>{page_id}")
    out.append(f",p_name=>'{_sanitize(page_name)}'")
    out.append(f",p_alias=>'{page_alias}'")
    out.append(f",p_step_title=>'{_sanitize(page_name)}'")
    out.append(",p_autocomplete_on_off=>'OFF'")
    out.append(",p_page_template_options=>'#DEFAULT#'")
    out.append(",p_protection_level=>'C'")
    out.append(",p_page_component_map=>'17'")
    out.append(");")

    # Form region — empty container (matches real export exactly: no source_type)
    out.append("wwv_flow_imp_page.create_page_plug(")
    out.append(f" p_id=>wwv_flow_imp.id({plug_id})")
    out.append(f",p_plug_name=>'{_sanitize(page_name)}'")
    out.append(",p_region_template_options=>'#DEFAULT#:t-Region--scrollBody'")
    out.append(f",p_plug_template=>{WORKSPACE_TEMPLATE_IDS['REGION_STANDARD']}")
    out.append(",p_plug_display_sequence=>10")
    out.append(",p_location=>null")
    out.append(",p_attributes=>wwv_flow_t_plugin_attributes(wwv_flow_t_varchar2(")
    out.append("  'expand_shortcuts', 'N',")
    out.append("  'output_as', 'HTML')).to_clob")
    out.append(");")

    # Save button
    out.append("wwv_flow_imp_page.create_page_button(")
    out.append(f" p_id=>wwv_flow_imp.id({save_btn_id})")
    out.append(",p_button_sequence=>40")
    out.append(f",p_button_plug_id=>wwv_flow_imp.id({plug_id})")
    out.append(",p_button_name=>'Save'")
    out.append(",p_button_action=>'SUBMIT'")
    out.append(",p_button_template_options=>'#DEFAULT#:t-Button--iconLeft'")
    out.append(f",p_button_template_id=>{WORKSPACE_TEMPLATE_IDS['BUTTON_TEMPLATE']}")
    out.append(",p_button_is_hot=>'Y'")
    out.append(",p_button_image_alt=>'Save'")
    out.append(",p_button_position=>'EDIT'")
    out.append(");")

    # Cancel button
    out.append("wwv_flow_imp_page.create_page_button(")
    out.append(f" p_id=>wwv_flow_imp.id({cancel_btn_id})")
    out.append(",p_button_sequence=>50")
    out.append(f",p_button_plug_id=>wwv_flow_imp.id({plug_id})")
    out.append(",p_button_name=>'cancel'")
    out.append(",p_button_action=>'REDIRECT_PAGE'")
    out.append(",p_button_template_options=>'#DEFAULT#:t-Button--iconLeft'")
    out.append(f",p_button_template_id=>{WORKSPACE_TEMPLATE_IDS['BUTTON_TEMPLATE']}")
    out.append(",p_button_is_hot=>'Y'")
    out.append(",p_button_image_alt=>'Cancel'")
    out.append(",p_button_position=>'EDIT'")
    out.append(");")

    # Items
    seq = 10
    for i, field in enumerate(fields[:30]):
        item_id = ids.next()
        display_as = _item_display_as(field)
        out.append("wwv_flow_imp_page.create_page_item(")
        out.append(f" p_id=>wwv_flow_imp.id({item_id})")
        out.append(f",p_name=>'P{page_id}_{field.upper()}'")
        out.append(f",p_item_sequence=>{seq}")
        out.append(f",p_item_plug_id=>wwv_flow_imp.id({plug_id})")
        out.append(f",p_prompt=>'{_sanitize(_label(field))}'")
        out.append(f",p_display_as=>'{display_as}'")
        out.append(",p_cSize=>30")
        if i > 0:
            out.append(",p_begin_on_new_line=>'N'")
        out.append(f",p_field_template=>{WORKSPACE_TEMPLATE_IDS['FIELD_TEMPLATE']}")
        out.append(",p_item_template_options=>'#DEFAULT#'")
        # Attributes block matches real export exactly
        if display_as == "NATIVE_NUMBER_FIELD":
            out.append(",p_attributes=>wwv_flow_t_plugin_attributes(wwv_flow_t_varchar2(")
            out.append("  'number_alignment', 'left',")
            out.append("  'virtual_keyboard', 'decimal')).to_clob")
        else:
            out.append(",p_attributes=>wwv_flow_t_plugin_attributes(wwv_flow_t_varchar2(")
            out.append("  'disabled', 'N',")
            out.append("  'submit_when_enter_pressed', 'N',")
            out.append("  'subtype', 'TEXT',")
            out.append("  'trim_spaces', 'BOTH')).to_clob")
        out.append(");")
        seq += 10

    out.append("end;")
    out.append("/")
    return "\n".join(out)


# =============================================================================
#   INTERACTIVE REPORT PAGE TEMPLATE  (cloned from real_ir_page.sql)
# =============================================================================

def _default_report_columns(fields: List[str]) -> List[Dict[str, Any]]:
    """Convert React field names into IR column definitions."""
    if not fields:
        fields = ["id", "name", "status", "created_at"]
    cols = []
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for i, f in enumerate(fields[:26]):
        cols.append({
            "db_name": f.upper(),
            "label": _label(f),
            "type": _column_type(f),
            "order": (i + 1) * 10,
            "ident": letters[i],
        })
    return cols


def generate_ir_page(ids: IdAllocator, page_id: int, comp: Dict[str, Any]) -> str:
    name = comp["name"]
    page_name = _label(name)
    page_alias = _alias(name)
    fields = comp.get("fields") or []
    columns = _default_report_columns(fields)

    plug_id = ids.next()
    ws_id = ids.next()
    rpt_id = ids.next()
    create_btn_id = ids.next()

    # Source SQL — synthesize a fake-but-runnable query yielding the declared columns
    select_list = ", ".join([f"'{c['db_name']}_' || rownum as {c['db_name']}" if c["type"] == "STRING"
                             else (f"rownum as {c['db_name']}" if c["type"] == "NUMBER"
                                   else f"sysdate - rownum as {c['db_name']}")
                             for c in columns])
    source_sql = f"select {select_list} from dual connect by level <= 25"
    source_sql_escaped = source_sql.replace("'", "''")

    out = []
    out.append(f"prompt --application/pages/page_{page_id:05d}")
    out.append("begin")
    out.append("wwv_flow_imp_page.create_page(")
    out.append(f" p_id=>{page_id}")
    out.append(f",p_name=>'{_sanitize(page_name)}'")
    out.append(f",p_alias=>'{page_alias}'")
    out.append(f",p_step_title=>'{_sanitize(page_name)}'")
    out.append(",p_autocomplete_on_off=>'OFF'")
    out.append(",p_page_template_options=>'#DEFAULT#'")
    out.append(",p_protection_level=>'C'")
    out.append(",p_page_component_map=>'18'")
    out.append(");")

    # IR region
    out.append("wwv_flow_imp_page.create_page_plug(")
    out.append(f" p_id=>wwv_flow_imp.id({plug_id})")
    out.append(f",p_plug_name=>'{_sanitize(page_name)}'")
    out.append(f",p_title=>'{_sanitize(page_name)}'")
    out.append(",p_region_template_options=>'#DEFAULT#:t-IRR-region--hideHeader js-addHiddenHeadingRoleDesc'")
    out.append(",p_component_template_options=>'#DEFAULT#'")
    out.append(f",p_plug_template=>{WORKSPACE_TEMPLATE_IDS['REGION_IRR']}")
    out.append(",p_plug_display_sequence=>10")
    out.append(",p_query_type=>'SQL'")
    out.append(f",p_plug_source=>'{source_sql_escaped}'")
    out.append(",p_include_rowid_column=>false")
    out.append(",p_plug_source_type=>'NATIVE_IR'")
    out.append(",p_prn_content_disposition=>'ATTACHMENT'")
    out.append(",p_prn_units=>'INCHES'")
    out.append(",p_prn_paper_size=>'LETTER'")
    out.append(",p_prn_width=>11")
    out.append(",p_prn_height=>8.5")
    out.append(",p_prn_orientation=>'HORIZONTAL'")
    out.append(f",p_prn_page_header=>'{_sanitize(page_name)}'")
    out.append(",p_prn_page_header_font_color=>'#000000'")
    out.append(",p_prn_page_header_font_family=>'Helvetica'")
    out.append(",p_prn_page_header_font_weight=>'normal'")
    out.append(",p_prn_page_header_font_size=>'12'")
    out.append(",p_prn_page_footer_font_color=>'#000000'")
    out.append(",p_prn_page_footer_font_family=>'Helvetica'")
    out.append(",p_prn_page_footer_font_weight=>'normal'")
    out.append(",p_prn_page_footer_font_size=>'12'")
    out.append(",p_prn_header_bg_color=>'#EEEEEE'")
    out.append(",p_prn_header_font_color=>'#000000'")
    out.append(",p_prn_header_font_family=>'Helvetica'")
    out.append(",p_prn_header_font_weight=>'bold'")
    out.append(",p_prn_header_font_size=>'10'")
    out.append(",p_prn_body_bg_color=>'#FFFFFF'")
    out.append(",p_prn_body_font_color=>'#000000'")
    out.append(",p_prn_body_font_family=>'Helvetica'")
    out.append(",p_prn_body_font_weight=>'normal'")
    out.append(",p_prn_body_font_size=>'10'")
    out.append(",p_prn_border_width=>.5")
    out.append(",p_prn_page_header_alignment=>'CENTER'")
    out.append(",p_prn_page_footer_alignment=>'CENTER'")
    out.append(",p_prn_border_color=>'#666666'")
    out.append(");")

    # Worksheet definition
    out.append("wwv_flow_imp_page.create_worksheet(")
    out.append(f" p_id=>wwv_flow_imp.id({ws_id})")
    out.append(",p_max_row_count=>'1000000'")
    out.append(",p_pagination_type=>'ROWS_X_TO_Y'")
    out.append(",p_pagination_display_pos=>'BOTTOM_RIGHT'")
    out.append(",p_report_list_mode=>'TABS'")
    out.append(",p_lazy_loading=>false")
    out.append(",p_show_detail_link=>'N'")
    out.append(",p_show_notify=>'Y'")
    out.append(",p_download_formats=>'CSV:HTML:XLSX:PDF'")
    out.append(",p_enable_mail_download=>'Y'")
    out.append(f",p_internal_uid=>{ws_id}")
    out.append(");")

    # Columns
    column_db_names = []
    for col in columns:
        col_id = ids.next()
        out.append("wwv_flow_imp_page.create_worksheet_column(")
        out.append(f" p_id=>wwv_flow_imp.id({col_id})")
        out.append(f",p_db_column_name=>'{col['db_name']}'")
        out.append(f",p_display_order=>{col['order']}")
        out.append(f",p_column_identifier=>'{col['ident']}'")
        out.append(f",p_column_label=>'{_sanitize(col['label'])}'")
        out.append(f",p_column_type=>'{col['type']}'")
        if col["type"] == "NUMBER":
            out.append(",p_heading_alignment=>'RIGHT'")
            out.append(",p_column_alignment=>'RIGHT'")
        else:
            out.append(",p_heading_alignment=>'LEFT'")
        if col["type"] == "DATE":
            out.append(",p_tz_dependent=>'N'")
        out.append(",p_use_as_row_header=>'N'")
        out.append(");")
        column_db_names.append(col["db_name"])

    # Default report definition
    out.append("wwv_flow_imp_page.create_worksheet_rpt(")
    out.append(f" p_id=>wwv_flow_imp.id({rpt_id})")
    out.append(",p_application_user=>'APXWS_DEFAULT'")
    out.append(",p_report_seq=>10")
    out.append(f",p_report_alias=>'{rpt_id % 1000000}'")
    out.append(",p_status=>'PUBLIC'")
    out.append(",p_is_default=>'Y'")
    out.append(f",p_report_columns=>'{':'.join(column_db_names)}'")
    out.append(");")

    # Create button (top-right)
    out.append("wwv_flow_imp_page.create_page_button(")
    out.append(f" p_id=>wwv_flow_imp.id({create_btn_id})")
    out.append(",p_button_sequence=>10")
    out.append(f",p_button_plug_id=>wwv_flow_imp.id({plug_id})")
    out.append(",p_button_name=>'CREATE'")
    out.append(",p_button_action=>'REDIRECT_PAGE'")
    out.append(",p_button_template_options=>'#DEFAULT#'")
    out.append(f",p_button_template_id=>{WORKSPACE_TEMPLATE_IDS['BUTTON_TEMPLATE_TOP']}")
    out.append(",p_button_is_hot=>'Y'")
    out.append(",p_button_image_alt=>'Create'")
    out.append(",p_button_position=>'TOP'")
    out.append(",p_button_alignment=>'RIGHT'")
    out.append(");")

    out.append("end;")
    out.append("/")
    return "\n".join(out)


# Dashboard pages reuse the IR template (stat-card style dashboards weren't
# given a reference export, so we generate a single summary IR page).
def generate_dashboard_page(ids: IdAllocator, page_id: int, comp: Dict[str, Any]) -> str:
    comp = {**comp, "fields": comp.get("fields") or ["metric", "value", "trend", "as_of_date"]}
    return generate_ir_page(ids, page_id, comp)


# =============================================================================
#   CSS static file (chunked BLOB — unchanged from previous version)
# =============================================================================

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


def generate_css_block(css_content: str, app_id: int) -> str:
    css = css_content if css_content else "/* react theme placeholder */"
    chunks = _chunk_css(css, max_bytes=16000)
    out = []
    out.append("declare")
    out.append("  l_blob blob;")
    out.append("  l_raw raw(32767);")
    out.append("begin")
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
    out.append("end;")
    out.append("/")
    return "\n".join(out)


# =============================================================================
#   MASTER SCRIPT ASSEMBLY
# =============================================================================

def generate_sql(parsed: Dict[str, Any], workspace: str, app_id: int, version: str) -> Dict[str, Any]:
    ids = IdAllocator()
    release, _ = _release(version)

    out = []
    out.append("prompt --application/set_environment")
    out.append("set define off verify off feedback off")
    out.append("whenever sqlerror exit sql.sqlcode rollback")
    out.append("--------------------------------------------------------------------------------")
    out.append("-- React → Oracle APEX SQL Migration Script")
    out.append(f"-- Workspace: {workspace}")
    out.append(f"-- Application ID: {app_id}")
    out.append(f"-- Target APEX Version: {version} (release {release})")
    out.append(f"-- Detected components: {len(parsed['components'])}")
    out.append("--------------------------------------------------------------------------------")
    out.append("")
    out.append(_emit_import_begin(workspace, app_id, version))

    page_summary: List[Dict[str, Any]] = []
    page_seq = 100
    for comp in parsed["components"][:40]:
        page_seq += 1
        out.append("")
        if comp["type"] == "form":
            out.append(generate_form_page(ids, page_seq, comp))
        elif comp["type"] == "report":
            out.append(generate_ir_page(ids, page_seq, comp))
        elif comp["type"] == "dashboard":
            out.append(generate_dashboard_page(ids, page_seq, comp))
        page_summary.append({
            "page_id": page_seq,
            "name": comp["name"],
            "type": comp["type"],
            "fields": len(comp.get("fields", [])),
        })

    # Static CSS file (in its own block — must be inside an import context)
    out.append("")
    out.append("prompt --application/shared_components/files/react_theme")
    out.append(generate_css_block(parsed.get("css", ""), app_id))

    out.append("prompt --application/end_environment")
    out.append(_emit_import_end())
    out.append("set verify on feedback on define on")
    out.append("prompt  ...done")

    sql = "\n".join(out)
    return {"sql": sql, "pages": page_summary, "component_count": len(parsed["components"])}
