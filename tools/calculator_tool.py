def calculate_percentage(part: float, whole: float) -> float:
    if whole == 0:
        raise ValueError("whole must not be zero")
    return (part / whole) * 100

