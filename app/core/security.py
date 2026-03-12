import secrets


def api_key_matches(provided_key: str, expected_key: str) -> bool:
    if not provided_key or not expected_key:
        return False
    return secrets.compare_digest(provided_key, expected_key)
