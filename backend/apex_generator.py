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

def _table_name_for(component_name: str) -> str:
    """Guess a source table name from a React component name.

    Customers       -> CUSTOMERS
    PurchaseOrders  -> PURCHASE_ORDERS
    SalesOrders     -> SALES_ORDERS
    """
    s = re.sub(r"([a-z])([A-Z])", r"\1_\2", component_name or "")
    return re.sub(r"[^A-Z0-9_]+", "_", s.upper()).strip("_")


def _primary_key_field(fields: List[str]) -> str:
    for f in fields:
        if f.lower() in ("id", "uid", "code"):
            return f
        if f.lower().endswith("_id") or f.lower().endswith("id"):
            return f
    return "id"


def _required_fields(fields: List[str]) -> List[str]:
    """Heuristic: name/email/code-like fields are required."""
    out = []
    for f in fields:
        fl = f.lower()
        if any(k in fl for k in ("name", "email", "code", "title", "no")) and len(fl) <= 30:
            out.append(f)
    return out[:5]  # cap


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

    # ------------------------------------------------------------------
    # Automatic Row Fetch  (Before Header pre-rendering process)
    # ------------------------------------------------------------------
    table_name = _table_name_for(name)
    pk_field = _primary_key_field(fields)
    pk_item = f"P{page_id}_{pk_field.upper()}"
    arf_id = ids.next()
    out.append("wwv_flow_imp_page.create_page_process(")
    out.append(f" p_id=>wwv_flow_imp.id({arf_id})")
    out.append(",p_process_sequence=>10")
    out.append(",p_process_point=>'BEFORE_HEADER'")
    out.append(",p_process_type=>'NATIVE_PLSQL'")
    out.append(f",p_process_name=>'Fetch Row from {table_name}'")
    out.append(",p_process_sql_clob=>wwv_flow_string.join(wwv_flow_t_varchar2(")
    out.append(f"'-- Automatic Row Fetch: hydrate P{page_id}_* items from {table_name} when {pk_item} is set',")
    out.append("'-- Replace this stub with actual SELECT INTO / apex_form.fetch_row after import.',")
    out.append("'begin',")
    out.append(f"'  if :{pk_item} is not null then',")
    out.append("'    null; -- TODO: select <cols> into :P<n>_<cols> from " + table_name + " where ...',")
    out.append("'  end if;',")
    out.append("'end;'))")
    out.append(",p_process_clob_language=>'PLSQL'")
    out.append(",p_error_display_location=>'INLINE_IN_NOTIFICATION'")
    out.append(");")

    # ------------------------------------------------------------------
    # Required-field validations  (Not-null check on heuristic key fields)
    # ------------------------------------------------------------------
    for req_field in _required_fields(fields):
        val_id = ids.next()
        req_item = f"P{page_id}_{req_field.upper()}"
        out.append("wwv_flow_imp_page.create_page_validation(")
        out.append(f" p_id=>wwv_flow_imp.id({val_id})")
        out.append(f",p_validation_name=>'{_label(req_field)} Required'")
        out.append(",p_validation_sequence=>10")
        out.append(f",p_validation=>':{req_item} is not null'")
        out.append(",p_validation_type=>'PLSQL_EXPRESSION'")
        out.append(f",p_error_message=>'{_label(req_field)} is required.'")
        out.append(f",p_associated_item=>wwv_flow_imp.id({arf_id})")
        out.append(",p_error_display_location=>'INLINE_WITH_FIELD_AND_NOTIFICATION'")
        out.append(",p_always_execute=>'N'")
        out.append(");")

    # ------------------------------------------------------------------
    # DML Save process  (Process Row of <TABLE>)
    # ------------------------------------------------------------------
    dml_id = ids.next()
    out.append("wwv_flow_imp_page.create_page_process(")
    out.append(f" p_id=>wwv_flow_imp.id({dml_id})")
    out.append(",p_process_sequence=>20")
    out.append(",p_process_point=>'AFTER_SUBMIT'")
    out.append(",p_process_type=>'NATIVE_FORM_DML'")
    out.append(f",p_process_name=>'Process Row of {table_name}'")
    out.append(",p_attribute_02=>'TABLE'")
    out.append(f",p_attribute_03=>'{table_name}'")
    out.append(f",p_attribute_04=>'{pk_item}'")
    out.append(f",p_attribute_05=>'{pk_field.upper()}'")
    out.append(",p_attribute_06=>'EXISTING'")
    out.append(",p_attribute_08=>'Y'")
    out.append(f",p_process_when_button_id=>wwv_flow_imp.id({save_btn_id})")
    out.append(",p_process_success_message=>'Row saved successfully.'")
    out.append(",p_error_display_location=>'INLINE_IN_NOTIFICATION'")
    out.append(");")

    # ------------------------------------------------------------------
    # Branch after submit  -> redirect back to self with cache reset
    # ------------------------------------------------------------------
    branch_id = ids.next()
    out.append("wwv_flow_imp_page.create_page_branch(")
    out.append(f" p_id=>wwv_flow_imp.id({branch_id})")
    out.append(f",p_branch_name=>'After Submit Redirect'")
    out.append(f",p_branch_action=>'f?p=&APP_ID.:{page_id}:&SESSION.::&DEBUG.:RP::&success_msg=#SUCCESS_MSG#'")
    out.append(",p_branch_point=>'AFTER_PROCESSING'")
    out.append(",p_branch_type=>'REDIRECT_URL'")
    out.append(",p_branch_sequence=>10")
    out.append(f",p_branch_when_button_id=>wwv_flow_imp.id({save_btn_id})")
    out.append(");")

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


