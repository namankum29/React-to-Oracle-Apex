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


REACT_NATIVE_CSS = """
.t-Body-content {
  background:#f8fafc!important;
}

.t-Region {
  border-radius:16px!important;
  border:1px solid #e2e8f0!important;
  box-shadow:0 8px 24px rgba(15,23,42,.08)!important;
  overflow:hidden!important;
}

.t-Region-header {
  background:#fff!important;
  border-bottom:1px solid #e2e8f0!important;
}

.t-Region-title {
  font-size:20px!important;
  font-weight:700!important;
  color:#1e293b!important;
}

.t-Button--hot,
.t-Button.is-hot {
  background:#0284c7!important;
  border-color:#0284c7!important;
  border-radius:10px!important;
  font-weight:600!important;
}

.a-IRR-table th {
  background:#f8fafc!important;
  color:#64748b!important;
  font-size:12px!important;
  text-transform:uppercase!important;
}

.a-IRR-table td {
  padding:14px 12px!important;
}

.t-Form-fieldContainer {
  margin-bottom:18px!important;
}

.apex-item-text,
.apex-item-number,
.apex-item-textarea,
select,
textarea {
  width:100%!important;
  min-height:46px!important;
  border-radius:10px!important;
  border:1px solid #cbd5e1!important;
  padding:8px 12px!important;
  box-shadow:none!important;
}

.apex-item-text:focus,
.apex-item-number:focus,
.apex-item-textarea:focus,
select:focus,
textarea:focus {
  border-color:#0284c7!important;
  outline:none!important;
}
"""

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

    out.append("wwv_flow_imp_page.create_page_plug(")
    out.append(f" p_id=>wwv_flow_imp.id({plug_id})")
    out.append(f",p_plug_name=>'{_sanitize(page_name)}'")
    out.append(",p_region_template_options=>'#DEFAULT#'")
    out.append(f",p_plug_template=>{WORKSPACE_TEMPLATE_IDS['REGION_STANDARD']}")
    out.append(",p_plug_display_sequence=>10")
    out.append(",p_location=>null")
    out.append(",p_attributes=>wwv_flow_t_plugin_attributes(wwv_flow_t_varchar2(")
    out.append("  'expand_shortcuts', 'N',")
    out.append("  'output_as', 'HTML')).to_clob")
    out.append(");")

    out.append("wwv_flow_imp_page.create_page_button(")
    out.append(f" p_id=>wwv_flow_imp.id({save_btn_id})")
    out.append(",p_button_sequence=>40")
    out.append(f",p_button_plug_id=>wwv_flow_imp.id({plug_id})")
    out.append(",p_button_name=>'SAVE'")
    out.append(",p_button_action=>'SUBMIT'")
    out.append(",p_button_template_options=>'#DEFAULT#:t-Button--hot'")
    out.append(f",p_button_template_id=>{WORKSPACE_TEMPLATE_IDS['BUTTON_TEMPLATE']}")
    out.append(",p_button_is_hot=>'Y'")
    out.append(",p_button_image_alt=>'Save'")
    out.append(",p_button_position=>'EDIT'")
    out.append(");")

    out.append("wwv_flow_imp_page.create_page_button(")
    out.append(f" p_id=>wwv_flow_imp.id({cancel_btn_id})")
    out.append(",p_button_sequence=>50")
    out.append(f",p_button_plug_id=>wwv_flow_imp.id({plug_id})")
    out.append(",p_button_name=>'CANCEL'")
    out.append(",p_button_action=>'REDIRECT_PAGE'")
    out.append(",p_button_template_options=>'#DEFAULT#'")
    out.append(f",p_button_template_id=>{WORKSPACE_TEMPLATE_IDS['BUTTON_TEMPLATE']}")
    out.append(",p_button_image_alt=>'Cancel'")
    out.append(",p_button_position=>'EDIT'")
    out.append(");")

    seq = 10
    for field in fields[:30]:
        item_id = ids.next()
        display_as = _item_display_as(field)

        out.append("wwv_flow_imp_page.create_page_item(")
        out.append(f" p_id=>wwv_flow_imp.id({item_id})")
        out.append(f",p_name=>'P{page_id}_{field.upper()}'")
        out.append(f",p_item_sequence=>{seq}")
        out.append(f",p_item_plug_id=>wwv_flow_imp.id({plug_id})")
        out.append(f",p_prompt=>'{_sanitize(_label(field))}'")
        out.append(f",p_display_as=>'{display_as}'")
        out.append(",p_cSize=>100")
        out.append(f",p_field_template=>{WORKSPACE_TEMPLATE_IDS['FIELD_TEMPLATE']}")
        out.append(",p_item_template_options=>'#DEFAULT#:margin-bottom-md'")

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

    table_name = _table_name_for(name)
    pk_field = _primary_key_field(fields)
    pk_item = f"P{page_id}_{pk_field.upper()}"

    select_cols = [f.upper() for f in fields[:30]]
    into_items = [f"P{page_id}_{c}" for c in select_cols]

    select_csv = ", ".join(select_cols) or "1"
    into_csv = ", ".join([f":{i}" for i in into_items]) or "null"

    arf_id = ids.next()
    out.append("wwv_flow_imp_page.create_page_process(")
    out.append(f" p_id=>wwv_flow_imp.id({arf_id})")
    out.append(",p_process_sequence=>10")
    out.append(",p_process_point=>'BEFORE_HEADER'")
    out.append(",p_process_type=>'NATIVE_PLSQL'")
    out.append(f",p_process_name=>'Fetch Row from {table_name}'")
    out.append(",p_process_sql_clob=>wwv_flow_string.join(wwv_flow_t_varchar2(")
    out.append("'begin',")
    out.append(f"'  if :{pk_item} is not null then',")
    out.append(f"'    select {select_csv}',")
    out.append(f"'    into   {into_csv}',")
    out.append(f"'    from   {table_name}',")
    out.append(f"'    where  {pk_field.upper()} = :{pk_item};',")
    out.append("'  end if;',")
    out.append("'exception',")
    out.append("'  when no_data_found then null;',")
    out.append("'end;'))")
    out.append(",p_process_clob_language=>'PLSQL'")
    out.append(",p_error_display_location=>'INLINE_IN_NOTIFICATION'")
    out.append(f",p_process_when=>'{pk_item}'")
    out.append(",p_process_when_type=>'ITEM_IS_NOT_NULL'")
    out.append(");")

    defaults: Dict[str, str] = comp.get("defaults") or {}

    for field, value in defaults.items():
        if field not in fields or value in ("", None):
            continue

        if field == pk_field:
            continue

        if any(tok in str(value) for tok in ("(", ")", "=>", "${", "`", "[", "]", "function")):
            continue

        if len(str(value)) > 60:
            continue

        comp_id = ids.next()
        target_item = f"P{page_id}_{field.upper()}"
        safe_val = _sanitize(str(value))

        out.append("wwv_flow_imp_page.create_page_computation(")
        out.append(f" p_id=>wwv_flow_imp.id({comp_id})")
        out.append(",p_computation_sequence=>30")
        out.append(f",p_computation_item=>'{target_item}'")
        out.append(",p_computation_point=>'BEFORE_HEADER'")
        out.append(",p_computation_type=>'STATIC_ASSIGNMENT'")
        out.append(f",p_computation=>'{safe_val}'")
        out.append(f",p_compute_when=>'{target_item}'")
        out.append(",p_compute_when_type=>'ITEM_IS_NULL'")
        out.append(");")

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
        out.append(",p_error_display_location=>'INLINE_WITH_FIELD_AND_NOTIFICATION'")
        out.append(",p_always_execute=>'N'")
        out.append(");")

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

    branch_id = ids.next()
    out.append("wwv_flow_imp_page.create_page_branch(")
    out.append(f" p_id=>wwv_flow_imp.id({branch_id})")
    out.append(",p_branch_name=>'After Submit Redirect'")
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

