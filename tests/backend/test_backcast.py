import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LinearRegression

from backend.portfolio.backcast import Backcast


class TestBackcast:
    def test_load_data_creates_source_and_percentage_columns(self):
        source = pd.DataFrame({"Date": [1, 2, 3], "Value": [10, 20, 30]})
        backcast = Backcast.__new__(Backcast)

        actual = backcast._load_data(source, "asset")

        assert actual["asset"].tolist() == [10, 20, 30]
        assert actual["asset_pct"].iloc[0] != actual["asset_pct"].iloc[0]
        assert actual["asset_pct"].iloc[1] == 1

    def test_train_model_fits_linear_relation(self):
        backcast = Backcast.__new__(Backcast)
        training = pd.DataFrame(
            {"reference_pct": [-0.1, 0, 0.1], "asset_pct": [-0.2, 0, 0.2]}
        )

        model, score = backcast._train_model(training)

        assert isinstance(model, LinearRegression)
        assert score == pytest.approx(1)
        assert model.coef_[0] == pytest.approx(2)

    def test_low_score_uses_reference_returns(self):
        backcast = Backcast.__new__(Backcast)
        frame = pd.DataFrame({"reference_pct": [0.1, -0.1]})

        actual = backcast._predict_asset_pct(frame, LinearRegression(), 0.5)

        assert actual["asset_pct_pred"].tolist() == [0.1, -0.1]

    def test_first_asset_value_skips_missing_values(self):
        backcast = Backcast.__new__(Backcast)
        frame = pd.DataFrame({"asset": [np.nan, 12.5]})

        assert backcast._get_first_asset_value(frame) == 12.5

    def test_run_adds_backcast_values_and_preserves_observed_values(self):
        dates = pd.bdate_range("2020-01-01", periods=6)
        reference = pd.DataFrame({"Date": dates, "Value": [100, 105, 110, 115, 120, 125]})
        asset = pd.DataFrame({"Date": dates[3:], "Value": [115, 120, 125]})
        backcast = Backcast(asset, reference)

        actual = backcast.run()

        assert len(actual) == len(reference) - 1
        assert actual["Date"].iloc[0] == dates[1]
        assert actual["Value"].iloc[-3:].tolist() == [115, 120, 125]
        assert actual["Value"].iloc[:3].notna().all()
