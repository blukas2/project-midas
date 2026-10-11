from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd
import pytest


APP_FOLDER = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_FOLDER))


@pytest.fixture
def price_history():
    def build(values, start=date(2020, 1, 1)):
        dates = pd.bdate_range(start=start, periods=len(values)).date
        return pd.DataFrame({"Date": dates, "Value": values, "Price": values})

    return build


@pytest.fixture
def portfolio_stub():
    from backend.portfolio.portfolio import Portfolio

    portfolio = object.__new__(Portfolio)
    portfolio.name = "Test portfolio"
    portfolio.content = {}
    portfolio.fx_rates = {}
    portfolio.asset_names_dict = {}
    portfolio.reference_assets = None
    return portfolio