# def generate_dashboard_page(ids: IdAllocator, page_id: int, comp: Dict[str, Any]) -> str:

#     name = comp["name"]
#     page_name = _label(name)
#     page_alias = _alias(name)

#     plug_id = ids.next()

#     html = f"""
# <div class="rt-shell">

# <div class="rt-header">
#   <div>
#     <h1 class="rt-title">{page_name}</h1>
#     <div class="rt-subtitle">
#       Dashboard Overview
#     </div>
#   </div>
# </div>

# <div class="rt-grid">
#   <div class="rt-card">
#     <div class="rt-card-label">Total Orders</div>
#     <div class="rt-card-value">248</div>
#   </div>

#   <div class="rt-card">
#     <div class="rt-card-label">Revenue</div>
#     <div class="rt-card-value">$84K</div>
#   </div>

#   <div class="rt-card">
#     <div class="rt-card-label">Pending</div>
#     <div class="rt-card-value">18</div>
#   </div>

#   <div class="rt-card">
#     <div class="rt-card-label">Completed</div>
#     <div class="rt-card-value">165</div>
#   </div>
# </div>

# </div>
# """

#     out = []

#     out.append(f"prompt --application/pages/page_{page_id:05d}")

#     out.append("begin")

#     out.append("wwv_flow_imp_page.create_page(")
#     out.append(f" p_id=>{page_id}")
#     out.append(f",p_name=>'{_sanitize(page_name)}'")
#     out.append(f",p_alias=>'{page_alias}'")
#     out.append(f",p_step_title=>'{_sanitize(page_name)}'")
#     out.append(",p_page_template_options=>'#DEFAULT#'")
#     # out.append(",p_css_classes=>'rt-page'")
#     out.append(");")

