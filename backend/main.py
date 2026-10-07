import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy import text

from circuit_breaker import redis_breaker
from database import (
    get_audit_log,
    get_consent_status,
    get_db_session,
    get_flagged_transactions,
    get_recent_transactions_df,
    get_risk_stats,
    get_transaction_by_id,
    get_transactions,
    get_user_profile,
    get_user_transactions,
    init_db,
    revoke_consent,
)
from drift_detector import compute_drift_report
from fiu_rules import fiu_engine
from models import ConsentRevocation, TransactionInput
from redis_store import close_redis_pool, feature_store, init_redis_pool
from sanctions import watchlist_engine
from scorer import engine
from security import SecurityHeadersMiddleware, verify_internal_api_key
from str_report import generate_str_report
from task_queue import durable_queue, queue_worker_loop

logger = logging.getLogger("suraksha.api")


# --- LIFECYCLE MANAGEMENT & DAEMON WORKER ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database schemas...")
    await init_db()

    logger.info("Connecting to Redis Feature Store...")
    await init_redis_pool()
    await feature_store.setup_scripts()

    logger.info("Starting Redis Streams persistent worker task...")
    worker_task = asyncio.create_task(queue_worker_loop())

    logger.info("Loading ML scoring engine artifacts...")
    engine.load_artifacts()

    logger.info("SuRaksha Resilient Engine and Feature Store initialized.")
    yield
    # Shutdown
    logger.info("Cancelling background stream worker...")
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass

    logger.info("Closing Redis connection pool...")
    await close_redis_pool()


app = FastAPI(
    title="SuRaksha Fraud Detection & AML Core",
    description="Enterprise transaction anomaly detection & statutory compliance system for Canara Bank",
    version="1.1.0",
    lifespan=lifespan,
)

# 1. OWASP Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# 2. Strict Origin Whitelist
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,https://suraksha.vercel.app",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://*.vercel.app",
        # add your production frontend domain here if you have a custom one
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "system": "SuRaksha Fraud Detection API",
        "version": "1.1.0",
        "compliance": ["PMLA Section 12", "RBI KYC/AML 2016", "FIU-IND AR-1"],
        "status": "operational",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    checks = {"database": False, "redis": False, "inference_engine": False, "circuit_breaker": "CLOSED"}
    latencies = {}

    # 1. Database Liveness & Latency
    t0 = datetime.now(timezone.utc)
    try:
        async with get_db_session() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = True
        latencies["database_ms"] = round((datetime.now(timezone.utc) - t0).total_seconds() * 1000, 2)
    except Exception as e:
        latencies["database_err"] = str(e)

    # 2. Redis Liveness & Latency
    t0 = datetime.now(timezone.utc)
    try:
        await feature_store.get_config("SHADOW_MODE", default=False)
        checks["redis"] = True
        latencies["redis_ms"] = round((datetime.now(timezone.utc) - t0).total_seconds() * 1000, 2)
    except Exception as e:
        latencies["redis_err"] = str(e)

    # 3. Model Engine Check
    checks["inference_engine"] = callable(getattr(engine, "score_transaction", None))
    checks["circuit_breaker"] = redis_breaker.state.value

    all_healthy = checks["database"] and checks["redis"] and checks["inference_engine"]
    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if all_healthy else "degraded",
            "checks": checks,
            "latencies": latencies,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# --- GRACEFUL DEGRADATION FALLBACK ---
async def fallback_velocity_stats(user_id: str, txn_id: str, amount: float) -> Dict[str, Any]:
    logger.warning(f"CIRCUIT OPEN: Engaging fallback velocity stats for txn {txn_id}")
    return {
        "count_1h": 1,
        "count_24h": 1,
        "sum_1h": amount,
        "sum_24h": amount,
        "degraded_mode": True,
    }


# --- INFERENCE PATHWAY WITH RESILIENCE & DURABLE QUEUE ---

