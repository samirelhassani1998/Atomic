# Mapping constants for data normalization

# Event type mapping from Indicateur_principal to standardized event types
EVENT_TYPE_MAPPING = {
    "identification": "IDENTIFICATION",
    "popin": "POPIN_DISPLAYED",
    "primo_identification_popin": "POPIN_DISPLAYED",
    "creation_lien": "LINK_CREATED",
    "validation_lien": "LINK_VALIDATED",
    "suppression_lien": "LINK_DELETED",
}

# Response code normalization (handles accents and variants)
RESPONSE_CODE_MAPPING = {
    "peut-être": "PEUT_ETRE",
    "peut-etre": "PEUT_ETRE",
    "peut etre": "PEUT_ETRE",
    "peutetre": "PEUT_ETRE",
    "association": "ASSOCIATION",
    "refus": "REFUS",
    "close": "CLOSE",
    "fermer": "CLOSE",
}

# Valid universe values
VALID_UNIVERSES = frozenset({"LBP", "LP", "LPM"})

# Auto-detection candidates for measure columns
MEASURE_COLUMN_CANDIDATES = ["valeur", "value", "count", "nb", "volume", "nombre", "qty", "quantity"]

# Auto-detection candidates for date columns
DATE_COLUMN_CANDIDATES = ["date", "periode", "period", "event_date", "jour", "day", "mois", "month"]

# Event type enum values
EVENT_TYPES = frozenset({
    "IDENTIFICATION",
    "POPIN_DISPLAYED",
    "POPIN_RESPONSE",
    "LINK_CREATED",
    "LINK_VALIDATED",
    "LINK_DELETED",
    "OTHER",
})

# Response code enum values
RESPONSE_CODES = frozenset({
    "ASSOCIATION",
    "PEUT_ETRE",
    "REFUS",
    "CLOSE",
})

# Quality flag values
QUALITY_OK = "OK"
QUALITY_WARNING = "WARNING"
QUALITY_ERROR = "ERROR"