#     out.append("wwv_flow_imp_page.create_page_plug(")
#     out.append(f" p_id=>wwv_flow_imp.id({plug_id})")
#     out.append(",p_plug_display_sequence=>10")
#     out.append(f",p_plug_name=>'{_sanitize(page_name)}'")
#     out.append(f",p_plug_template=>{WORKSPACE_TEMPLATE_IDS['REGION_STANDARD']}")
#     # out.append(f",p_plug_source=>q'~{html}~'")
#     out.append(f",p_plug_source=>q'!{html}!'")
#     out.append(");")

#     out.append("end;")
#     out.append("/")

#     # return '\\n'.join(out)
#     return "\n".join(out)


def generate_dashboard_page(ids: IdAllocator, page_id: int, comp: Dict[str, Any]) -> str:

    name = comp["name"]
    page_name = _label(name)
    page_alias = _alias(name)

    plug_id = ids.next()

    dashboard_html = (
        '<div class="rt-shell">'
        '<div class="rt-header">'
        '<div>'
        f'<h1 class="rt-title">{_sanitize(page_name)}</h1>'
        '<div class="rt-subtitle">Dashboard Overview</div>'
        '</div>'
        '</div>'
        '<div class="rt-grid">'
        '<div class="rt-card"><div class="rt-card-label">Total Orders</div><div class="rt-card-value">248</div></div>'
        '<div class="rt-card"><div class="rt-card-label">Revenue</div><div class="rt-card-value">$84K</div></div>'
        '<div class="rt-card"><div class="rt-card-label">Pending</div><div class="rt-card-value">18</div></div>'
        '<div class="rt-card"><div class="rt-card-label">Completed</div><div class="rt-card-value">165</div></div>'
        '</div>'
        '</div>'
    )

    out = []
    out.append(f"prompt --application/pages/page_{page_id:05d}")
    out.append("begin")

    out.append("wwv_flow_imp_page.create_page(")
    out.append(f" p_id=>{page_id}")
    out.append(f",p_name=>'{_sanitize(page_name)}'")
    out.append(f",p_alias=>'{page_alias}'")
    out.append(f",p_step_title=>'{_sanitize(page_name)}'")
    out.append(",p_page_template_options=>'#DEFAULT#'")
    out.append(",p_autocomplete_on_off=>'OFF'")
    out.append(",p_protection_level=>'C'")
    out.append(",p_page_component_map=>'18'")
    out.append(");")

    out.append("wwv_flow_imp_page.create_page_plug(")
    out.append(f" p_id=>wwv_flow_imp.id({plug_id})")
    out.append(f",p_plug_name=>'{_sanitize(page_name)}'")
    out.append(",p_region_template_options=>'#DEFAULT#'")
    out.append(f",p_plug_template=>{WORKSPACE_TEMPLATE_IDS['REGION_STANDARD']}")
    out.append(",p_plug_display_sequence=>10")
    out.append(",p_location=>null")
    out.append(f",p_plug_source=>q'~{dashboard_html}~'")
    out.append(",p_attributes=>wwv_flow_t_plugin_attributes(wwv_flow_t_varchar2(")
    out.append("  'expand_shortcuts', 'N',")
    out.append("  'output_as', 'HTML')).to_clob")
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

