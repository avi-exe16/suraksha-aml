import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    desc,
    func,
    select,
    text,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

logger = logging.getLogger("suraksha.database")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/suraksha_aml",
)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_recycle=1800,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


# --- DATABASE MODELS ---

class TransactionRecord(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    txn_id = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(String(64), index=True, nullable=False)
    amount = Column(Float, nullable=False)
    channel = Column(String(32), default="UPI")
    anomaly_score = Column(Float, nullable=False)
    risk_level = Column(String(16), index=True, nullable=False)
    action = Column(String(16), nullable=False)
    shadow_mode = Column(Boolean, default=False)
    km_from_last_txn = Column(Float, default=0.0)
    minutes_from_last_txn = Column(Float, default=0.0)
    impossible_speed = Column(Float, default=0.0)
    hour = Column(Integer, default=12)
    is_weekend = Column(Integer, default=0)
    is_night = Column(Integer, default=0)
    txn_count_1hr = Column(Float, default=0.0)
    txn_count_24hr = Column(Float, default=0.0)
    amount_sum_1hr = Column(Float, default=0.0)
    amount_sum_24hr = Column(Float, default=0.0)
    amount_vs_user_avg = Column(Float, default=1.0)
    is_new_device = Column(Float, default=0.0)
    device_count_7d = Column(Float, default=1.0)
    is_new_merchant_category = Column(Float, default=0.0)
    raw_payload = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        Index("idx_user_timestamp", "user_id", "timestamp"),
    )


class AuditLogRecord(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), index=True, nullable=False)
    accessor = Column(String(64), nullable=False)
    access_type = Column(String(64), nullable=False)
    purpose = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)