# =============================================================================
#   DASHBOARD PAGE TEMPLATE  (cloned from f107_page_5.1.sql)
#   Layout: 4 stat-cards (Classic Report) + 1 JET line chart + 1 JET bar chart
# =============================================================================

def generate_dashboard_page(ids: IdAllocator, page_id: int, comp: Dict[str, Any]) -> str:
    name = comp["name"]
    page_name = _label(name)
    page_alias = _alias(name)

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

    # ---- 4 KPI cards (as Classic Report rows in a row container) ----
    cards_plug = ids.next()
    out.append("wwv_flow_imp_page.create_page_plug(")
    out.append(f" p_id=>wwv_flow_imp.id({cards_plug})")
    out.append(",p_plug_name=>'KPI Cards'")
    out.append(",p_region_template_options=>'#DEFAULT#'")
    out.append(f",p_plug_template=>{WORKSPACE_TEMPLATE_IDS['REGION_STANDARD']}")
    out.append(",p_plug_display_sequence=>10")
    out.append(",p_query_type=>'SQL'")
    out.append(",p_plug_source=>'select ''Total'' as label, 1024 as value, ''#28a745'' as color from dual "
                "union all select ''Active'', 312, ''#0d6efd'' from dual "
                "union all select ''Pending'', 47, ''#ffc107'' from dual "
                "union all select ''Completed'', 665, ''#6c757d'' from dual'")
    out.append(",p_plug_source_type=>'NATIVE_SQL_REPORT'")
    out.append(",p_attributes=>wwv_flow_t_plugin_attributes(wwv_flow_t_varchar2(")
    out.append("  'pagination_type', 'NONE',")
    out.append("  'show_null_values_as', '-',")
    out.append("  'strip_html', 'N')).to_clob")
    out.append(");")

    # ---- JET line chart: trend over time ----
    line_chart_plug = ids.next()
    line_chart_id = ids.next()
    line_series_id = ids.next()
    line_xaxis_id = ids.next()
    line_yaxis_id = ids.next()
    line_sql = (
        "select to_char(sysdate - level + 1, 'YYYY-MM-DD') as day, "
        "round(dbms_random.value(50, 200)) as value "
        "from dual connect by level <= 14 order by 1"
    )
    out.append("wwv_flow_imp_page.create_page_plug(")
    out.append(f" p_id=>wwv_flow_imp.id({line_chart_plug})")
    out.append(",p_plug_name=>'Trend'")
    out.append(",p_region_template_options=>'#DEFAULT#'")
    out.append(f",p_plug_template=>{WORKSPACE_TEMPLATE_IDS['REGION_STANDARD']}")
    out.append(",p_plug_display_sequence=>20")
    out.append(",p_plug_source_type=>'NATIVE_JET_CHART'")
    out.append(",p_attributes=>wwv_flow_t_plugin_attributes(wwv_flow_t_varchar2(")
    out.append("  'animation_on_data_change', 'auto',")
    out.append("  'animation_on_display', 'auto')).to_clob")
    out.append(");")
    # JET chart definition
    out.append("wwv_flow_imp_page.create_jet_chart(")
    out.append(f" p_id=>wwv_flow_imp.id({line_chart_id})")
    out.append(f",p_region_id=>wwv_flow_imp.id({line_chart_plug})")
    out.append(",p_chart_type=>'line'")
    out.append(",p_animation_on_display=>'auto'")
    out.append(",p_animation_on_data_change=>'auto'")
    out.append(",p_show_toolbar=>'N'")
    out.append(",p_hover_behavior=>'dim'")
    out.append(",p_zoom_and_scroll=>'off'")
    out.append(");")
    # Y axis
    out.append("wwv_flow_imp_page.create_jet_chart_axis(")
    out.append(f" p_id=>wwv_flow_imp.id({line_yaxis_id})")
    out.append(f",p_chart_id=>wwv_flow_imp.id({line_chart_id})")
    out.append(",p_axis=>'y'")
    out.append(",p_is_rendered=>'on'")
    out.append(",p_format_scaling=>'auto'")
    out.append(",p_scaling=>'linear'")
    out.append(",p_baseline_scaling=>'zero'")
    out.append(",p_position=>'auto'")
    out.append(");")
    # X axis
    out.append("wwv_flow_imp_page.create_jet_chart_axis(")
    out.append(f" p_id=>wwv_flow_imp.id({line_xaxis_id})")
    out.append(f",p_chart_id=>wwv_flow_imp.id({line_chart_id})")
    out.append(",p_axis=>'x'")
    out.append(",p_is_rendered=>'on'")
    out.append(",p_format_scaling=>'auto'")
    out.append(",p_scaling=>'linear'")
    out.append(",p_baseline_scaling=>'zero'")
    out.append(",p_major_tick_rendered=>'on'")
    out.append(",p_minor_tick_rendered=>'off'")
    out.append(",p_position=>'auto'")
    out.append(");")
    # Series
    out.append("wwv_flow_imp_page.create_jet_chart_series(")
    out.append(f" p_id=>wwv_flow_imp.id({line_series_id})")
    out.append(f",p_chart_id=>wwv_flow_imp.id({line_chart_id})")
    out.append(",p_seq=>10")
    out.append(",p_name=>'Value'")
    out.append(",p_query_type=>'SQL'")
    out.append(f",p_query_source=>'{line_sql}'")
    out.append(",p_items_value_column_name=>'VALUE'")
    out.append(",p_items_label_column_name=>'DAY'")
    out.append(");")

    # ---- JET bar chart: distribution ----
    bar_plug = ids.next()
    bar_chart_id = ids.next()
    bar_series_id = ids.next()
    bar_xaxis_id = ids.next()
    bar_yaxis_id = ids.next()
    bar_sql = (
        "select category, value from ("
        "select 'A' as category, 24 as value from dual "
        "union all select 'B', 38 from dual "
        "union all select 'C', 17 from dual "
        "union all select 'D', 52 from dual "
        "union all select 'E', 31 from dual)"
    )
    out.append("wwv_flow_imp_page.create_page_plug(")
    out.append(f" p_id=>wwv_flow_imp.id({bar_plug})")
    out.append(",p_plug_name=>'By Category'")
    out.append(",p_region_template_options=>'#DEFAULT#'")
    out.append(f",p_plug_template=>{WORKSPACE_TEMPLATE_IDS['REGION_STANDARD']}")
    out.append(",p_plug_display_sequence=>30")
    out.append(",p_plug_source_type=>'NATIVE_JET_CHART'")
    out.append(",p_attributes=>wwv_flow_t_plugin_attributes(wwv_flow_t_varchar2(")
    out.append("  'animation_on_data_change', 'auto',")
    out.append("  'animation_on_display', 'auto')).to_clob")
    out.append(");")
    out.append("wwv_flow_imp_page.create_jet_chart(")
    out.append(f" p_id=>wwv_flow_imp.id({bar_chart_id})")
    out.append(f",p_region_id=>wwv_flow_imp.id({bar_plug})")
    out.append(",p_chart_type=>'bar'")
    out.append(",p_animation_on_display=>'auto'")
    out.append(",p_animation_on_data_change=>'auto'")
    out.append(",p_show_toolbar=>'N'")
    out.append(",p_hover_behavior=>'dim'")
    out.append(",p_orientation=>'vertical'")
    out.append(");")
    out.append("wwv_flow_imp_page.create_jet_chart_axis(")
    out.append(f" p_id=>wwv_flow_imp.id({bar_yaxis_id})")
    out.append(f",p_chart_id=>wwv_flow_imp.id({bar_chart_id})")
    out.append(",p_axis=>'y'")
    out.append(",p_is_rendered=>'on'")
    out.append(",p_format_scaling=>'auto'")
    out.append(",p_scaling=>'linear'")
    out.append(",p_baseline_scaling=>'zero'")
    out.append(",p_position=>'auto'")
    out.append(");")
    out.append("wwv_flow_imp_page.create_jet_chart_axis(")
    out.append(f" p_id=>wwv_flow_imp.id({bar_xaxis_id})")
    out.append(f",p_chart_id=>wwv_flow_imp.id({bar_chart_id})")
    out.append(",p_axis=>'x'")
    out.append(",p_is_rendered=>'on'")
    out.append(",p_format_scaling=>'auto'")
    out.append(",p_scaling=>'linear'")
    out.append(",p_position=>'auto'")
    out.append(");")
    out.append("wwv_flow_imp_page.create_jet_chart_series(")
    out.append(f" p_id=>wwv_flow_imp.id({bar_series_id})")
    out.append(f",p_chart_id=>wwv_flow_imp.id({bar_chart_id})")
    out.append(",p_seq=>10")
    out.append(",p_name=>'Count'")
    out.append(",p_query_type=>'SQL'")
    out.append(f",p_query_source=>'{bar_sql}'")
    out.append(",p_items_value_column_name=>'VALUE'")
    out.append(",p_items_label_column_name=>'CATEGORY'")
    out.append(");")

    out.append("end;")
    out.append("/")
    return "\n".join(out)


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