REACT_CLONE_CSS = """
.rt-shell{min-height:100vh;background:#f8fafc;font-family:Inter,Arial,sans-serif;padding:32px}
.rt-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:24px}
.rt-title{font-size:28px;font-weight:700;color:#1e293b;margin:0}
.rt-subtitle{font-size:14px;color:#64748b;margin-top:4px}
.rt-btn-primary{background:#0284c7;color:#fff;border:0;border-radius:10px;padding:10px 16px;font-weight:600}
.rt-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}
.rt-card{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:20px;box-shadow:0 1px 2px rgba(0,0,0,.05)}
.rt-card-label{font-size:12px;color:#64748b;text-transform:uppercase;font-weight:600}
.rt-card-value{font-size:26px;color:#1e293b;font-weight:700;margin-top:6px}
.rt-panel{background:#fff;border:1px solid #e2e8f0;border-radius:14px;box-shadow:0 1px 2px rgba(0,0,0,.05);overflow:hidden}
.rt-toolbar{display:flex;gap:12px;padding:16px;border-bottom:1px solid #e2e8f0}
.rt-input,.rt-select{height:42px;border:1px solid #cbd5e1;border-radius:10px;padding:0 12px}
.rt-input{flex:1}
.rt-table{width:100%;border-collapse:collapse}
.rt-table th{background:#f8fafc;text-align:left;padding:12px 16px;font-size:12px;color:#64748b;text-transform:uppercase}
.rt-table td{padding:14px 16px;border-top:1px solid #f1f5f9;color:#334155;font-size:14px}
.rt-badge{display:inline-flex;border-radius:999px;padding:4px 10px;font-size:12px;font-weight:600;background:#e0f2fe;color:#0369a1}
.rt-actions{display:flex;gap:8px}
.rt-icon-btn{width:32px;height:32px;border:0;border-radius:8px;background:#f1f5f9;color:#475569}
.rt-modal{margin-top:24px;background:#fff;border:1px solid #e2e8f0;border-radius:18px;box-shadow:0 20px 40px rgba(15,23,42,.12);max-width:560px}
.rt-modal-head{display:flex;justify-content:space-between;padding:18px 22px;border-bottom:1px solid #e2e8f0}
.rt-modal-body{padding:22px;display:grid;gap:16px}
.rt-form-field label{display:block;font-size:13px;font-weight:600;color:#334155;margin-bottom:6px}
.rt-form-field input,.rt-form-field select,.rt-form-field textarea{width:100%;height:44px;border:1px solid #cbd5e1;border-radius:10px;padding:0 12px}
.rt-modal-foot{display:flex;gap:12px;padding:0 22px 22px}
.rt-btn-secondary{background:#e2e8f0;color:#334155;border:0;border-radius:10px;padding:10px 16px;font-weight:600;flex:1}
.rt-btn-save{background:#0284c7;color:#fff;border:0;border-radius:10px;padding:10px 16px;font-weight:600;flex:1}
@media(max-width:900px){.rt-grid{grid-template-columns:1fr}.rt-header{flex-direction:column;align-items:flex-start;gap:12px}}
"""


def _react_sample_rows(comp):
    name = comp["name"].lower()

    if "customer" in name:
        return [
            ["Acme Corp", "acme@example.com", "9876543210", "<span class='rt-badge'>Active</span>"],
            ["Global Traders", "global@example.com", "9876501234", "<span class='rt-badge'>Pending</span>"],
            ["Nova Industries", "nova@example.com", "9876511111", "<span class='rt-badge'>Active</span>"],
        ]

    if "purchase" in name:
        return [
            ["PO-1001", "ABC Supplier", "2026-05-01", "<span class='rt-badge'>Draft</span>"],
            ["PO-1002", "Global Supplies", "2026-05-04", "<span class='rt-badge'>Confirmed</span>"],
        ]

    if "sales" in name:
        return [
            ["SO-1001", "Acme Corp", "2026-05-03", "<span class='rt-badge'>Shipped</span>"],
            ["SO-1002", "Nova Industries", "2026-05-06", "<span class='rt-badge'>Draft</span>"],
        ]

    return [
        ["ORD-1001", "Website redesign", "$1200", "<span class='rt-badge'>Pending</span>"],
        ["ORD-1002", "ERP customization", "$2400", "<span class='rt-badge'>Completed</span>"],
    ]


