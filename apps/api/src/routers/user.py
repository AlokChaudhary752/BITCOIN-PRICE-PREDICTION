"""
User Management and Paper Trading Router.
Alerts management and virtual capital trading portfolio.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.database import get_db
from apps.api.src.models import Alert, PaperPortfolio, PaperTrade, User
from apps.api.src.routers.market import get_latest_dataframe
from apps.api.src.schemas import (
    AlertCreate,
    AlertResponse,
    PaperPortfolioResponse,
    PaperTradeCreate,
    PaperTradeResponse,
)
from apps.api.src.security import get_current_user

router = APIRouter(prefix="/user", tags=["User & Portfolio"])


@router.get("/alerts", response_model=list[AlertResponse])
async def list_alerts(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """List all active alerts configured by the user."""
    stmt = select(Alert).where(Alert.user_id == user.id).order_by(desc(Alert.created_at))
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/alerts", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    req: AlertCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new alert trigger (price, signal, or regime change)."""
    alert = Alert(
        user_id=user.id,
        alert_type=req.alert_type,
        condition=req.condition,
        threshold=req.threshold,
        target_value=req.target_value,
        is_active=True,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an alert."""
    stmt = select(Alert).where(Alert.id == alert_id, Alert.user_id == user.id)
    res = await db.execute(stmt)
    alert = res.scalars().first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    await db.delete(alert)
    await db.commit()


@router.get("/portfolio", response_model=PaperPortfolioResponse)
async def get_portfolio(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get user's virtual paper trading portfolio."""
    stmt = select(PaperPortfolio).where(PaperPortfolio.user_id == user.id)
    res = await db.execute(stmt)
    portfolio = res.scalars().first()

    if not portfolio:
        # Initialize if not present
        portfolio = PaperPortfolio(
            user_id=user.id,
            initial_capital=100000.0,
            cash=100000.0,
            btc_balance=0.0,
            total_equity=100000.0,
        )
        db.add(portfolio)
        await db.commit()
        await db.refresh(portfolio)

    df = get_latest_dataframe()
    curr_price = float(df["close"].iloc[-1]) if not df.empty else 81500.0

    total_equity = portfolio.cash + (portfolio.btc_balance * curr_price)
    unrealized_pnl = total_equity - portfolio.initial_capital

    trades_stmt = select(PaperTrade).where(PaperTrade.portfolio_id == portfolio.id).order_by(desc(PaperTrade.timestamp)).limit(20)
    trades_res = await db.execute(trades_stmt)
    trades = trades_res.scalars().all()

    return PaperPortfolioResponse(
        id=portfolio.id,
        initial_capital=portfolio.initial_capital,
        cash=round(portfolio.cash, 2),
        btc_balance=round(portfolio.btc_balance, 6),
        total_equity=round(total_equity, 2),
        realized_pnl=round(portfolio.realized_pnl, 2),
        current_btc_price=round(curr_price, 2),
        unrealized_pnl=round(unrealized_pnl, 2),
        recent_trades=[
            PaperTradeResponse(
                id=t.id,
                side=t.side,
                price=round(t.price, 2),
                amount=round(t.amount, 6),
                value=round(t.value, 2),
                fee=round(t.fee, 2),
                pnl=round(t.pnl, 2),
                timestamp=t.timestamp,
            )
            for t in trades
        ],
    )


@router.post("/portfolio/trade", response_model=PaperTradeResponse)
async def execute_trade(
    req: PaperTradeCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute virtual paper trade (BUY or SELL BTC) at live market price."""
    stmt = select(PaperPortfolio).where(PaperPortfolio.user_id == user.id)
    res = await db.execute(stmt)
    portfolio = res.scalars().first()
    if not portfolio:
        raise HTTPException(status_code=400, detail="Portfolio not initialized.")

    df = get_latest_dataframe()
    curr_price = float(df["close"].iloc[-1]) if not df.empty else 81500.0

    fee_rate = 0.0006  # 6 bps
    value = req.amount * curr_price
    fee = value * fee_rate

    side = req.side.upper()
    if side == "BUY":
        tot_cost = value + fee
        if portfolio.cash < tot_cost:
            raise HTTPException(status_code=400, detail=f"Insufficient cash balance. Required: ${tot_cost:,.2f}")
        portfolio.cash -= tot_cost
        portfolio.btc_balance += req.amount
        pnl = 0.0
    elif side == "SELL":
        if portfolio.btc_balance < req.amount:
            raise HTTPException(status_code=400, detail=f"Insufficient BTC balance. Available: {portfolio.btc_balance:.6f}")
        net_proceeds = value - fee
        portfolio.cash += net_proceeds
        portfolio.btc_balance -= req.amount
        pnl = 0.0  # Realized on transaction
    else:
        raise HTTPException(status_code=400, detail="Invalid trade side. Must be BUY or SELL.")

    trade = PaperTrade(
        portfolio_id=portfolio.id,
        side=side,
        price=curr_price,
        amount=req.amount,
        value=value,
        fee=fee,
        pnl=pnl,
    )
    db.add(trade)
    await db.commit()
    await db.refresh(trade)

    return PaperTradeResponse(
        id=trade.id,
        side=trade.side,
        price=round(trade.price, 2),
        amount=round(trade.amount, 6),
        value=round(trade.value, 2),
        fee=round(trade.fee, 2),
        pnl=round(trade.pnl, 2),
        timestamp=trade.timestamp,
    )
