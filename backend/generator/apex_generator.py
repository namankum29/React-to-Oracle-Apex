# from parser.react_parser import (
#     extract_inputs,
#     extract_buttons
# )

# from generator.region_generator import generate_region
# from generator.item_generator import generate_item
# from generator.button_generator import generate_button


# def generate_apex_page(react_code):

#     sql = ""

#     region_id = 1001

#     sql += generate_region(region_id, "React Converted Form")

#     inputs = extract_inputs(react_code)

#     seq = 10

#     item_id = 2000

#     for inp in inputs:

#         sql += generate_item(
#             item_id,
#             region_id,
#             f"P1_{inp.upper()}",
#             inp.capitalize(),
#             seq
#         )

#         seq += 10
#         item_id += 1

#     buttons = extract_buttons(react_code)

#     button_id = 3000

#     for btn in buttons:

#         sql += generate_button(
#             button_id,
#             region_id,
#             btn.upper().replace(" ", "_"),
#             btn
#         )

#         button_id += 1

#     return sql


from parser.react_parser import (
    extract_inputs,
    extract_buttons
)

from generator.region_generator import generate_region
from generator.item_generator import generate_item
from generator.button_generator import generate_button


def generate_apex_page(react_code):

    sql = ""

    region_id = 1001

    sql += generate_region(
        region_id,
        "New Order"
    )

    # -----------------------------
    # ITEMS
    # -----------------------------

    inputs = extract_inputs(react_code)

    seq = 10
    item_id = 2000

    for inp in inputs:

        sql += generate_item(
            item_id,
            region_id,
            f"P1_{inp.upper()}",
            inp.capitalize(),
            seq
        )

        seq += 10
        item_id += 1

    # -----------------------------
    # FOOTER HTML
    # -----------------------------

    sql += """
begin

htp.p(q'[

</div>

<div class="react-modal-footer">

<button class="react-btn react-btn-secondary">
Cancel
</button>

<button class="react-btn react-btn-primary">
Create Order
</button>

</div>

</div>

</div>

]');

end;
/
"""

    return sql