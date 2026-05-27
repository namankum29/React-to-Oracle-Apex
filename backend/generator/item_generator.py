def generate_item(item_id, region_id, item_name, label, sequence, item_type="TEXT"):

    display_as = "NATIVE_TEXT_FIELD"

    if item_type == "NUMBER":
        display_as = "NATIVE_NUMBER_FIELD"

    if item_type == "SELECT":
        display_as = "NATIVE_SELECT_LIST"

    return f"""
wwv_flow_imp_page.create_page_item(
    p_id => {item_id},
    p_name => '{item_name}',
    p_item_sequence => {sequence},
    p_item_plug_id => {region_id},
    p_prompt => '{label}',
    p_display_as => '{display_as}',
    p_cSize => 100,
    p_cMaxlength => 4000,
    p_field_template => 4501445636535496330,
    p_item_css_classes => 'react-input',
    p_grid_label_column_span => 12,
    p_grid_column_span => 12,
    p_grid_new_row => 'Y',
    p_grid_new_column => 'N',
    p_item_template_options => '#DEFAULT#'
);
"""