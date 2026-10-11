import importlib.util
from pathlib import Path
from unittest.mock import Mock


class TestSandboxScript:
    def test_ticker_lookup_and_output_are_mocked(self, monkeypatch):
        app_folder = Path(__file__).resolve().parents[1] / "app"
        spec = importlib.util.spec_from_file_location(
            "midas_sandbox", app_folder / "sandbox.py"
        )
        module = importlib.util.module_from_spec(spec)
        ticker = Mock(info={"shortName": "Index"})
        ticker_factory = Mock(return_value=ticker)
        output = Mock()
        monkeypatch.setattr("yfinance.Ticker", ticker_factory)
        monkeypatch.setattr("builtins.print", output)

        spec.loader.exec_module(module)

        ticker_factory.assert_called_once_with("^GSPC")
        output.assert_called_once_with(ticker.info)