def _react_columns(comp):
    fields = comp.get("fields") or comp.get("table_columns") or []

    if fields:
        return [_label(f) for f in fields[:5]]

    name = comp["name"].lower()

    if "customer" in name:
        return ["Name", "Email", "Phone", "Status"]

    if "purchase" in name:
        return ["PO Number", "Supplier", "Date", "Status"]

    if "sales" in name:
        return ["SO Number", "Customer", "Date", "Status"]

    return ["Order No", "Description", "Amount", "Status"]


def _build_table_html(comp):
    cols = _react_columns(comp)
    rows = _react_sample_rows(comp)

    th = "".join([f"<th>{c}</th>" for c in cols])
    th += "<th>Actions</th>"

    body = []
    for row in rows:
        tds = "".join([f"<td>{cell}</td>" for cell in row[:len(cols)]])
        tds += """
<td>
  <div class="rt-actions">
    <button class="rt-icon-btn">✎</button>
    <button class="rt-icon-btn">🗑</button>
  </div>
</td>
"""
        body.append(f"<tr>{tds}</tr>")

    return f"""
<table class="rt-table">
  <thead><tr>{th}</tr></thead>
  <tbody>{''.join(body)}</tbody>
</table>
"""


def _build_form_html(comp):
    fields = comp.get("fields") or []

    if not fields:
        name = comp["name"].lower()
        if "customer" in name:
            fields = ["name", "email", "phone", "status"]
        elif "purchase" in name:
            fields = ["po_number", "supplier", "order_date", "status", "notes"]
        elif "sales" in name:
            fields = ["so_number", "customer_name", "order_date", "status", "notes"]
        else:
            fields = ["description", "amount", "status"]

    controls = []
    for f in fields[:8]:
        label = _label(f)
        if "status" in f.lower():
            control = f"""
<div class="rt-form-field">
  <label>{label}</label>
  <select><option>Active</option><option>Pending</option><option>Completed</option></select>
</div>
"""
        elif "notes" in f.lower() or "description" in f.lower():
            control = f"""
<div class="rt-form-field">
  <label>{label}</label>
  <textarea></textarea>
</div>
"""
        else:
            control = f"""
<div class="rt-form-field">
  <label>{label}</label>
  <input type="text" />
</div>
"""
        controls.append(control)

    return f"""
<div class="rt-modal">
  <div class="rt-modal-head">
    <strong>Create / Edit {_label(comp["name"])}</strong>
    <span>×</span>
  </div>
  <div class="rt-modal-body">
    {''.join(controls)}
  </div>
  <div class="rt-modal-foot">
    <button class="rt-btn-secondary">Cancel</button>
    <button class="rt-btn-save">Save</button>
  </div>
</div>
"""