class ConsentRecord(Base):
    __tablename__ = "consents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), index=True, nullable=False)
    accessor = Column(String(64), nullable=False)
    status = Column(String(32), default="active", nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# --- LIFECYCLE & SESSION ---

@asynccontextmanager
async def get_db_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schemas verified and initialized.")


# --- PERSISTENCE OPERATIONS ---

async def store_transaction_and_flag_safe(txn: Dict[str, Any], result: Dict[str, Any], is_shadow: bool = False):
    try:
        async with get_db_session() as session:
            record = TransactionRecord(
                txn_id=txn.get("txn_id"),
                user_id=txn.get("user_id"),
                amount=float(txn.get("amount", 0.0)),
                channel=txn.get("channel", "UPI"),
                anomaly_score=float(result.get("anomaly_score", 0.0)),
                risk_level=result.get("risk_level", "low"),
                action="approved" if is_shadow else result.get("action", "approved"),
                shadow_mode=is_shadow,
                km_from_last_txn=float(txn.get("km_from_last_txn", 0.0)),
                minutes_from_last_txn=float(txn.get("minutes_from_last_txn", 0.0)),
                impossible_speed=float(txn.get("impossible_speed", 0.0)),
                hour=int(txn.get("hour", 12)),
                is_weekend=int(txn.get("is_weekend", 0)),
                is_night=int(txn.get("is_night", 0)),
                txn_count_1hr=float(txn.get("txn_count_1hr", 0.0)),
                txn_count_24hr=float(txn.get("txn_count_24hr", 0.0)),
                amount_sum_1hr=float(txn.get("amount_sum_1hr", 0.0)),
                amount_sum_24hr=float(txn.get("amount_sum_24hr", 0.0)),
                amount_vs_user_avg=float(txn.get("amount_vs_user_avg", 1.0)),
                is_new_device=float(txn.get("is_new_device", 0.0)),
                device_count_7d=float(txn.get("device_count_7d", 1.0)),
                is_new_merchant_category=float(txn.get("is_new_merchant_category", 0.0)),
                raw_payload=str(txn),
            )
            session.add(record)
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to persist transaction {txn.get('txn_id')}: {e}", exc_info=True)


async def log_audit_entry_safe(user_id: str, accessor: str, access_type: str, purpose: str):
    try:
        async with get_db_session() as session:
            record = AuditLogRecord(
                user_id=user_id,
                accessor=accessor,
                access_type=access_type,
                purpose=purpose,
            )
            session.add(record)
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to persist audit log for {user_id}: {e}", exc_info=True)


# --- QUERIES ---

async def get_transactions(limit: int = 100, risk_level: Optional[str] = None) -> List[Dict[str, Any]]:
    async with get_db_session() as session:
        stmt = select(TransactionRecord).order_by(desc(TransactionRecord.timestamp)).limit(limit)
        if risk_level:
            stmt = stmt.where(TransactionRecord.risk_level == risk_level)
        result = await session.execute(stmt)
        records = result.scalars().all()
        return [
            {
                "txn_id": r.txn_id,
                "user_id": r.user_id,
                "amount": r.amount,
                "channel": r.channel,
                "anomaly_score": r.anomaly_score,
                "risk_level": r.risk_level,
                "action": r.action,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            }
            for r in records
        ]


async def get_flagged_transactions(limit: int = 50) -> List[Dict[str, Any]]:
    async with get_db_session() as session:
        stmt = (
            select(TransactionRecord)
            .where(TransactionRecord.risk_level.in_(["medium", "high"]))
            .order_by(desc(TransactionRecord.timestamp))
            .limit(limit)
        )
        result = await session.execute(stmt)
        records = result.scalars().all()
        return [
            {
                "txn_id": r.txn_id,
                "user_id": r.user_id,
                "amount": r.amount,
                "anomaly_score": r.anomaly_score,
                "risk_level": r.risk_level,
                "action": r.action,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            }
            for r in records
        ]


async def get_transaction_by_id(txn_id: str) -> Optional[Dict[str, Any]]:
    async with get_db_session() as session:
        stmt = select(TransactionRecord).where(TransactionRecord.txn_id == txn_id)
        result = await session.execute(stmt)
        r = result.scalars().first()
        if not r:
            return None
        return {
            "txn_id": r.txn_id,
            "user_id": r.user_id,
            "amount": r.amount,
            "channel": r.channel,
            "anomaly_score": r.anomaly_score,
            "risk_level": r.risk_level,
            "action": r.action,
            "km_from_last_txn": r.km_from_last_txn,
            "minutes_from_last_txn": r.minutes_from_last_txn,
            "impossible_speed": r.impossible_speed,
            "txn_count_1hr": r.txn_count_1hr,
            "txn_count_24hr": r.txn_count_24hr,
            "amount_sum_1hr": r.amount_sum_1hr,
            "amount_sum_24hr": r.amount_sum_24hr,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        }


async def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    async with get_db_session() as session:
        stmt = (
            select(
                func.count(TransactionRecord.id).label("total_txns"),
                func.coalesce(func.sum(TransactionRecord.amount), 0.0).label("total_volume"),
                func.coalesce(func.avg(TransactionRecord.amount), 0.0).label("avg_amount"),
                func.coalesce(func.max(TransactionRecord.amount), 0.0).label("max_amount"),
            )
            .where(TransactionRecord.user_id == user_id)
        )
        res = await session.execute(stmt)
        stats = res.first()
        if not stats or stats.total_txns == 0:
            return None

        return {
            "user_id": user_id,
            "total_transactions": stats.total_txns,
            "total_volume": float(stats.total_volume),
            "average_amount": round(float(stats.avg_amount), 2),
            "max_amount": float(stats.max_amount),
        }


async def get_user_transactions(user_id: str) -> List[Dict[str, Any]]:
    async with get_db_session() as session:
        stmt = (
            select(TransactionRecord)
            .where(TransactionRecord.user_id == user_id)
            .order_by(desc(TransactionRecord.timestamp))
            .limit(50)
        )
        result = await session.execute(stmt)
        records = result.scalars().all()
        return [
            {
                "txn_id": r.txn_id,
                "amount": r.amount,
                "risk_level": r.risk_level,
                "action": r.action,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            }
            for r in records
        ]


async def get_risk_stats() -> Dict[str, Any]:
    async with get_db_session() as session:
        total_stmt = select(func.count(TransactionRecord.id))
        high_stmt = select(func.count(TransactionRecord.id)).where(TransactionRecord.risk_level == "high")
        med_stmt = select(func.count(TransactionRecord.id)).where(TransactionRecord.risk_level == "medium")
        low_stmt = select(func.count(TransactionRecord.id)).where(TransactionRecord.risk_level == "low")

        total = (await session.execute(total_stmt)).scalar() or 0
        high = (await session.execute(high_stmt)).scalar() or 0
        medium = (await session.execute(med_stmt)).scalar() or 0
        low = (await session.execute(low_stmt)).scalar() or 0

        return {
            "total_scored": total,
            "high_risk": high,
            "medium_risk": medium,
            "low_risk": low,
            "high_risk_pct": round((high / total) * 100, 2) if total > 0 else 0.0,
        }


async def get_audit_log(user_id: str) -> List[Dict[str, Any]]:
    async with get_db_session() as session:
        stmt = (
            select(AuditLogRecord)
            .where(AuditLogRecord.user_id == user_id)
            .order_by(desc(AuditLogRecord.timestamp))
            .limit(50)
        )
        result = await session.execute(stmt)
        records = result.scalars().all()
        return [
            {
                "id": r.id,
                "user_id": r.user_id,
                "accessor": r.accessor,
                "access_type": r.access_type,
                "purpose": r.purpose,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            }
            for r in records
        ]


async def revoke_consent(user_id: str, accessor: str):
    async with get_db_session() as session:
        record = ConsentRecord(
            user_id=user_id,
            accessor=accessor,
            status="revoked",
            updated_at=datetime.now(timezone.utc),
        )
        session.add(record)
        await session.commit()


async def get_consent_status(user_id: str) -> List[Dict[str, Any]]:
    async with get_db_session() as session:
        stmt = select(ConsentRecord).where(ConsentRecord.user_id == user_id)
        result = await session.execute(stmt)
        records = result.scalars().all()
        return [
            {
                "accessor": r.accessor,
                "status": r.status,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in records
        ]


async def get_recent_transactions_df(limit: int = 1000) -> pd.DataFrame:
    async with get_db_session() as session:
        query = text("""
            SELECT 
                amount, km_from_last_txn, minutes_from_last_txn, impossible_speed,
                hour, is_weekend, is_night, txn_count_1hr, txn_count_24hr,
                amount_sum_1hr, amount_sum_24hr, amount_vs_user_avg,
                is_new_device, device_count_7d, is_new_merchant_category,
                risk_level
            FROM transactions
            ORDER BY timestamp DESC
            LIMIT :limit
        """)
        result = await session.execute(query, {"limit": limit})
        rows = result.fetchall()
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows, columns=result.keys())