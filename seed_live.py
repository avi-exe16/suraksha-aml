import time
import pandas as pd
import requests

# Point to local running FastAPI backend
LIVE_API = "http://127.0.0.1:8000"
CSV_PATH = "data/processed/transactions_scored.csv"

try:
    df = pd.read_csv(CSV_PATH)
except Exception as e:
    print(f"Error loading {CSV_PATH}: {e}")
    exit(1)

# Sample a realistic stratified distribution: 50 normal, 20 medium risk, 10 high risk
sample = pd.concat([
    df[df["anomaly_score"] < 0.5].head(50),
    df[(df["anomaly_score"] >= 0.5) & (df["anomaly_score"] < 0.8)].head(20),
    df[df["anomaly_score"] >= 0.8].head(10),
]).reset_index(drop=True)

print(f"Streaming {len(sample)} realistic transactions into SuRaksha dashboard at {LIVE_API}...")

success = 0
for idx, row in sample.iterrows():
    # Construct exact payload matching FastAPI TransactionInput schema
    payload = {
        "txn_id": str(row["txn_id"]),
        "user_id": str(row["user_id"]),
        "amount": float(row["amount"]),
        "channel": str(row.get("channel", "UPI")),
        "city": str(row["city"]),
        "lat": float(row["lat"]),
        "lon": float(row["lon"]),
        "device_id": str(row["device_id"]),
        "merchant_category": str(row["merchant_category"]),
        "hour": int(row["hour"]),
        "is_weekend": int(row["is_weekend"]),
        "ip_country": str(row.get("ip_country", "IN")),
        "device_type": str(row.get("device_type", "mobile")),
    }

    try:
        response = requests.post(f"{LIVE_API}/transaction/score", json=payload, timeout=3.0)
        if response.status_code == 200:
            res_json = response.json()
            risk = res_json.get("risk_level", "low").upper()
            action = res_json.get("action", "approved")
            fiu_flag = res_json.get("fiu_compliance", {}).get("flagged", False)
            flag_str = " [FIU FLAG]" if fiu_flag else ""
            print(f"[{idx+1:02d}/{len(sample)}] {payload['txn_id']} | ₹{payload['amount']:>10,.2f} | Risk: {risk:<6} | Action: {action:<8}{flag_str}")
            success += 1
        else:
            print(f"[{idx+1:02d}/{len(sample)}] Failed {payload['txn_id']}: {response.status_code} - {response.text}")
    except Exception as err:
        print(f"[{idx+1:02d}/{len(sample)}] Request error: {err}")

    time.sleep(0.3)  # Gentle pacing to avoid local token-bucket rate limits

print(f"\nCompleted: Successfully streamed {success}/{len(sample)} transactions.")