def generate_react_clone_page(ids: IdAllocator, page_id: int, comp: Dict[str, Any]) -> str:
    name = comp["name"]
    page_name = _label(name)
    page_alias = _alias(name)
    plug_id = ids.next()

    is_form_management = comp["type"] == "form"
    is_dashboard = comp["type"] == "dashboard"

    if is_dashboard:
        inner = f"""
<div class="rt-header">
  <div>
    <h1 class="rt-title">{page_name}</h1>
    <div class="rt-subtitle">Overview and analytics dashboard</div>
  </div>
</div>

<div class="rt-grid">
  <div class="rt-card"><div class="rt-card-label">Total Customers</div><div class="rt-card-value">156</div></div>
  <div class="rt-card"><div class="rt-card-label">Total Orders</div><div class="rt-card-value">248</div></div>
  <div class="rt-card"><div class="rt-card-label">Revenue</div><div class="rt-card-value">$84,200</div></div>
  <div class="rt-card"><div class="rt-card-label">Pending</div><div class="rt-card-value">18</div></div>
</div>

<div class="rt-panel" style="padding:24px;height:320px">
  <h3>Recent Activity</h3>
  <p class="rt-subtitle">Chart area / KPI summary</p>
</div>
"""
    else:
        create_label = "Create"
        lname = name.lower()
        if "customer" in lname:
            create_label = "Add Customer"
        elif "purchase" in lname:
            create_label = "New PO"
        elif "sales" in lname:
            create_label = "New SO"
        elif "order" in lname:
            create_label = "New Order"

        inner = f"""
<div class="rt-header">
  <div>
    <h1 class="rt-title">{page_name}</h1>
    <div class="rt-subtitle">React-style cloned page generated in APEX</div>
  </div>
  {"<button class='rt-btn-primary'>+ " + create_label + "</button>" if is_form_management else ""}
</div>

<div class="rt-grid">
  <div class="rt-card"><div class="rt-card-label">Total</div><div class="rt-card-value">24</div></div>
  <div class="rt-card"><div class="rt-card-label">Active</div><div class="rt-card-value">18</div></div>
  <div class="rt-card"><div class="rt-card-label">Pending</div><div class="rt-card-value">4</div></div>
  <div class="rt-card"><div class="rt-card-label">Completed</div><div class="rt-card-value">12</div></div>
</div>

<div class="rt-panel">
  <div class="rt-toolbar">
    <input class="rt-input" placeholder="Search..." />
    <select class="rt-select"><option>Sort / Filter</option></select>
  </div>
  {_build_table_html(comp)}
</div>

{_build_form_html(comp) if is_form_management else ""}
"""

    html = f"<div class='rt-shell'>{inner}</div>"

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

    out.append("wwv_flow_imp_page.create_page_plug(")
    out.append(f" p_id=>wwv_flow_imp.id({plug_id})")
    out.append(f",p_plug_name=>'{_sanitize(page_name)}'")
    out.append(",p_region_template_options=>'#DEFAULT#'")
    out.append(f",p_plug_template=>{WORKSPACE_TEMPLATE_IDS['REGION_STANDARD']}")
    out.append(",p_plug_display_sequence=>10")
    out.append(f",p_plug_source=>q'~{html}~'")
    out.append(",p_attributes=>wwv_flow_t_plugin_attributes(wwv_flow_t_varchar2(")
    out.append("  'expand_shortcuts', 'N',")
    out.append("  'output_as', 'HTML')).to_clob")
    out.append(");")
    out.append("end;")
    out.append("/")
    return "\n".join(out)


def generate_modal_form_page(ids: IdAllocator, page_id: int, comp: Dict[str, Any]) -> str:
    name = comp["name"]
    fields = comp.get("fields") or ["description", "amount", "status"]
    page_name = "Create " + _label(name)
    page_alias = _alias("Create " + name)

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
    out.append(",p_page_mode=>'MODAL'")
    out.append(",p_autocomplete_on_off=>'OFF'")
    out.append(",p_page_template_options=>'#DEFAULT#'")
    out.append(",p_protection_level=>'C'")
    out.append(",p_page_component_map=>'17'")
    out.append(");")

    out.append("wwv_flow_imp_page.create_page_plug(")
    out.append(f" p_id=>wwv_flow_imp.id({plug_id})")
    out.append(f",p_plug_name=>'{_sanitize(page_name)}'")
    out.append(",p_region_template_options=>'#DEFAULT#'")
    out.append(f",p_plug_template=>{WORKSPACE_TEMPLATE_IDS['REGION_STANDARD']}")
    out.append(",p_plug_display_sequence=>10")
    out.append(",p_location=>null")
    out.append(");")

    seq = 10
    for field in fields[:20]:
        item_id = ids.next()
        display_as = _item_display_as(field)

        out.append("wwv_flow_imp_page.create_page_item(")
        out.append(f" p_id=>wwv_flow_imp.id({item_id})")
        out.append(f",p_name=>'P{page_id}_{field.upper()}'")
        out.append(f",p_item_sequence=>{seq}")
        out.append(f",p_item_plug_id=>wwv_flow_imp.id({plug_id})")
        out.append(f",p_prompt=>'{_sanitize(_label(field))}'")
        out.append(f",p_display_as=>'{display_as}'")
        out.append(",p_cSize=>100")
        out.append(f",p_field_template=>{WORKSPACE_TEMPLATE_IDS['FIELD_TEMPLATE']}")
        out.append(",p_item_template_options=>'#DEFAULT#'")
        out.append(");")
        seq += 10

    out.append("wwv_flow_imp_page.create_page_button(")
    out.append(f" p_id=>wwv_flow_imp.id({save_btn_id})")
    out.append(",p_button_sequence=>10")
    out.append(f",p_button_plug_id=>wwv_flow_imp.id({plug_id})")
    out.append(",p_button_name=>'SAVE'")
    out.append(",p_button_action=>'SUBMIT'")
    out.append(",p_button_template_options=>'#DEFAULT#:t-Button--hot'")
    out.append(f",p_button_template_id=>{WORKSPACE_TEMPLATE_IDS['BUTTON_TEMPLATE']}")
    out.append(",p_button_is_hot=>'Y'")
    out.append(",p_button_image_alt=>'Save'")
    out.append(",p_button_position=>'CHANGE'")
    out.append(");")

    out.append("wwv_flow_imp_page.create_page_button(")
    out.append(f" p_id=>wwv_flow_imp.id({cancel_btn_id})")
    out.append(",p_button_sequence=>20")
    out.append(f",p_button_plug_id=>wwv_flow_imp.id({plug_id})")
    out.append(",p_button_name=>'CANCEL'")
    out.append(",p_button_action=>'DEFINED_BY_DA'")
    out.append(f",p_button_template_id=>{WORKSPACE_TEMPLATE_IDS['BUTTON_TEMPLATE']}")
    out.append(",p_button_image_alt=>'Cancel'")
    out.append(",p_button_position=>'CHANGE'")
    out.append(");")

    # Real APEX close dialog process after submit
    close_id = ids.next()
    out.append("wwv_flow_imp_page.create_page_process(")
    out.append(f" p_id=>wwv_flow_imp.id({close_id})")
    out.append(",p_process_sequence=>30")
    out.append(",p_process_point=>'AFTER_SUBMIT'")
    out.append(",p_process_type=>'NATIVE_CLOSE_WINDOW'")
    out.append(",p_process_name=>'Close Dialog'")
    out.append(f",p_process_when_button_id=>wwv_flow_imp.id({save_btn_id})")
    out.append(");")

    out.append("end;")
    out.append("/")
    return "\n".join(out)


