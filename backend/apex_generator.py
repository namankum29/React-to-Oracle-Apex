"""Universal React -> Oracle APEX SQL generator.

Generates native APEX pages, regions, page items, buttons, reports and modal forms
from metadata produced by apex_parser.py.
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

.rt-shell{min-height:100vh;background:#f8fafc;font-family:Inter,Arial,sans-serif;padding:32px}
.rt-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:24px}
.rt-title{font-size:28px;font-weight:700;color:#1e293b;margin:0}
.rt-subtitle{font-size:14px;color:#64748b;margin-top:4px}
.rt-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}
.rt-card{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:20px;box-shadow:0 1px 2px rgba(0,0,0,.05)}
.rt-card-label{font-size:12px;color:#64748b;text-transform:uppercase;font-weight:600}
.rt-card-value{font-size:26px;color:#1e293b;font-weight:700;margin-top:6px}
@media(max-width:900px){.rt-grid{grid-template-columns:1fr}.rt-header{flex-direction:column;align-items:flex-start;gap:12px}}
"""


WORKSPACE_TEMPLATE_IDS = {
    "REGION_STANDARD": 4072358936313175081,
    "REGION_IRR": 2100526641005906379,
    "REGION_BREADCRUMB": 2531463326621247859,
    "FIELD_TEMPLATE": 1609121967514267634,
    "BUTTON_TEMPLATE": 2082829544945815391,
    "BUTTON_TEMPLATE_TOP": 4072362960822175091,
    "MENU_ID": 40672399510259321,
    "MENU_TEMPLATE_ID": 4072363345357175094,
}


APEX_VERSION_META = {
    "22.2": ("22.2.0", "2022.10.07"),
    "23.1": ("23.1.0", "2023.04.18"),
    "23.2": ("23.2.0", "2023.10.31"),
    "24.1": ("24.1.0", "2024.05.22"),
    "24.2": ("24.2.0", "2024.11.30"),
    "26.1": ("26.1.0", "2026.04.30"),
}


class IdAllocator:
    def __init__(self):
        self._cur = int(time.time() * 1000) * 100000

    def next(self) -> int:
        self._cur += 1
        return self._cur


def _sanitize(value: Any) -> str:
    return str(value or "").replace("'", "''")


def _label(name: str) -> str:
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", name or "")
    s = s.replace("_", " ").replace("-", " ")
    return " ".join(w.capitalize() for w in s.split())


# def _alias(name: str) -> str:
#     s = re.sub(r"([a-z])([A-Z])", r"\1-\2", name or "")
#     s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").upper()
#     return s[:30] or "PAGE"
def _alias(name: str, page_id: int = None) -> str:
    s = re.sub(r"([a-z])([A-Z])", r"\1-\2", name or "")
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").upper()
    s = s[:24] or "PAGE"

    if page_id:
        return f"{s}-{page_id}"

    return s


def _release(version: str):
    return APEX_VERSION_META.get(version, APEX_VERSION_META["24.2"])


def _base_entity_name(name: str) -> str:
    return name[6:] if name.lower().startswith("report") else name


def _table_name_for(component_name: str) -> str:
    name = _base_entity_name(component_name)
    s = re.sub(r"([a-z])([A-Z])", r"\1_\2", name or "")
    return re.sub(r"[^A-Z0-9_]+", "_", s.upper()).strip("_") or "APP_TABLE"


def _column_type(field: str) -> str:
    f = field.lower()
    if any(k in f for k in ("amount", "price", "qty", "quantity", "count", "age", "phone", "number", "total")):
        return "NUMBER"
    if any(k in f for k in ("date", "dob", "birth", "_at", "time")):
        return "DATE"
    return "STRING"


def _primary_key_field(fields: List[str]) -> str:
    for f in fields:
        fl = f.lower()
        if fl in ("id", "uid", "code") or fl.endswith("_id") or fl.endswith("id"):
            return f
    return "id"


def _fields_from_comp(comp: Dict[str, Any]) -> List[Dict[str, Any]]:
    fields_meta = comp.get("fields_meta") or []
    out = []
    seen = set()

    if fields_meta:
        source = fields_meta
    else:
        source = [
            {"name": f, "label": _label(f), "type": "text", "default": "", "required": False}
            for f in (comp.get("fields") or [])
        ]

    for f in source:
        name = str(f.get("name") or "").strip()
        if not name or name.lower() == "length" or name in seen:
            continue
        seen.add(name)
        out.append({
            "name": name,
            "label": f.get("label") or _label(name),
            "type": f.get("type") or "text",
            "default": f.get("default", ""),
            "required": bool(f.get("required")),
        })

    return out


def _item_display_from_meta(field: Dict[str, Any]) -> str:
    t = (field.get("type") or "text").lower()
    name = (field.get("name") or "").lower()

    # Select lists need LOV metadata; keep text field for stable imports until LOV parser is added.
    if t == "textarea":
        return "NATIVE_TEXTAREA"
    if t == "number" or any(k in name for k in ("amount", "price", "qty", "quantity", "total")):
        return "NATIVE_NUMBER_FIELD"
    if t == "date" or "date" in name:
        return "NATIVE_DATE_PICKER_APEX"
    if t == "password":
        return "NATIVE_PASSWORD"
    return "NATIVE_TEXT_FIELD"


