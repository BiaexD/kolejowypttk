import re

import requests

NOMINATIM_USER_AGENT = "kolejowypttk-site/1.0 (kontakt@kolejowy.pttk.pl)"

# "ul./al./pl./os." na początku adresu bywa niepoprawnie odczytywane przez
# Nominatim i potrafi zwrócić zero wyników dla poprawnego adresu.
_ADDRESS_PREFIX_RE = re.compile(r'^\s*(ul\.?|al\.?|pl\.?|os\.?)\s+', re.IGNORECASE)


def geocode_address(address):
    """Zwraca (lat, lng) dla adresu tekstowego albo None, jeśli nie znaleziono."""
    if not address or not address.strip():
        return None

    query = _ADDRESS_PREFIX_RE.sub('', address.strip())
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"format": "json", "q": query, "countrycodes": "pl", "limit": 1},
            headers={"User-Agent": NOMINATIM_USER_AGENT},
            timeout=8,
        )
        response.raise_for_status()
        results = response.json()
    except (requests.RequestException, ValueError):
        return None

    if not results:
        return None
    return float(results[0]["lat"]), float(results[0]["lon"])
