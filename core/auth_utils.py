def normalize_username(value):
    value = (value or '').strip()
    if not value:
        return value
    normalized = []
    for char in value:
        if char.isalnum() or char in {'-', '_'}:
            normalized.append(char)
        else:
            normalized.append('-')
    return ''.join(normalized).strip('-')