@app.post("/transaction/score", status_code=status.HTTP_200_OK, tags=["Inference"])
async def score_new_transaction(txn: TransactionInput, request: Request):
    # 1. Edge rate-limiting
    client_ip = request.client.host if request.client else "unknown"
    try:
        allowed = await feature_store.check_rate_limit(f"ip:{client_ip}", capacity=60, refill_per_sec=10.0)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Too many scoring requests from this source.",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Rate limiting check degraded: {e}")

    # 2. Redis Feature Extraction via Circuit Breaker
    velocity_stats = await redis_breaker.call(
        feature_store.get_and_update_features,
        fallback_velocity_stats,
        user_id=txn.user_id,
        txn_id=txn.txn_id,
        amount=txn.amount,
    )

    # 3. Model payload construction
    txn_dict = txn.model_dump()
    txn_dict["txn_count_1hr"] = velocity_stats["count_1h"]
    txn_dict["txn_count_24hr"] = velocity_stats["count_24h"]
    txn_dict["amount_sum_1hr"] = velocity_stats["sum_1h"]
    txn_dict["amount_sum_24hr"] = velocity_stats["sum_24h"]

    # 4. Scorer evaluation
    result = engine.score_transaction(txn_dict, explain=True)

    # 5. FIU-IND statutory rules
    fiu_result = fiu_engine.evaluate(txn=txn_dict, velocity_stats=velocity_stats)

    # 5b. Watchlist screening (UNSCR, MHA, PEP)
    sender_name = getattr(txn, "sender_name", None) or txn_dict.get("sender_name") or txn_dict.get("user_id")
    sanctions_result = watchlist_engine.screen_entity(
        user_name=sender_name,
        user_id=txn.user_id,
    )

    # 6. Unified risk aggregation
    final_risk = result["risk_level"]
    if sanctions_result["action_required"] == "IMMEDIATE_BLOCK_AND_STR":
        final_risk = "high"
    elif fiu_result["risk_override"] == "high":
        final_risk = "high"
    elif fiu_result["risk_override"] == "medium" and final_risk == "low":
        final_risk = "medium"

    action = "declined" if final_risk == "high" else ("flagged" if final_risk == "medium" else "approved")

    # 7. Safe shadow mode check
    try:
        is_shadow = await feature_store.get_config("SHADOW_MODE", default=False)
    except Exception:
        is_shadow = False

    effective_action = "approved" if is_shadow else action

    # 8. Dispatch events to Redis Streams
    await durable_queue.enqueue(
        "TRANSACTION_RECORD",
        {
            "txn": txn_dict,
            "result": result,
            "is_shadow": is_shadow,
        },
    )

    if final_risk in ["medium", "high"]:
        purpose_str = "Automated fraud scan"
        if sanctions_result["matched"]:
            purpose_str += " | PEP/Sanctions Hit: " + sanctions_result["hits"][0]["watchlist_id"]
        if fiu_result["triggered"]:
            purpose_str += " | FIU Violation: " + fiu_result["violations"][0]["rule_id"]

        await durable_queue.enqueue(
            "AUDIT_LOG",
            {
                "user_id": txn.user_id,
                "accessor": "fraud_detection_engine",
                "access_type": "statutory_block" if final_risk == "high" else "anomaly_scan",
                "purpose": purpose_str,
            },
        )

    return {
        "txn_id": txn.txn_id,
        "user_id": txn.user_id,
        "amount": txn.amount,
        "anomaly_score": result["anomaly_score"],
        "risk_level": final_risk,
        "action": effective_action,
        "shadow_mode": is_shadow,
        "resilience": {
            "circuit_breaker_state": redis_breaker.state.value,
            "velocity_degraded": velocity_stats.get("degraded_mode", False),
        },
        "sanctions_screening": sanctions_result,
        "fiu_compliance": {
            "flagged": fiu_result["triggered"] or sanctions_result["matched"],
            "violations": fiu_result["violations"],
        },
        "explanation": result["explanation"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# --- TRANSACTION & AUDIT ROUTES ---

@app.get("/transactions")
async def list_transactions(
    limit: int = Query(100, ge=1, le=500),
    risk_level: Optional[str] = Query(None),
):
    transactions = await get_transactions(limit=limit, risk_level=risk_level)
    return {
        "count": len(transactions),
        "transactions": transactions,
    }


@app.get("/transactions/flagged")
async def list_flagged_transactions(limit: int = Query(50, ge=1, le=200)):
    flagged = await get_flagged_transactions(limit=limit)
    return {
        "count": len(flagged),
        "transactions": flagged,
    }


@app.get("/transactions/{txn_id}")
async def get_transaction(txn_id: str):
    txn = await get_transaction_by_id(txn_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    await durable_queue.enqueue(
        "AUDIT_LOG",
        {
            "user_id": str(txn.get("user_id", "unknown")),
            "accessor": "bank_officer",
            "access_type": "transaction_view",
            "purpose": "Transaction detail review",
        },
    )
    return txn


@app.get("/users/{user_id}")
async def get_user(user_id: str):
    profile = await get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return profile


@app.get("/users/{user_id}/transactions")
async def get_user_transaction_history(user_id: str):
    transactions = await get_user_transactions(user_id)
    if not transactions:
        raise HTTPException(status_code=404, detail="No transactions found for user")
    return {
        "user_id": user_id,
        "count": len(transactions),
        "transactions": transactions,
    }


@app.get("/dashboard/stats")
async def get_dashboard_stats():
    return await get_risk_stats()


@app.get("/audit/{user_id}")
async def get_user_audit_log(user_id: str):
    entries = await get_audit_log(user_id)
    return {
        "user_id": user_id,
        "count": len(entries),
        "entries": entries,
    }


@app.post("/consent/revoke")
async def revoke_user_consent(revocation: ConsentRevocation):
    await revoke_consent(user_id=revocation.user_id, accessor=revocation.accessor)
    await durable_queue.enqueue(
        "AUDIT_LOG",
        {
            "user_id": revocation.user_id,
            "accessor": revocation.accessor,
            "access_type": "consent_revocation",
            "purpose": "User revoked data access",
        },
    )
    return {
        "status": "success",
        "user_id": revocation.user_id,
        "accessor": revocation.accessor,
        "revoked_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/consent/{user_id}")
async def get_user_consent(user_id: str):
    return {
        "user_id": user_id,
        "consents": await get_consent_status(user_id),
    }


@app.get("/transactions/{txn_id}/report")
async def download_str_report(txn_id: str):
    txn = await get_transaction_by_id(txn_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    await durable_queue.enqueue(
        "AUDIT_LOG",
        {
            "user_id": str(txn.get("user_id", "unknown")),
            "accessor": "compliance_team",
            "access_type": "str_report_generation",
            "purpose": "Suspicious Transaction Report generated for FIU-IND submission",
        },
    )

    pdf_bytes = generate_str_report(txn)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=STR_{txn_id}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf"
        },
    )


# --- CONFIGURATION & MANAGEMENT (AUTHENTICATED) ---

@app.get("/shadow-mode")
async def get_shadow_mode():
    enabled = await feature_store.get_config("SHADOW_MODE", default=False)
    return {"shadow_mode": enabled}


@app.post("/shadow-mode/toggle")
async def toggle_shadow_mode(api_key: str = Depends(verify_internal_api_key)):
    current = await feature_store.get_config("SHADOW_MODE", default=False)
    new_state = not current
    await feature_store.set_config("SHADOW_MODE", new_state)
    return {
        "shadow_mode": new_state,
        "message": "Shadow mode enabled." if new_state else "Shadow mode disabled.",
    }


@app.get("/drift/report")
async def get_drift_report():
    df = await get_recent_transactions_df(limit=1000)
    return compute_drift_report(df)


@app.post("/model/reload", tags=["MLOps"])
async def reload_model_artifacts(api_key: str = Depends(verify_internal_api_key)):
    try:
        engine.load_artifacts()
        return {
            "status": "success",
            "message": "Inference engine reloaded new model artifacts from disk.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to reload model artifacts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Artifact reload failed: {str(e)}",
        )