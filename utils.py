def format_amount(value):
    try:
        value = float(value.replace(",", ""))
        return f"{value:,.2f}"
    except:
        return "0.00"


def parse_amount(value):
    try:
        return float(value.replace(",", ""))
    except:
        return 0.0