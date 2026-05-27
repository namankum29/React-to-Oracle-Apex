# import re
# from bs4 import BeautifulSoup


# def extract_classnames(code):
#     pattern = r'className="([^"]+)"'
#     matches = re.findall(pattern, code)

#     classes = []

#     for match in matches:
#         classes.extend(match.split())

#     return list(set(classes))


# def extract_inputs(code):
#     pattern = r'<input[^>]*name=["\']([^"\']+)["\']'
#     return re.findall(pattern, code)


# def extract_buttons(code):
#     pattern = r'<button[^>]*>(.*?)</button>'
#     return re.findall(pattern, code, re.DOTALL)


# def detect_layout(code):

#     if "grid-cols-2" in code:
#         return "2_COLUMN"

#     if "grid-cols-3" in code:
#         return "3_COLUMN"

#     if "flex" in code:
#         return "FLEX"

#     return "SINGLE"




import re
from bs4 import BeautifulSoup


# -----------------------------------
# CLASSNAME EXTRACTION
# -----------------------------------

CLASSNAME_RE = re.compile(
    r'className\s*=\s*["\']([^"\']+)["\']'
)


def extract_classnames(code):

    classes = set()

    for match in CLASSNAME_RE.findall(code):

        for cls in match.split():

            cls = cls.strip()

            if cls:
                classes.add(cls)

    return list(classes)


# -----------------------------------
# INPUT EXTRACTION
# -----------------------------------

INPUT_RE = re.compile(
    r'<input[^>]*name=["\']([^"\']+)["\']',
    re.IGNORECASE
)


def extract_inputs(code):

    return INPUT_RE.findall(code)


# -----------------------------------
# BUTTON EXTRACTION
# -----------------------------------

BUTTON_RE = re.compile(
    r'<button[^>]*>(.*?)</button>',
    re.IGNORECASE | re.DOTALL
)


def extract_buttons(code):

    buttons = []

    for btn in BUTTON_RE.findall(code):

        clean = re.sub(r"<.*?>", "", btn).strip()

        if clean:
            buttons.append(clean)

    return buttons


# -----------------------------------
# LAYOUT DETECTION
# -----------------------------------

def detect_layout(code):

    if "grid-cols-4" in code:
        return "4_COLUMN"

    if "grid-cols-3" in code:
        return "3_COLUMN"

    if "grid-cols-2" in code:
        return "2_COLUMN"

    if "flex-col" in code:
        return "FLEX_COLUMN"

    if "flex-row" in code:
        return "FLEX_ROW"

    if "flex" in code:
        return "FLEX"

    return "SINGLE"


# -----------------------------------
# CARD DETECTION
# -----------------------------------

def detect_cards(code):

    card_patterns = [
        "rounded-xl",
        "rounded-lg",
        "shadow-lg",
        "shadow-md",
        "bg-white"
    ]

    score = 0

    for pattern in card_patterns:

        if pattern in code:
            score += 1

    return score >= 2


# -----------------------------------
# TABLE DETECTION
# -----------------------------------

def detect_table(code):

    return "<table" in code.lower()


# -----------------------------------
# CHART DETECTION
# -----------------------------------

def detect_chart(code):

    chart_keywords = [
        "LineChart",
        "BarChart",
        "PieChart",
        "AreaChart"
    ]

    for chart in chart_keywords:

        if chart in code:
            return True

    return False


# -----------------------------------
# FULL PAGE ANALYSIS
# -----------------------------------

def analyze_react_code(code):

    return {

        "classnames": extract_classnames(code),

        "inputs": extract_inputs(code),

        "buttons": extract_buttons(code),

        "layout": detect_layout(code),

        "has_cards": detect_cards(code),

        "has_table": detect_table(code),

        "has_chart": detect_chart(code)
    }