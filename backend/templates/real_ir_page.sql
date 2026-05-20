prompt --application/set_environment
set define off verify off feedback off
whenever sqlerror exit sql.sqlcode rollback
--------------------------------------------------------------------------------
--
-- Oracle APEX export file
--
-- You should run this script using a SQL client connected to the database as
-- the owner (parsing schema) of the application or as a database user with the
-- APEX_ADMINISTRATOR_ROLE role.
--
-- This export file has been automatically generated. Modifying this file is not
-- supported by Oracle and can lead to unexpected application and/or instance
-- behavior now or in the future.
--
-- NOTE: Calls to apex_application_install override the defaults below.
--
--------------------------------------------------------------------------------
begin
wwv_flow_imp.import_begin (
 p_version_yyyy_mm_dd=>'2024.11.30'
,p_release=>'24.2.0'
,p_default_workspace_id=>39775583738945003
,p_default_application_id=>109
,p_default_id_offset=>0
,p_default_owner=>'MAKESS'
);
end;
/
 
prompt APPLICATION 109 - Test for export
--
-- Application Export:
--   Application:     109
--   Name:            Test for export
--   Exported By:     NAMAN1
--   Flashback:       0
--   Export Type:     Page Export
--   Manifest
--     PAGE: 3
--   Manifest End
--   Version:         24.2.0
--   Instance ID:     743386619493800
--