def _required_fields(fields_meta: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    required = []
    for f in fields_meta:
        name = f.get("name", "")
        if f.get("required") or any(k in name.lower() for k in ("name", "email", "code", "title", "no")):
            required.append(f)
    return required[:5]


def _report_columns_from_comp(comp: Dict[str, Any]) -> List[Dict[str, Any]]:
    table_cols = comp.get("table_columns") or []
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    if table_cols:
        return [
            {
                "db_name": c.get("name", f"COL_{i+1}").upper(),
                "label": c.get("label") or _label(c.get("name", f"Column {i+1}")),
                "type": "STRING",
                "order": (i + 1) * 10,
                "ident": letters[i],
            }
            for i, c in enumerate(table_cols[:26])
        ]

    fields = _fields_from_comp(comp)
    if not fields:
        fields = [
            {"name": "id", "label": "Id", "type": "number"},
            {"name": "name", "label": "Name", "type": "text"},
            {"name": "status", "label": "Status", "type": "text"},
        ]

    cols = []
    for i, f in enumerate(fields[:26]):
        name = f["name"]
        cols.append({
            "db_name": name.upper(),
            "label": f.get("label") or _label(name),
            "type": _column_type(name),
            "order": (i + 1) * 10,
            "ident": letters[i],
        })
    return cols


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


def _emit_item(out: List[str], ids: IdAllocator, page_id: int, plug_id: int, field_obj: Dict[str, Any], seq: int):
    field = field_obj["name"]
    item_id = ids.next()
    display_as = _item_display_from_meta(field_obj)

    out.append("wwv_flow_imp_page.create_page_item(")
    out.append(f" p_id=>wwv_flow_imp.id({item_id})")
    out.append(f",p_name=>'P{page_id}_{field.upper()}'")
    out.append(f",p_item_sequence=>{seq}")
    out.append(f",p_item_plug_id=>wwv_flow_imp.id({plug_id})")
    out.append(f",p_prompt=>'{_sanitize(field_obj.get('label') or _label(field))}'")
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


def generate_form_page(ids: IdAllocator, page_id: int, comp: Dict[str, Any]) -> str:
    name = _base_entity_name(comp["name"])
    fields_meta = _fields_from_comp(comp) or [
        {"name": "name", "label": "Name", "type": "text", "required": True},
        {"name": "description", "label": "Description", "type": "textarea", "required": False},
        {"name": "status", "label": "Status", "type": "text", "required": False},
    ]
    fields = [f["name"] for f in fields_meta]
    page_name = comp.get("title") or _label(name)
    page_alias = _alias(name, page_id)

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
    for field_obj in fields_meta[:30]:
        _emit_item(out, ids, page_id, plug_id, field_obj, seq)
        seq += 10

    table_name = _table_name_for(name)
    pk_field = _primary_key_field(fields)
    pk_item = f"P{page_id}_{pk_field.upper()}"

    # Add safe DML scaffold. It imports successfully; actual runtime table must exist.
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

    for req in _required_fields(fields_meta):
        val_id = ids.next()
        req_item = f"P{page_id}_{req['name'].upper()}"
        out.append("wwv_flow_imp_page.create_page_validation(")
        out.append(f" p_id=>wwv_flow_imp.id({val_id})")
        out.append(f",p_validation_name=>'{_sanitize(req.get('label') or _label(req['name']))} Required'")
        out.append(",p_validation_sequence=>10")
        out.append(f",p_validation=>':{req_item} is not null'")
        out.append(",p_validation_type=>'PLSQL_EXPRESSION'")
        out.append(f",p_error_message=>'{_sanitize(req.get('label') or _label(req['name']))} is required.'")
        out.append(",p_error_display_location=>'INLINE_WITH_FIELD_AND_NOTIFICATION'")
        out.append(",p_always_execute=>'N'")
        out.append(");")

    out.append("end;")
    out.append("/")
    return "\n".join(out)


def generate_modal_form_page(ids: IdAllocator, page_id: int, comp: Dict[str, Any]) -> str:
    base_name = _base_entity_name(comp["name"])
    temp_comp = dict(comp)
    temp_comp["name"] = base_name
    temp_comp["title"] = "Create " + _label(base_name)
    sql = generate_form_page(ids, page_id, temp_comp)
    sql = sql.replace(",p_name=>'", ",p_name=>'Create ", 1) if "Create Create" not in sql else sql
    sql = sql.replace(",p_step_title=>'", ",p_step_title=>'Create ", 1) if "Create Create" not in sql else sql
    sql = sql.replace(",p_page_template_options=>'#DEFAULT#'", ",p_page_template_options=>'#DEFAULT#'\n,p_page_mode=>'MODAL'", 1)
    return sql


def generate_ir_page(ids: IdAllocator, page_id: int, comp: Dict[str, Any]) -> str:
    name = comp["name"]
    page_name = comp.get("title") or _label(name)
    page_alias = _alias(name, page_id)
    columns = _report_columns_from_comp(comp)

    plug_id = ids.next()
    ws_id = ids.next()
    rpt_id = ids.next()
    create_btn_id = ids.next()

    select_parts = []
    for c in columns:
        db = c["db_name"]
        if c["type"] == "NUMBER":
            select_parts.append(f"rownum as {db}")
        elif c["type"] == "DATE":
            select_parts.append(f"sysdate - rownum as {db}")
        else:
            select_parts.append(f"'{db}_' || rownum as {db}")
    source_sql = "select " + ", ".join(select_parts) + " from dual connect by level <= 25"
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
        out.append(",p_heading_alignment=>'RIGHT'" if col["type"] == "NUMBER" else ",p_heading_alignment=>'LEFT'")
        if col["type"] == "NUMBER":
            out.append(",p_column_alignment=>'RIGHT'")
        if col["type"] == "DATE":
            out.append(",p_tz_dependent=>'N'")
        out.append(",p_use_as_row_header=>'N'")
        out.append(");")
        column_db_names.append(col["db_name"])

    out.append("wwv_flow_imp_page.create_worksheet_rpt(")
    out.append(f" p_id=>wwv_flow_imp.id({rpt_id})")
    out.append(",p_application_user=>'APXWS_DEFAULT'")
    out.append(",p_report_seq=>10")
    out.append(f",p_report_alias=>'{rpt_id % 1000000}'")
    out.append(",p_status=>'PUBLIC'")
    out.append(",p_is_default=>'Y'")
    out.append(f",p_report_columns=>'{':'.join(column_db_names)}'")
    out.append(");")

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


def generate_styled_report_page(ids: IdAllocator, page_id: int, comp: Dict[str, Any], form_page_id: int) -> str:
    sql = generate_ir_page(ids, page_id, comp)
    sql = sql.replace(
        ",p_button_alignment=>'RIGHT'",
        f",p_button_alignment=>'RIGHT'\n,p_button_redirect_url=>'f?p=&APP_ID.:{form_page_id}:&SESSION.::&DEBUG.:RP::'"
    )
    return sql


def generate_dashboard_page(ids: IdAllocator, page_id: int, comp: Dict[str, Any]) -> str:
    page_name = comp.get("title") or _label(comp["name"])
    page_alias = _alias(comp["name"])
    plug_id = ids.next()

    cards = []
    chart_names = comp.get("charts") or []
    base_cards = ["Total Records", "Active Items", "Pending Items", "Completed Items"]
    for i, label in enumerate(base_cards):
        value = ["248", "156", "18", "74"][i]
        cards.append(
            f'<div class="rt-card"><div class="rt-card-label">{_sanitize(label)}</div><div class="rt-card-value">{value}</div></div>'
        )

    subtitle = "Dashboard Overview"
    if chart_names:
        subtitle = "Charts detected: " + ", ".join(chart_names)

    dashboard_html = (
        '<div class="rt-shell">'
        '<div class="rt-header"><div>'
        f'<h1 class="rt-title">{_sanitize(page_name)}</h1>'
        f'<div class="rt-subtitle">{_sanitize(subtitle)}</div>'
        '</div></div>'
        '<div class="rt-grid">'
        + ''.join(cards) +
        '</div></div>'
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
    page_seq = 500

    for comp in parsed["components"][:40]:
        page_seq += 1
        out.append("")

        if comp["type"] == "report":
            report_page_id = page_seq
            form_page_id = page_seq + 500
            out.append(generate_styled_report_page(ids, report_page_id, comp, form_page_id))
            out.append(generate_modal_form_page(ids, form_page_id, comp))
            page_summary.append({"page_id": report_page_id, "name": comp["name"], "type": "report", "fields": len(comp.get("fields", []))})
            page_summary.append({"page_id": form_page_id, "name": "Create " + _base_entity_name(comp["name"]), "type": "modal_form", "fields": len(comp.get("fields", []))})

        elif comp["type"] == "form":
            out.append(generate_form_page(ids, page_seq, comp))
            page_summary.append({"page_id": page_seq, "name": comp["name"], "type": "form", "fields": len(comp.get("fields", []))})

        elif comp["type"] == "dashboard":
            out.append(generate_dashboard_page(ids, page_seq, comp))
            page_summary.append({"page_id": page_seq, "name": comp["name"], "type": "dashboard", "fields": 0})

    out.append("")
    out.append("prompt --application/shared_components/files/react_theme")
    out.append(generate_css_block((parsed.get("css", "") or "") + "\n" + REACT_NATIVE_CSS, app_id))
    out.append("prompt --application/end_environment")
    out.append(_emit_import_end())
    out.append("set verify on feedback on define on")
    out.append("prompt  ...done")

    sql = "\n".join(out)
    return {"sql": sql, "pages": page_summary, "component_count": len(parsed["components"])}
