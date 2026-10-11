from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from backend.backend import BackEnd


class TestBackEnd:
    def test_constructor_builds_dependencies(self, monkeypatch):
        dependencies = {
            "Portfolio": object(),
            "FileManager": object(),
            "Comparer": object(),
            "AssetAnalyzer": object(),
        }
        for name, instance in dependencies.items():
            monkeypatch.setattr("backend.backend." + name, lambda instance=instance: instance)
        backend = BackEnd()

        assert backend.portfolio is dependencies["Portfolio"]
        assert backend.file_manager is dependencies["FileManager"]
        assert backend.comparer is dependencies["Comparer"]
        assert backend.asset_analyzer is dependencies["AssetAnalyzer"]

    def test_load_and_save_delegate_to_file_manager(self):
        backend = BackEnd.__new__(BackEnd)
        backend.file_manager = Mock()

        backend.load_portfolio("Fund")
        backend.save_portfolio()

        backend.file_manager.load_portfolio.assert_called_once_with("Fund")
        backend.file_manager.save_portfolio.assert_called_once_with(backend.portfolio)

    def test_new_portfolio_replaces_current_portfolio(self, monkeypatch):
        created = object()
        monkeypatch.setattr("backend.backend.Portfolio", lambda name: created)
        backend = BackEnd.__new__(BackEnd)

        backend.new_portfolio("New")

        assert backend.portfolio is created

    def test_analyze_portfolio_returns_analysis(self, monkeypatch):
        expected = object()
        monkeypatch.setattr(
            "backend.backend.PortfolioAnalyzer",
            lambda portfolio: SimpleNamespace(analyze=lambda: expected),
        )
        backend = BackEnd.__new__(BackEnd)
        backend.portfolio = object()

        assert backend.analyze_portfolio() is expected

    def test_analyze_impact_returns_current_and_projected_results(self, monkeypatch):
        current_result, projected_result = object(), object()
        modified = SimpleNamespace(content={"ABC": object()}, calculate=Mock())
        backend = BackEnd.__new__(BackEnd)
        backend.portfolio = SimpleNamespace(create_modified_copy=lambda *args: modified)
        backend.analyze_portfolio = Mock(return_value=current_result)
        monkeypatch.setattr(
            "backend.backend.PortfolioAnalyzer",
            lambda portfolio: SimpleNamespace(analyze=lambda: projected_result),
        )

        assert backend.analyze_impact("ABC", 1) == (current_result, projected_result)
        modified.calculate.assert_called_once_with()

    def test_analyze_impact_rejects_empty_projection(self):
        backend = BackEnd.__new__(BackEnd)
        backend.portfolio = SimpleNamespace(
            create_modified_copy=lambda *args: SimpleNamespace(content={})
        )
        backend.analyze_portfolio = Mock()

        with pytest.raises(ValueError, match="portfolio empty"):
            backend.analyze_impact("ABC", -1)