begin
null;
end;
/
prompt --application/pages/delete_00003
begin
wwv_flow_imp_page.remove_page (p_flow_id=>wwv_flow.g_flow_id, p_page_id=>3);
end;
/
prompt --application/pages/page_00003
begin
wwv_flow_imp_page.create_page(
 p_id=>3
,p_name=>'Report test'
,p_alias=>'REPORT-TEST'
,p_step_title=>'Report test'
,p_autocomplete_on_off=>'OFF'
,p_page_template_options=>'#DEFAULT#'
,p_protection_level=>'C'
,p_page_component_map=>'18'
);
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id(40688602795264407)
,p_plug_name=>'Data'
,p_title=>'Data'
,p_region_template_options=>'#DEFAULT#:t-IRR-region--hideHeader js-addHiddenHeadingRoleDesc'
,p_component_template_options=>'#DEFAULT#'
,p_plug_template=>2100526641005906379
,p_plug_display_sequence=>10
,p_query_type=>'TABLE'
,p_query_owner=>'PRODUCTION'
,p_query_table=>'DT_BULKPROD_EXE'
,p_include_rowid_column=>false
,p_plug_source_type=>'NATIVE_IR'
,p_prn_content_disposition=>'ATTACHMENT'
,p_prn_units=>'INCHES'
,p_prn_paper_size=>'LETTER'
,p_prn_width=>11
,p_prn_height=>8.5
,p_prn_orientation=>'HORIZONTAL'
,p_prn_page_header=>'Data'
,p_prn_page_header_font_color=>'#000000'
,p_prn_page_header_font_family=>'Helvetica'
,p_prn_page_header_font_weight=>'normal'
,p_prn_page_header_font_size=>'12'
,p_prn_page_footer_font_color=>'#000000'
,p_prn_page_footer_font_family=>'Helvetica'
,p_prn_page_footer_font_weight=>'normal'
,p_prn_page_footer_font_size=>'12'
,p_prn_header_bg_color=>'#EEEEEE'
,p_prn_header_font_color=>'#000000'
,p_prn_header_font_family=>'Helvetica'
,p_prn_header_font_weight=>'bold'
,p_prn_header_font_size=>'10'
,p_prn_body_bg_color=>'#FFFFFF'
,p_prn_body_font_color=>'#000000'
,p_prn_body_font_family=>'Helvetica'
,p_prn_body_font_weight=>'normal'
,p_prn_body_font_size=>'10'
,p_prn_border_width=>.5
,p_prn_page_header_alignment=>'CENTER'
,p_prn_page_footer_alignment=>'CENTER'
,p_prn_border_color=>'#666666'
);
wwv_flow_imp_page.create_worksheet(
 p_id=>wwv_flow_imp.id(40688713911264408)
,p_max_row_count=>'1000000'
,p_pagination_type=>'ROWS_X_TO_Y'
,p_pagination_display_pos=>'BOTTOM_RIGHT'
,p_report_list_mode=>'TABS'
,p_lazy_loading=>false
,p_show_detail_link=>'N'
,p_show_notify=>'Y'
,p_download_formats=>'CSV:HTML:XLSX:PDF'
,p_enable_mail_download=>'Y'
,p_owner=>'NAMAN1'
,p_internal_uid=>40688713911264408
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40688878152264409)
,p_db_column_name=>'VC_COMP_CODE'
,p_display_order=>10
,p_column_identifier=>'A'
,p_column_label=>'Vc Comp Code'
,p_column_type=>'STRING'
,p_heading_alignment=>'LEFT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40688950914264410)
,p_db_column_name=>'NU_AREA_CODE'
,p_display_order=>20
,p_column_identifier=>'B'
,p_column_label=>'Nu Area Code'
,p_column_type=>'NUMBER'
,p_heading_alignment=>'RIGHT'
,p_column_alignment=>'RIGHT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40689045175264411)
,p_db_column_name=>'VC_BULKEXE_NO'
,p_display_order=>30
,p_column_identifier=>'C'
,p_column_label=>'Vc Bulkexe No'
,p_column_type=>'STRING'
,p_heading_alignment=>'LEFT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40689171400264412)
,p_db_column_name=>'DT_BULKEXE_DATE'
,p_display_order=>40
,p_column_identifier=>'D'
,p_column_label=>'Dt Bulkexe Date'
,p_column_type=>'DATE'
,p_heading_alignment=>'LEFT'
,p_tz_dependent=>'N'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40689228457264413)
,p_db_column_name=>'VC_MPS_NO'
,p_display_order=>50
,p_column_identifier=>'E'
,p_column_label=>'Vc Mps No'
,p_column_type=>'STRING'
,p_heading_alignment=>'LEFT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40689364061264414)
,p_db_column_name=>'DT_MPS_DATE'
,p_display_order=>60
,p_column_identifier=>'F'
,p_column_label=>'Dt Mps Date'
,p_column_type=>'DATE'
,p_heading_alignment=>'LEFT'
,p_tz_dependent=>'N'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40689456632264415)
,p_db_column_name=>'VC_JOB_CARD_NO'
,p_display_order=>70
,p_column_identifier=>'G'
,p_column_label=>'Vc Job Card No'
,p_column_type=>'STRING'
,p_heading_alignment=>'LEFT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40689515920264416)
,p_db_column_name=>'DT_JOB_DATE'
,p_display_order=>80
,p_column_identifier=>'H'
,p_column_label=>'Dt Job Date'
,p_column_type=>'DATE'
,p_heading_alignment=>'LEFT'
,p_tz_dependent=>'N'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40689671817264417)
,p_db_column_name=>'VC_PROCESS_CODE'
,p_display_order=>90
,p_column_identifier=>'I'
,p_column_label=>'Vc Process Code'
,p_column_type=>'STRING'
,p_heading_alignment=>'LEFT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40689768522264418)
,p_db_column_name=>'VC_SHIFT_CODE'
,p_display_order=>100
,p_column_identifier=>'J'
,p_column_label=>'Vc Shift Code'
,p_column_type=>'STRING'
,p_heading_alignment=>'LEFT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40689885619264419)
,p_db_column_name=>'VC_MACHINE_CODE'
,p_display_order=>110
,p_column_identifier=>'K'
,p_column_label=>'Vc Machine Code'
,p_column_type=>'STRING'
,p_heading_alignment=>'LEFT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40689993841264420)
,p_db_column_name=>'VC_MOULD_NO'
,p_display_order=>120
,p_column_identifier=>'L'
,p_column_label=>'Vc Mould No'
,p_column_type=>'STRING'
,p_heading_alignment=>'LEFT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40690035419264421)
,p_db_column_name=>'VC_PRODUCT_CODE'
,p_display_order=>130
,p_column_identifier=>'M'
,p_column_label=>'Vc Product Code'
,p_column_type=>'STRING'
,p_heading_alignment=>'LEFT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40690185993264422)
,p_db_column_name=>'NU_QTY_PLANNED'
,p_display_order=>140
,p_column_identifier=>'N'
,p_column_label=>'Nu Qty Planned'
,p_column_type=>'NUMBER'
,p_heading_alignment=>'RIGHT'
,p_column_alignment=>'RIGHT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40690220322264423)
,p_db_column_name=>'NU_QTY_PRODUCED'
,p_display_order=>150
,p_column_identifier=>'O'
,p_column_label=>'Nu Qty Produced'
,p_column_type=>'NUMBER'
,p_heading_alignment=>'RIGHT'
,p_column_alignment=>'RIGHT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40690302960264424)
,p_db_column_name=>'NU_QTY_REJECTED'
,p_display_order=>160
,p_column_identifier=>'P'
,p_column_label=>'Nu Qty Rejected'
,p_column_type=>'NUMBER'
,p_heading_alignment=>'RIGHT'
,p_column_alignment=>'RIGHT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40690458590264425)
,p_db_column_name=>'NU_WEIGHT'
,p_display_order=>170
,p_column_identifier=>'Q'
,p_column_label=>'Nu Weight'
,p_column_type=>'NUMBER'
,p_heading_alignment=>'RIGHT'
,p_column_alignment=>'RIGHT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40690506214264426)
,p_db_column_name=>'NU_LENGTH'
,p_display_order=>180
,p_column_identifier=>'R'
,p_column_label=>'Nu Length'
,p_column_type=>'NUMBER'
,p_heading_alignment=>'RIGHT'
,p_column_alignment=>'RIGHT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40690611845264427)
,p_db_column_name=>'VC_BATCH_NO'
,p_display_order=>190
,p_column_identifier=>'S'
,p_column_label=>'Vc Batch No'
,p_column_type=>'STRING'
,p_heading_alignment=>'LEFT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40690784883264428)
,p_db_column_name=>'DT_MFG_DATE'
,p_display_order=>200
,p_column_identifier=>'T'
,p_column_label=>'Dt Mfg Date'
,p_column_type=>'DATE'
,p_heading_alignment=>'LEFT'
,p_tz_dependent=>'N'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40690832039264429)
,p_db_column_name=>'DT_EXPIRY_DATE'
,p_display_order=>210
,p_column_identifier=>'U'
,p_column_label=>'Dt Expiry Date'
,p_column_type=>'DATE'
,p_heading_alignment=>'LEFT'
,p_tz_dependent=>'N'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40690934200264430)
,p_db_column_name=>'VC_OPERATOR_ID'
,p_display_order=>220
,p_column_identifier=>'V'
,p_column_label=>'Vc Operator Id'
,p_column_type=>'STRING'
,p_heading_alignment=>'LEFT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40691097390264431)
,p_db_column_name=>'DT_START_TIME'
,p_display_order=>230
,p_column_identifier=>'W'
,p_column_label=>'Dt Start Time'
,p_column_type=>'DATE'
,p_heading_alignment=>'LEFT'
,p_tz_dependent=>'N'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40691136418264432)
,p_db_column_name=>'DT_END_TIME'
,p_display_order=>240
,p_column_identifier=>'X'
,p_column_label=>'Dt End Time'
,p_column_type=>'DATE'
,p_heading_alignment=>'LEFT'
,p_tz_dependent=>'N'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40691280156264433)
,p_db_column_name=>'VC_BOM_NO'
,p_display_order=>250
,p_column_identifier=>'Y'
,p_column_label=>'Vc Bom No'
,p_column_type=>'STRING'
,p_heading_alignment=>'LEFT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40691383291264434)
,p_db_column_name=>'DT_BOM_DATE'
,p_display_order=>260
,p_column_identifier=>'Z'
,p_column_label=>'Dt Bom Date'
,p_column_type=>'DATE'
,p_heading_alignment=>'LEFT'
,p_tz_dependent=>'N'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40691410352264435)
,p_db_column_name=>'CH_STATUS'
,p_display_order=>270
,p_column_identifier=>'AA'
,p_column_label=>'Ch Status'
,p_column_type=>'STRING'
,p_heading_alignment=>'LEFT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40691578130264436)
,p_db_column_name=>'VC_LOT_STRING'
,p_display_order=>280
,p_column_identifier=>'AB'
,p_column_label=>'Vc Lot String'
,p_column_type=>'STRING'
,p_heading_alignment=>'LEFT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40691603620264437)
,p_db_column_name=>'VC_INPUT_STRING'
,p_display_order=>290
,p_column_identifier=>'AC'
,p_column_label=>'Vc Input String'
,p_column_type=>'STRING'
,p_heading_alignment=>'LEFT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40691776839264438)
,p_db_column_name=>'VC_DOWNTIME_STRING'
,p_display_order=>300
,p_column_identifier=>'AD'
,p_column_label=>'Vc Downtime String'
,p_column_type=>'STRING'
,p_heading_alignment=>'LEFT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40691885100264439)
,p_db_column_name=>'DT_CRT_DATE'
,p_display_order=>310
,p_column_identifier=>'AE'
,p_column_label=>'Dt Crt Date'
,p_column_type=>'DATE'
,p_heading_alignment=>'LEFT'
,p_tz_dependent=>'N'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40691999250264440)
,p_db_column_name=>'VC_AUTH_CODE'
,p_display_order=>320
,p_column_identifier=>'AF'
,p_column_label=>'Vc Auth Code'
,p_column_type=>'STRING'
,p_heading_alignment=>'LEFT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40692006501264441)
,p_db_column_name=>'VC_CRT_CODE'
,p_display_order=>330
,p_column_identifier=>'AG'
,p_column_label=>'Vc Crt Code'
,p_column_type=>'STRING'
,p_heading_alignment=>'LEFT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40692179469264442)
,p_db_column_name=>'NU_PROD_WT'
,p_display_order=>340
,p_column_identifier=>'AH'
,p_column_label=>'Nu Prod Wt'
,p_column_type=>'NUMBER'
,p_heading_alignment=>'RIGHT'
,p_column_alignment=>'RIGHT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40692273707264443)
,p_db_column_name=>'VC_PROD_ADV_NO'
,p_display_order=>350
,p_column_identifier=>'AI'
,p_column_label=>'Vc Prod Adv No'
,p_column_type=>'STRING'
,p_heading_alignment=>'LEFT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40692384183264444)
,p_db_column_name=>'DT_PROD_ADV_DATE'
,p_display_order=>360
,p_column_identifier=>'AJ'
,p_column_label=>'Dt Prod Adv Date'
,p_column_type=>'DATE'
,p_heading_alignment=>'LEFT'
,p_tz_dependent=>'N'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40692414485264445)
,p_db_column_name=>'NU_R_AREA_CODE'
,p_display_order=>370
,p_column_identifier=>'AK'
,p_column_label=>'Nu R Area Code'
,p_column_type=>'NUMBER'
,p_heading_alignment=>'RIGHT'
,p_column_alignment=>'RIGHT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40692574066264446)
,p_db_column_name=>'NU_TOT_CONSUMPTION'
,p_display_order=>380
,p_column_identifier=>'AL'
,p_column_label=>'Nu Tot Consumption'
,p_column_type=>'NUMBER'
,p_heading_alignment=>'RIGHT'
,p_column_alignment=>'RIGHT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40692699240264447)
,p_db_column_name=>'NU_TOT_OVERHEAD'
,p_display_order=>390
,p_column_identifier=>'AM'
,p_column_label=>'Nu Tot Overhead'
,p_column_type=>'NUMBER'
,p_heading_alignment=>'RIGHT'
,p_column_alignment=>'RIGHT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40692758880264448)
,p_db_column_name=>'NU_TOT_PRODUCTION'
,p_display_order=>400
,p_column_identifier=>'AN'
,p_column_label=>'Nu Tot Production'
,p_column_type=>'NUMBER'
,p_heading_alignment=>'RIGHT'
,p_column_alignment=>'RIGHT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40692805920264449)
,p_db_column_name=>'NU_OUTPUT_COST'
,p_display_order=>410
,p_column_identifier=>'AO'
,p_column_label=>'Nu Output Cost'
,p_column_type=>'NUMBER'
,p_heading_alignment=>'RIGHT'
,p_column_alignment=>'RIGHT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(40692949290264450)
,p_db_column_name=>'CH_ITEM_FLAG'
,p_display_order=>420
,p_column_identifier=>'AP'
,p_column_label=>'Ch Item Flag'
,p_column_type=>'STRING'
,p_heading_alignment=>'LEFT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_column(
 p_id=>wwv_flow_imp.id(41368350108891101)
