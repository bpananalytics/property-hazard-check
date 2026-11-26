# Every FEMA zone that counts as High risk
HIGH_ZONES = {"A", "AE", "AH", "AO", "AR", "A99", "V", "VE"}


def flood_tier(zone, subtype=None):
    """Turn a FEMA flood zone into High / Moderate / Low / Unknown."""
    if zone is None:
        return "Unknown"                 # no FEMA data

    zone = zone.strip().upper()          # tidy the input: " ae " becomes "AE"

    if zone in HIGH_ZONES:
        return "High"

    if zone == "X":
        sub = (subtype or "").upper()
        if "0.2 PCT" in sub or "LEVEE" in sub:
            return "Moderate"            # shaded X
        if "MINIMAL" in sub:
            return "Low"                 # unshaded X
        return "Unknown"                 # X, but we can't tell which kind

    return "Unknown"                     # D, or any code we don't recognize
