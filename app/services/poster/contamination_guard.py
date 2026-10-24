"""Lexical & Visual Cross-Industry Contamination Guard.

Enforces strict separation between industries. Ensures that non-coffee businesses
(sneaker stores, dental clinics, salons, gyms, etc.) never inherit coffee terms
("coffee", "brew", "beans", "single-origin", "espresso", "latte", "barista",
"tasting session", "slow pour") or inappropriate motifs.
"""
import re
from typing import Dict, List, Tuple, Set, Any


# Specific prohibited vocabulary per vertical when generated for ANOTHER vertical
INDUSTRY_TOKEN_SETS: Dict[str, Set[str]] = {
    "cafe_coffee": {
        "coffee", "brew", "brewed", "brewing", "cold brew", "coldbrew", "espresso",
        "latte", "cappuccino", "roastery", "roast", "beans", "barista", "pour-over",
        "pourover", "single-origin", "single origin", "tasting session", "artisan selection",
        "slow pour", "glass rim", "crema", "steam stroke", "coffee shop"
    },
    "clinic_healthcare": {
        "dentist", "dental", "teeth", "molar", "orthodontic", "caries", "enamel",
        "surgery", "clinic", "root canal", "invisalign", "cavity", "whitening"
    },
    "sneakers_streetwear": {
        "sneaker", "sneakers", "kicks", "drop", "drops", "colorway", "silhouette",
        "sole", "outsole", "midsole", "hypebeast", "streetwear"
    },
    "auto_detail": {
        "ceramic coating", "paint protection", "detailing", "car wash", "oil change",
        "horsepower", "engine", "chassis", "tachometer"
    }
}


def get_forbidden_tokens_for_vertical(vertical: str) -> Set[str]:
    """Returns all token strings forbidden for the given vertical.
    For instance, any vertical that is NOT cafe_coffee strictly forbids all coffee tokens.
    """
    forbidden = set()
    clean_vert = vertical.lower().replace("-", "_")

    # If NOT coffee, forbid all coffee tokens
    if clean_vert != "cafe_coffee":
        forbidden.update(INDUSTRY_TOKEN_SETS["cafe_coffee"])

    # If NOT clinic, forbid dental/surgery tokens
    if clean_vert != "clinic_healthcare":
        forbidden.update(INDUSTRY_TOKEN_SETS["clinic_healthcare"])

    # If NOT sneakers, forbid sneaker-specific jargon (e.g. kicks, silhouette drop)
    if clean_vert != "sneakers_streetwear":
        forbidden.update(INDUSTRY_TOKEN_SETS["sneakers_streetwear"])

    # If NOT auto, forbid automotive detailing jargon
    if clean_vert != "auto_detail":
        forbidden.update(INDUSTRY_TOKEN_SETS["auto_detail"])

    return forbidden


def check_copy_contamination(text: str, vertical: str) -> Tuple[bool, List[str]]:
    """Checks whether the copy text contains forbidden cross-industry contaminated tokens.
    Returns (is_clean: bool, violations: List[str]).
    """
    if not text:
        return True, []

    forbidden = get_forbidden_tokens_for_vertical(vertical)
    text_lower = text.lower()
    violations = []

    for token in forbidden:
        # Check boundary matches or phrase occurrences
        if " " in token or "-" in token:
            if token in text_lower:
                violations.append(token)
        else:
            if re.search(rf"\b{re.escape(token)}\b", text_lower):
                violations.append(token)

    return (len(violations) == 0, violations)


def clean_copy_of_contamination(text: str, vertical: str, fallback: str = "") -> str:
    """Strips or replaces contaminated terms with clean, vertical-appropriate text."""
    if not text:
        return fallback

    is_clean, violations = check_copy_contamination(text, vertical)
    if is_clean:
        return text

    cleaned = text
    for term in violations:
        cleaned = re.sub(rf"\b{re.escape(term)}\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(re.escape(term), "", cleaned, flags=re.IGNORECASE)

    cleaned = " ".join(cleaned.split()).strip(" :-–—.")
    if not cleaned or len(cleaned) < 3:
        return fallback

    return cleaned


def validate_poster_spec_contamination(spec_dict: Dict[str, Any], vertical: str) -> Tuple[bool, List[str]]:
    """Recursively inspects a complete poster spec (elements, tags, design notes)
    for contaminated cross-industry tokens or visual motifs.
    """
    violations = []
    clean_vert = vertical.lower().replace("-", "_")

    # 1. Text elements inspection
    elements = spec_dict.get("elements", [])
    for el in elements:
        text_val = el.get("text")
        if text_val:
            _, el_violations = check_copy_contamination(text_val, vertical)
            for v in el_violations:
                violations.append(f"Element '{el.get('id', 'unknown')}' contains contaminated term '{v}'")

    # 2. Design notes, reading order, category inspection
    for key in ("design_notes", "self_check", "copy", "tags"):
        item = spec_dict.get(key)
        if isinstance(item, dict):
            for sub_k, sub_v in item.items():
                if isinstance(sub_v, str):
                    _, v_list = check_copy_contamination(sub_v, vertical)
                    for v in v_list:
                        violations.append(f"{key}.{sub_k} contains contaminated term '{v}'")

    # 3. Shape/pattern contamination (e.g. coffee steam in non-coffee designs)
    shapes_patterns = spec_dict.get("shapes_patterns", []) or spec_dict.get("patterns", [])
    if clean_vert != "cafe_coffee":
        for pat in shapes_patterns:
            pat_str = str(pat).lower()
            if any(k in pat_str for k in ("steam", "coffee", "crema", "roast_bean")):
                violations.append(f"Shape/pattern contains coffee motif '{pat}' on non-coffee design")

    return (len(violations) == 0, violations)
