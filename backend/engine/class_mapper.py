from engine.layout_engine import resolve_layout


def map_classes(classes):

    styles = resolve_layout(classes)

    return {
        "classes": classes,
        "styles": styles
    }