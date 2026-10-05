from typing import List


def alias_for(reseller_id: str) -> str:
    """Generates an operational alias for a reseller ID.

    Example: 'RS019' -> 'ALIAS-19', 'RS006' -> 'ALIAS-06'
    """
    if not reseller_id or len(reseller_id) < 4:
        return "ALIAS-UNKNOWN"
    numeric_part = reseller_id[3:]
    return f"ALIAS-{numeric_part}"


def assert_no_raw_names_leak(text: str, reseller_names: List[str]) -> bool:
    """Returns False if any raw reseller name appears verbatim in text, True otherwise."""
    for name in reseller_names:
        if name and name.strip() in text:
            return False
    return True


if __name__ == "__main__":
    # Internal validation tests
    assert alias_for("RS019") == "ALIAS-19"
    assert alias_for("RS006") == "ALIAS-06"

    known_raw_names = [
        "Mumbai Reseller 1",
        "Mumbai Reseller 4",
        "Hyderabad Reseller 6",
        "Lucknow Reseller 6",
        "Jaipur Reseller 5",
    ]

    safe_narrative = (
        "Top performer ALIAS-19 in West region achieved total spend of ₹75,295.09, "
        "followed by ALIAS-22 at ₹73,882.33."
    )
    leaky_narrative = (
        "Top performer Mumbai Reseller 1 in West region achieved total spend of ₹75,295.09."
    )

    assert assert_no_raw_names_leak(safe_narrative, known_raw_names) is True
    assert assert_no_raw_names_leak(leaky_narrative, known_raw_names) is False
    print("Masking guardrails verified successfully!")