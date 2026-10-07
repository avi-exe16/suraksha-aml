import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# FIU-IND Mandatory Reporting Limits (INR)
MANDATORY_CTR_LIMIT = 1000000.0  # ₹10 Lakhs (CTR trigger)
STRUCTURING_LOWER_BOUND = 850000.0  # Common smurfing band just below ₹10L
STRUCTURING_BURST_BOUND = 45000.0  # Frequent micro-smurfing band below ₹50k


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates geodesic distance between two points in km."""
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class FIURuleEngine:
    def __init__(self):
        pass

    def evaluate(
        self,
        txn: Dict[str, Any],
        velocity_stats: Dict[str, Any],
        last_txn: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates regulatory and statutory rules.
        Returns:
            triggered: bool
            rules_violated: List[Dict]
            risk_override: Optional[str] (e.g., 'high' or 'critical')
        """
        amount = float(txn.get("amount", 0.0))
        hour = int(txn.get("hour", 0))
        violations: List[Dict[str, Any]] = []

        # 1. MANDATORY CTR THRESHOLD (Direct statutory trigger)
        if amount >= MANDATORY_CTR_LIMIT:
            violations.append({
                "rule_id": "FIU-CTR-001",
                "name": "Mandatory Cash Transaction Report (CTR) Limit Exceeded",
                "severity": "high",
                "details": f"Transaction amount ₹{amount:,.2f} equals or exceeds ₹10,00,000 threshold.",
            })

        # 2. STRUCTURING / SMURFING DETECTION
        # A: High-value single transaction just below the reporting ceiling
        if STRUCTURING_LOWER_BOUND <= amount < MANDATORY_CTR_LIMIT:
            violations.append({
                "rule_id": "FIU-STR-001",
                "name": "Potential Smurfing (Near-Threshold Structuring)",
                "severity": "high",
                "details": f"Amount ₹{amount:,.2f} falls within evasion band (₹8.5L - ₹10L).",
            })

        # B: Velocity-based structuring (burst of amounts accumulating past threshold in 24h)
        sum_24h = float(velocity_stats.get("sum_24h", 0.0)) + amount
        count_24h = int(velocity_stats.get("count_24h", 0)) + 1
        if count_24h >= 3 and sum_24h >= MANDATORY_CTR_LIMIT and amount < STRUCTURING_LOWER_BOUND:
            violations.append({
                "rule_id": "FIU-STR-002",
                "name": "Aggregate 24-Hour Velocity Structuring",
                "severity": "high",
                "details": f"User accumulated ₹{sum_24h:,.2f} over {count_24h} transactions in 24h.",
            })

        # 3. HIGH-VELOCITY BURSTS (Sub-50k micro structuring)
        count_1h = int(velocity_stats.get("count_1h", 0)) + 1
        if count_1h >= 5 and amount <= STRUCTURING_BURST_BOUND:
            violations.append({
                "rule_id": "FIU-VEL-001",
                "name": "Rapid Micro-Structuring Burst",
                "severity": "medium",
                "details": f"High frequency of sub-₹50,000 txns ({count_1h} txns in 1 hour).",
            })

        # 4. IMPOSSIBLE TRAVEL / VELOCITY TELEPORTATION
        if last_txn and "lat" in last_txn and "lon" in last_txn and "timestamp" in last_txn:
            try:
                curr_lat = float(txn.get("lat", 0.0))
                curr_lon = float(txn.get("lon", 0.0))
                prev_lat = float(last_txn.get("lat", 0.0))
                prev_lon = float(last_txn.get("lon", 0.0))

                dist_km = haversine_distance_km(prev_lat, prev_lon, curr_lat, curr_lon)
                prev_time = datetime.fromisoformat(str(last_txn["timestamp"]))
                curr_time = datetime.now(timezone.utc)
                time_diff_hours = max((curr_time - prev_time).total_seconds() / 3600.0, 0.01)

                speed_kmh = dist_km / time_diff_hours
                # Commercial flight cruise speed ~900 km/h; flags physical travel impossibility
                if dist_km > 300.0 and speed_kmh > 850.0:
                    violations.append({
                        "rule_id": "FIU-GEO-001",
                        "name": "Impossible Geographic Teleportation",
                        "severity": "critical",
                        "details": f"User jumped {dist_km:.1f} km in {time_diff_hours:.2f} hrs ({speed_kmh:.0f} km/h).",
                    })
            except Exception:
                pass

        # 5. NOCTURNAL HIGH-VALUE DRIFT
        if (1 <= hour <= 4) and amount >= 200000.0:
            violations.append({
                "rule_id": "FIU-TIM-001",
                "name": "High-Value Nocturnal Transaction",
                "severity": "medium",
                "details": f"Transaction of ₹{amount:,.2f} initiated during dormant window ({hour}:00 hrs).",
            })

        # Determine highest severity level
        severities = [v["severity"] for v in violations]
        highest_risk = None
        if "critical" in severities:
            highest_risk = "high"  # triggers immediate hold
        elif "high" in severities:
            highest_risk = "high"
        elif "medium" in severities:
            highest_risk = "medium"

        return {
            "triggered": len(violations) > 0,
            "violations": violations,
            "risk_override": highest_risk,
        }


# Singleton engine instance
fiu_engine = FIURuleEngine()