LAYOUT_CLASSES = {
    "flex": {
        "display": "flex"
    },

    "flex-col": {
        "flex-direction": "column"
    },

    "flex-row": {
        "flex-direction": "row"
    },

    "grid": {
        "display": "grid"
    },

    "items-center": {
        "align-items": "center"
    },

    "justify-between": {
        "justify-content": "space-between"
    },

    "gap-2": {
        "gap": "0.5rem"
    },

    "gap-4": {
        "gap": "1rem"
    },

    "p-4": {
        "padding": "1rem"
    },

    "p-6": {
        "padding": "1.5rem"
    },

    "rounded-xl": {
        "border-radius": "1rem"
    },

    "shadow-lg": {
        "box-shadow": "0 10px 15px rgba(0,0,0,0.1)"
    }
}


def resolve_layout(classes):

    styles = {}

    for cls in classes:

        if cls in LAYOUT_CLASSES:
            styles.update(LAYOUT_CLASSES[cls])

    return styles