# def generate_styled_report_page(ids: IdAllocator, page_id: int, comp: Dict[str, Any], form_page_id: int) -> str:
#     sql = generate_ir_page(ids, page_id, comp)

#     # Add page CSS class
#     sql = sql.replace(
#         ",p_page_template_options=>'#DEFAULT#'",
#         ",p_page_template_options=>'#DEFAULT#'\n,p_css_classes=>'rt-page'"
#     )

#     # Add Create button redirect to modal page
#     sql = sql.replace(
#         ",p_button_action=>'REDIRECT_PAGE'",
#         ",p_button_action=>'REDIRECT_PAGE'"
#     )

#     sql = sql.replace(
#         ",p_button_alignment=>'RIGHT'",
#         f",p_button_alignment=>'RIGHT'\n,p_button_redirect_url=>'f?p=&APP_ID.:{form_page_id}:&SESSION.::&DEBUG.:RP::'"
#     )

#     return sql

def generate_styled_report_page(ids: IdAllocator, page_id: int, comp: Dict[str, Any], form_page_id: int) -> str:
    sql = generate_ir_page(ids, page_id, comp)

    # Do not add p_css_classes here.
    # Your current APEX import API does not support p_css_classes in create_page.

    sql = sql.replace(
        ",p_button_alignment=>'RIGHT'",
        f",p_button_alignment=>'RIGHT'\n,p_button_redirect_url=>'f?p=&APP_ID.:{form_page_id}:&SESSION.::&DEBUG.:RP::'"
    )

    return sql

# =============================================================================
#   MASTER SCRIPT ASSEMBLY
# =============================================================================

# this is correct Till single page generation with UI
# def generate_sql(parsed: Dict[str, Any], workspace: str, app_id: int, version: str) -> Dict[str, Any]:
#     ids = IdAllocator()
#     release, _ = _release(version)

#     out = []
#     out.append("prompt --application/set_environment")
#     out.append("set define off verify off feedback off")
#     out.append("whenever sqlerror exit sql.sqlcode rollback")
#     out.append("--------------------------------------------------------------------------------")
#     out.append("-- React → Oracle APEX SQL Migration Script")
#     out.append(f"-- Workspace: {workspace}")
#     out.append(f"-- Application ID: {app_id}")
#     out.append(f"-- Target APEX Version: {version} (release {release})")
#     out.append(f"-- Detected components: {len(parsed['components'])}")
#     out.append("--------------------------------------------------------------------------------")
#     out.append("")
#     out.append(_emit_import_begin(workspace, app_id, version))

