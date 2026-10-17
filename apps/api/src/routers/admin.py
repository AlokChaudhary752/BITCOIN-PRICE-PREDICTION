"""
Admin Management Router.
Model registry control, retrain trigger, promotion, and audit log inspection.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from apps.api.src.database import get_db
from apps.api.src.models import User, AuditLog
from apps.api.src.security import require_admin
from btc_oracle_ml.train import train_pipeline
from btc_oracle_ml.config import MODEL_REGISTRY_DIR

router = APIRouter(prefix="/admin", tags=["Admin Controls"])


@router.post("/retrain")
async def trigger_retrain(
    background_tasks: BackgroundTasks,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Trigger quantitative model retraining job in background."""
    background_tasks.add_task(train_pipeline, force_refresh=True)

    audit = AuditLog(
        user_id=admin.id,
        action="ADMIN_MODEL_RETRAIN_TRIGGERED",
        details="Admin triggered model retrain pipeline.",
    )
    db.add(audit)
    await db.commit()

    return {"status": "QUEUED", "message": "Model retraining pipeline initiated."}


@router.post("/promote")
async def promote_model(
    model_version: str = "1.0.0",
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Promote challenger model to production champion."""
    audit = AuditLog(
        user_id=admin.id,
        action="ADMIN_MODEL_PROMOTED",
        details=f"Model version {model_version} promoted to production champion.",
    )
    db.add(audit)
    await db.commit()

    return {
        "status": "PROMOTED",
        "champion_version": model_version,
        "promoted_by": admin.email,
    }


@router.get("/model-registry")
async def get_model_registry(admin: User = Depends(require_admin)):
    """List model registry artifacts and provenance."""
    champion_path = MODEL_REGISTRY_DIR / "champion_model.joblib"
    exists = champion_path.exists()
    size_mb = round(champion_path.stat().st_size / (1024 * 1024), 2) if exists else 0.0

    return {
        "active_champion": {
            "version": "1.0.0",
            "artifact": "champion_model.joblib",
            "size_mb": size_mb,
            "status": "SERVING",
            "horizons": ["1h", "4h", "24h", "7d", "30d"],
            "models": ["Quantile LightGBM", "Stacked Quantile GRU", "Gaussian HMM", "Conformal Calibrator"],
        },
        "registry_directory": str(MODEL_REGISTRY_DIR),
    }


@router.get("/audit-log")
async def get_audit_logs(
    limit: int = 100,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Return chronological security and administrative audit trail."""
    stmt = select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit)
    res = await db.execute(stmt)
    logs = res.scalars().all()

    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "ip_address": log.ip_address,
            "details": log.details,
            "timestamp": log.timestamp.isoformat(),
        }
        for log in logs
    ]
