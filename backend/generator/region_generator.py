# def generate_region(region_id, title):

#     return f"""
# wwv_flow_imp_page.create_page_plug(
#     p_id => {region_id},
#     p_plug_name => '{title}',
#     p_region_template_options => '#DEFAULT#',
#     p_plug_template => 4501440665235496320,
#     p_plug_display_sequence => 10,
#     p_plug_display_point => 'BODY',
#     p_region_css_classes => 'react-card'
# );
# """

from generator.css_generator import get_modal_css


def generate_region(region_id, title):

    return f"""
wwv_flow_imp_page.create_page_plug(
    p_id => {region_id},
    p_plug_name => '{title}',
    p_region_template_options => '#DEFAULT#',
    p_plug_template => 4501440665235496320,
    p_plug_display_sequence => 10,
    p_plug_display_point => 'BODY',
    p_plug_source => q'[
    
    {get_modal_css()}
    
    <div class="react-modal-overlay">

        <div class="react-modal-card">

            <div class="react-modal-header">

                <div class="react-modal-title">
                    {title}
                </div>

                <div class="react-modal-close">
                    ×
                </div>

            </div>

            <div class="react-modal-body">

    ]'
);
"""