#     page_summary: List[Dict[str, Any]] = []
#     page_seq = 100
#     for comp in parsed["components"][:40]:

#         page_seq += 1
#         out.append("")

#     # =========================
#     # REPORT PAGE
#     # =========================
#     if comp["type"] == "report":

#         report_page_id = page_seq
#         form_page_id = page_seq + 500

#         out.append(
#             generate_styled_report_page(
#                 ids,
#                 report_page_id,
#                 comp,
#                 form_page_id
#             )
#         )

#         out.append(
#             generate_modal_form_page(
#                 ids,
#                 form_page_id,
#                 comp
#             )
#         )

#         page_summary.append({
#             "page_id": report_page_id,
#             "name": comp["name"],
#             "type": "report",
#             "fields": len(comp.get("fields", [])),
#         })

#         page_summary.append({
#             "page_id": form_page_id,
#             "name": "Create " + comp["name"],
#             "type": "modal_form",
#             "fields": len(comp.get("fields", [])),
#         })

#     # =========================
#     # FORM PAGE
#     # =========================
#     elif comp["type"] == "form":

#         out.append(
#             generate_form_page(
#                 ids,
#                 page_seq,
#                 comp
#             )
#         )

#         page_summary.append({
#             "page_id": page_seq,
#             "name": comp["name"],
#             "type": "form",
#             "fields": len(comp.get("fields", [])),
#         })

#     # =========================
#     # DASHBOARD PAGE
#     # =========================
#     elif comp["type"] == "dashboard":

#         out.append(
#             generate_dashboard_page(
#                 ids,
#                 page_seq,
#                 comp
#             )
#         )

#         page_summary.append({
#             "page_id": page_seq,
#             "name": comp["name"],
#             "type": "dashboard",
#             "fields": 0,
#         })

#     # Static CSS file (in its own block — must be inside an import context)
#     out.append("")
#     out.append("prompt --application/shared_components/files/react_theme")
#     out.append(
#     generate_css_block((parsed.get("css", "") or "")+ "\n"+ REACT_NATIVE_CSS,app_id))

#     out.append("prompt --application/end_environment")
#     out.append(_emit_import_end())
#     out.append("set verify on feedback on define on")
#     out.append("prompt  ...done")

#     sql = "\n".join(out)
#     return {"sql": sql, "pages": page_summary, "component_count": len(parsed["components"])}




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

    page_summary = []
    page_seq = 500

    for comp in parsed["components"][:40]:
        page_seq += 1
        out.append("")

        if comp["type"] == "report":
            report_page_id = page_seq
            form_page_id = page_seq + 500

            out.append(generate_styled_report_page(ids, report_page_id, comp, form_page_id))
            out.append(generate_modal_form_page(ids, form_page_id, comp))

            page_summary.append({
                "page_id": report_page_id,
                "name": comp["name"],
                "type": "report",
                "fields": len(comp.get("fields", [])),
            })

            page_summary.append({
                "page_id": form_page_id,
                "name": "Create " + comp["name"],
                "type": "modal_form",
                "fields": len(comp.get("fields", [])),
            })

        elif comp["type"] == "form":
            out.append(generate_form_page(ids, page_seq, comp))

            page_summary.append({
                "page_id": page_seq,
                "name": comp["name"],
                "type": "form",
                "fields": len(comp.get("fields", [])),
            })

        elif comp["type"] == "dashboard":
            out.append(generate_dashboard_page(ids, page_seq, comp))

            page_summary.append({
                "page_id": page_seq,
                "name": comp["name"],
                "type": "dashboard",
                "fields": 0,
            })

    out.append("")
    out.append("prompt --application/shared_components/files/react_theme")
    out.append(
        generate_css_block(
            (parsed.get("css", "") or "") + "\n" + REACT_NATIVE_CSS,
            app_id
        )
    )

    out.append("prompt --application/end_environment")
    out.append(_emit_import_end())
    out.append("set verify on feedback on define on")
    out.append("prompt  ...done")

    sql = "\n".join(out)

    return {
        "sql": sql,
        "pages": page_summary,
        "component_count": len(parsed["components"])
    }