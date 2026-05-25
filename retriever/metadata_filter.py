def metadata_matches(
    candidate: dict[str, str | int | float | None],
    required: dict[str, str | int | float | None],
) -> bool:
    for key, value in required.items():
        if value is None:
            continue
        if str(candidate.get(key, "")).casefold() != str(value).casefold():
            return False
    return True

