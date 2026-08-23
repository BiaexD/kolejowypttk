import re

import requests
from django.conf import settings

NOMINATIM_USER_AGENT = "kolejowypttk-site/1.0 (kontakt@kolejowy.pttk.pl)"

ORS_PROFILES = {
    "foot-walking": "foot-walking",
    "cycling-regular": "cycling-regular",
    "driving-car": "driving-car",
}

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


def get_route(start_lat, start_lng, end_lat, end_lng, profile):
    """Zwraca trasę z OpenRouteService albo None, jeśli nie udało się jej wyznaczyć.

    Wynik: {"geometry": [[lat, lng], ...], "distance_km": float, "duration_min": float}
    """
    if profile not in ORS_PROFILES:
        return None
    if not settings.ORS_API_KEY:
        return None

    try:
        response = requests.post(
            f"https://api.openrouteservice.org/v2/directions/{profile}/geojson",
            json={"coordinates": [[start_lng, start_lat], [end_lng, end_lat]]},
            headers={
                "Authorization": settings.ORS_API_KEY,
                "Content-Type": "application/json",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return None

    features = data.get("features") or []
    if not features:
        return None

    feature = features[0]
    coords = feature.get("geometry", {}).get("coordinates") or []
    summary = feature.get("properties", {}).get("summary") or {}
    if not coords or "distance" not in summary or "duration" not in summary:
        return None

    return {
        "geometry": [[lat, lng] for lng, lat in coords],
        "distance_km": round(summary["distance"] / 1000, 1),
        "duration_min": round(summary["duration"] / 60),
    }
