import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

# Statutory watchlists conformant with MHA (UAPA), UNSCR 1267, and Indian PEP regulations
STATUTORY_WATCHLIST = [
    {
        "id": "UN-SANCT-091",
        "name": "Dawood Ibrahim Kaskar",
        "aliases": ["Dawood Ebrahim", "Sheikh Dawood Hassan", "Bada Rajan"],
        "category": "SANCTIONED_TERROR",
        "regime": "UNSCR 1267 / MHA UAPA",
        "risk_severity": "critical",
    },
    {
        "id": "MHA-UAPA-104",
        "name": "Hafiz Muhammad Saeed",
        "aliases": ["Hafiz Saeed", "Talha Saeed"],
        "category": "SANCTIONED_TERROR",
        "regime": "MHA Fourth Schedule UAPA",
        "risk_severity": "critical",
    },
    {
        "id": "PEP-IND-401",
        "name": "Vijay Vittal Mallya",
        "aliases": ["Vijay Mallya", "V Mallya"],
        "category": "FUGITIVE_ECONOMIC_OFFENDER",
        "regime": "FEOA 2018 / CBI / ED",
        "risk_severity": "critical",
    },
    {
        "id": "PEP-IND-402",
        "name": "Nirav Deepak Modi",
        "aliases": ["Nirav Modi"],
        "category": "FUGITIVE_ECONOMIC_OFFENDER",
        "regime": "FEOA 2018 / PMLA",
        "risk_severity": "critical",
    },
    {
        "id": "PEP-DOM-701",
        "name": "Suresh Kalmadi",
        "aliases": ["S Kalmadi"],
        "category": "PEP",
        "regime": "Domestic PEP Registry",
        "risk_severity": "high",
    },
]


def normalize_name(name: str) -> str:
    """Sanitizes prefixes, titles, punctuation, and extraneous spaces."""
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", name.lower())
    prefixes_and_titles = {
        "usr", "user", "acc", "account", "id", "shri", "smt",
        "dr", "mr", "mrs", "ms", "sheikh", "syed",
    }
    tokens = [t for t in cleaned.split() if t not in prefixes_and_titles]
    return " ".join(tokens)


def string_similarity(s1: str, s2: str) -> float:
    return SequenceMatcher(None, s1, s2).ratio()


class WatchlistEngine:
    def __init__(self, match_threshold: float = 0.82):
        self.match_threshold = match_threshold
        self.watchlist = STATUTORY_WATCHLIST

    def screen_entity(self, user_name: Optional[str], user_id: str) -> Dict[str, Any]:
        """
        Screens an entity against PEP, UAPA, and UN Sanctions regimes.
        Evaluates both token containment and string sequence ratios.
        """
        candidates: List[str] = []
        if user_name:
            candidates.append(normalize_name(user_name))
        if user_id:
            candidates.append(normalize_name(user_id))

        target = " ".join([c for c in candidates if c]).strip()
        if not target:
            return {"matched": False, "match_count": 0, "hits": [], "action_required": "NONE"}

        target_tokens = set(target.split())
        hits: List[Dict[str, Any]] = []

        for entry in self.watchlist:
            names_to_check = [entry["name"]] + entry.get("aliases", [])
            best_sim = 0.0
            matched_on = entry["name"]

            for candidate_name in names_to_check:
                cand_norm = normalize_name(candidate_name)
                cand_tokens = set(cand_norm.split())

                # 1. Full string sequence ratio
                sim_ratio = string_similarity(target, cand_norm)

                # 2. Token overlap ratio (e.g., 'nirav modi' inside 'nirav deepak modi')
                overlap_count = len(target_tokens & cand_tokens)
                token_overlap = overlap_count / max(len(target_tokens), 1) if target_tokens else 0.0

                effective_score = max(sim_ratio, token_overlap)

                if effective_score > best_sim:
                    best_sim = effective_score
                    matched_on = candidate_name

            if best_sim >= self.match_threshold:
                hits.append({
                    "watchlist_id": entry["id"],
                    "entity_name": entry["name"],
                    "matched_alias": matched_on,
                    "confidence": round(best_sim, 4),
                    "category": entry["category"],
                    "regime": entry["regime"],
                    "risk_severity": entry["risk_severity"],
                })

        is_matched = len(hits) > 0
        has_critical = any(h["risk_severity"] == "critical" for h in hits)

        return {
            "matched": is_matched,
            "match_count": len(hits),
            "hits": hits,
            "action_required": "IMMEDIATE_BLOCK_AND_STR" if has_critical else ("ENHANCED_DUE_DILIGENCE" if is_matched else "NONE"),
        }


# Singleton engine instance
watchlist_engine = WatchlistEngine(match_threshold=0.82)