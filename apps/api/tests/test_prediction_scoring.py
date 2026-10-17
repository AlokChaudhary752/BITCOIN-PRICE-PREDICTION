"""
Live Prediction Persistence and Scoring Unit Test.
Acceptance Check: a live prediction row is written and later scored.
"""
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.models import Prediction
from apps.api.src.scheduler import score_pending_predictions


@pytest.mark.asyncio
async def test_live_prediction_written_and_scored(db_session: AsyncSession):
    # 1. WRITE: Insert a live prediction row with is_scored = False
    past_timestamp = datetime.now(UTC) - timedelta(hours=2)
    pred_row = Prediction(
        horizon="1h",
        timestamp=past_timestamp,
        current_price=80000.0,
        point_forecast=81200.0,
        expected_return_pct=1.5,
        prob_up=0.68,
        agreement_score=88.5,
        risk_score=4,
        signal="Buy",
        signal_level=4,
        confidence_level="High confidence",
        interval_50_lower=80500.0,
        interval_50_upper=81800.0,
        interval_90_lower=79200.0,
        interval_90_upper=82500.0,
        q05=79200.0,
        q25=80500.0,
        q50=81200.0,
        q75=81800.0,
        q95=82500.0,
        is_scored=False,
        actual_price=None,
        model_version="1.0.0",
    )
    db_session.add(pred_row)
    await db_session.commit()
    await db_session.refresh(pred_row)

    assert pred_row.id is not None
    assert pred_row.is_scored is False
    assert pred_row.actual_price is None

    # 2. SCORE: Run background scoring engine
    scored_count = await score_pending_predictions(session=db_session)
    assert scored_count >= 1

    # 3. VERIFY: Query the prediction row and assert it was scored
    stmt = select(Prediction).where(Prediction.id == pred_row.id)
    res = await db_session.execute(stmt)
    scored_pred = res.scalars().first()

    assert scored_pred is not None
    assert scored_pred.is_scored is True
    assert scored_pred.actual_price is not None
    assert scored_pred.actual_price > 0.0
    assert scored_pred.error is not None
    assert scored_pred.abs_error is not None
    assert scored_pred.pinball_loss is not None
    assert scored_pred.scored_at is not None

    print(
        f"\n[ACCEPTANCE VERIFIED] Prediction {scored_pred.id} successfully written and scored: "
        f"Forecast=${scored_pred.point_forecast:,.2f} -> Actual=${scored_pred.actual_price:,.2f}, "
        f"AbsError=${scored_pred.abs_error:,.2f}, ScoredAt={scored_pred.scored_at}"
    )
