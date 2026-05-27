def generate_button(button_id, region_id, name, label):

    return f"""
wwv_flow_imp_page.create_page_button(
    p_id => {button_id},
    p_button_sequence => 10,
    p_button_plug_id => {region_id},

    p_button_name => '{name}',

    p_button_action => 'SUBMIT',

    p_button_template_options =>
    '#DEFAULT#:t-Button--hot',

    p_button_position => 'EDIT',

    p_button_css_classes => 'react-btn',

    p_button_image_alt => '{label}'
);
"""