,p_db_column_name=>'NU_WASTE_QTY'
,p_display_order=>430
,p_column_identifier=>'AQ'
,p_column_label=>'Nu Waste Qty'
,p_column_type=>'NUMBER'
,p_heading_alignment=>'RIGHT'
,p_column_alignment=>'RIGHT'
,p_use_as_row_header=>'N'
);
wwv_flow_imp_page.create_worksheet_rpt(
 p_id=>wwv_flow_imp.id(41387008697891711)
,p_application_user=>'APXWS_DEFAULT'
,p_report_seq=>10
,p_report_alias=>'413871'
,p_status=>'PUBLIC'
,p_is_default=>'Y'
,p_report_columns=>'VC_COMP_CODE:NU_AREA_CODE:VC_BULKEXE_NO:DT_BULKEXE_DATE:VC_MPS_NO:DT_MPS_DATE:VC_JOB_CARD_NO:DT_JOB_DATE:VC_PROCESS_CODE:VC_SHIFT_CODE:VC_MACHINE_CODE:VC_MOULD_NO:VC_PRODUCT_CODE:NU_QTY_PLANNED:NU_QTY_PRODUCED:NU_QTY_REJECTED:NU_WEIGHT:NU_LENGTH:VC_B'
||'ATCH_NO:DT_MFG_DATE:DT_EXPIRY_DATE:VC_OPERATOR_ID:DT_START_TIME:DT_END_TIME:VC_BOM_NO:DT_BOM_DATE:CH_STATUS:VC_LOT_STRING:VC_INPUT_STRING:VC_DOWNTIME_STRING:DT_CRT_DATE:VC_AUTH_CODE:VC_CRT_CODE:NU_PROD_WT:VC_PROD_ADV_NO:DT_PROD_ADV_DATE:NU_R_AREA_COD'
||'E:NU_TOT_CONSUMPTION:NU_TOT_OVERHEAD:NU_TOT_PRODUCTION:NU_OUTPUT_COST:CH_ITEM_FLAG:NU_WASTE_QTY'
);
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id(41367693945886434)
,p_plug_name=>'Breadcrumb'
,p_region_template_options=>'#DEFAULT#:t-BreadcrumbRegion--useBreadcrumbTitle'
,p_component_template_options=>'#DEFAULT#'
,p_plug_template=>2531463326621247859
,p_plug_display_sequence=>10
,p_plug_display_point=>'REGION_POSITION_01'
,p_menu_id=>wwv_flow_imp.id(40672399510259321)
,p_plug_source_type=>'NATIVE_BREADCRUMB'
,p_menu_template_id=>4072363345357175094
);
wwv_flow_imp_page.create_page_button(
 p_id=>wwv_flow_imp.id(41368493929891102)
,p_button_sequence=>10
,p_button_plug_id=>wwv_flow_imp.id(40688602795264407)
,p_button_name=>'CREATE'
,p_button_action=>'REDIRECT_PAGE'
,p_button_template_options=>'#DEFAULT#'
,p_button_template_id=>4072362960822175091
,p_button_is_hot=>'Y'
,p_button_image_alt=>'Create'
,p_button_position=>'TOP'
,p_button_alignment=>'RIGHT'
,p_button_redirect_url=>'f?p=&APP_ID.:2:&SESSION.::&DEBUG.:2::'
);
end;
/
prompt --application/end_environment
begin
wwv_flow_imp.import_end(p_auto_install_sup_obj => nvl(wwv_flow_application_install.get_auto_install_sup_obj, false)
);
commit;
end;
/
set verify on feedback on define on
prompt  ...done
