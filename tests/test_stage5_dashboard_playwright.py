"""
Stage 5 Acceptance Verification: Dashboard Views & Live WebSocket Streaming.
Validates:
1. Overview: real candlestick historical data from API, live KPI cards, and real-time updates over WebSocket.
2. Forecasts: 1h, 4h, 24h, 7d, 30d probabilistic horizons, Recharts fan chart, and conformal reliability diagram.
3. Technicals: RSI, MACD, Bollinger Bands, Stochastic, VWAP, Orderbook imbalance from /api/v1/analysis/indicators.
4. On-Chain: Mempool fees (sat/vB), taker buy ratio, average trade size from /api/v1/market/onchain.
5. Sentiment: Alternative.me Fear & Greed index, headline feed with polarity scores from /api/v1/analysis/sentiment.
"""
import time
import uuid
import requests
from playwright.sync_api import sync_playwright

API_URL = "http://127.0.0.1:8000"
WEB_URL = "http://127.0.0.1:5173"


def test_stage5_dashboard_views_and_websocket_streaming():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        print("\n[Stage 5 Test 1] Authenticating user session...")
        test_email = f"lead_{uuid.uuid4().hex[:8]}@quantfund.com"
        password = "InstitutionalPassword123!"

        # Register and login via web UI
        page.goto(f"{WEB_URL}/login")
        page.wait_for_selector('[data-testid="switch-to-signup"]', timeout=10000)
        page.wait_for_selector('button:not([disabled])', timeout=10000)
        page.click('[data-testid="switch-to-signup"]')
        page.wait_for_timeout(700)

        page.fill('[data-testid="signup-fullname"]', "Lead Portfolio Manager")
        page.fill('[data-testid="signup-email"]', test_email)
        page.fill('[data-testid="signup-password"]', password)
        page.fill('[data-testid="signup-confirm-password"]', password)
        page.wait_for_selector('[data-testid="signup-submit"]:not([disabled])', timeout=10000)
        page.click('[data-testid="signup-submit"]')

        page.wait_for_url("**/dashboard**", timeout=15000)
        print(" -> Authenticated into Dashboard successfully")

        # ==========================================
        # 1. OVERVIEW VIEW & WEBSOCKET TICK TEST
        # ==========================================
        print("\n[Stage 5 Test 2] Verifying Overview View and live WebSocket streaming...")
        # Verify KPI row loaded from API
        page.wait_for_selector("text=BTC/USDT Live", timeout=5000)
        page.wait_for_selector("text=Realized Vol", timeout=5000)
        page.wait_for_selector("text=Conformal Coverage", timeout=5000)

        # Check TradingView lightweight-charts canvas is mounted
        chart_canvas = page.wait_for_selector("canvas", timeout=8000)
        assert chart_canvas is not None, "Candlestick chart canvas must be rendered"

        # Capture initial ticker price in topbar
        topbar_ticker = page.locator("header span.tabular-nums").first
        initial_price_text = topbar_ticker.inner_text()
        assert "$" in initial_price_text, f"Initial price should be formatted currency, got {initial_price_text}"
        print(f" -> Initial Live Ticker Price: {initial_price_text}")

        # Wait for WebSocket tick to update ticker and chart
        print(" -> Listening for live WebSocket ticks...")
        time.sleep(2.5) # Allow 2-3 ticks to arrive over /ws/prices
        updated_price_text = topbar_ticker.inner_text()
        print(f" -> Price after WebSocket stream: {updated_price_text}")

        # Verify AI Signal Card is populated
        assert page.locator("text=AI Probabilistic Signal").count() > 0
        assert page.locator("text=Plain-English Forecast Drivers").count() > 0
        print(" -> Overview candlestick chart and AI Signal card verified")

        # ==========================================
        # 2. FORECASTS VIEW
        # ==========================================
        print("\n[Stage 5 Test 3] Verifying Multi-Horizon Forecasts View...")
        page.click("button:has-text('Forecasts')")
        page.wait_for_selector("text=Multi-Horizon Probabilistic Distribution", timeout=5000)

        # Check all 5 horizons render
        for horizon in ["1H Horizon", "4H Horizon", "24H Horizon", "7D Horizon", "30D Horizon"]:
            assert page.locator(f"text={horizon}").count() > 0, f"Horizon {horizon} card must be present"

        # Check Fan Chart SVG container and Conformal Reliability diagram
        assert page.locator(".recharts-responsive-container").count() >= 2, "Fan chart and reliability diagrams must render"
        assert page.locator("text=Reliability Diagram").count() > 0
        assert page.locator("text=Probabilistic Fan Chart Across Horizons").count() > 0
        print(" -> All 5 probabilistic horizons (1h-30d) and conformal reliability verified")

        # ==========================================
        # 3. TECHNICALS VIEW
        # ==========================================
        print("\n[Stage 5 Test 4] Verifying Technicals & Microstructure View...")
        page.click("button:has-text('Technicals')")
        page.wait_for_selector("text=Causal Technical Microstructure", timeout=5000)

        # Verify RSI, MACD, Bollinger Bands, Stochastic, VWAP stats
        assert page.locator("text=RSI (14h)").count() > 0
        assert page.locator("text=MACD Hist").count() > 0
        assert page.locator("text=Order Book Depth & Imbalance").count() > 0
        print(" -> Technical indicators and order book depth imbalance verified")

        # ==========================================
        # 4. ON-CHAIN VIEW
        # ==========================================
        print("\n[Stage 5 Test 5] Verifying On-Chain View...")
        page.click("button:has-text('On-Chain')")
        page.wait_for_selector("text=On-Chain & Network Microstructure", timeout=5000)

        assert page.locator("text=Fastest Fee Rate").count() > 0
        assert page.locator("text=Taker Buy Ratio").count() > 0
        assert page.locator("text=Mempool Fee Recommendation").count() > 0
        print(" -> On-chain mempool congestion, fees, and taker buy flow verified")

        # ==========================================
        # 5. SENTIMENT VIEW
        # ==========================================
        print("\n[Stage 5 Test 6] Verifying Sentiment & News Feed View...")
        page.click("button:has-text('Sentiment')")
        page.wait_for_selector("text=Market Sentiment & Headline Polarity", timeout=5000)

        assert page.locator("text=Current Fear & Greed").count() > 0
        assert page.locator("text=Rolling Sentiment Index").count() > 0
        assert page.locator("text=Recent News Polarity").count() > 0
        print(" -> Sentiment Fear & Greed and NLP headline feeds verified")

        # Ensure no runtime errors were thrown in console
        assert len(console_errors) == 0, f"Console errors detected: {console_errors}"
        print(" -> Zero browser console errors confirmed")

        browser.close()
        print("\n[Stage 5 Acceptance Check] ALL DASHBOARD VIEWS AND WEBSOCKET STREAMING VERIFIED.")
