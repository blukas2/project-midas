from backend.portfolio.portfolio import Portfolio
from backend.portfolio.portfolio_analyzer import PortfolioAnalyzer, AnalysisResult
from backend.comparer.comparer import Comparer
from backend.asset_analyzer import AssetAnalyzer
from backend.tools import FileManager

class BackEnd:
    def __init__(self):
        self.portfolio = Portfolio()
        self.file_manager = FileManager()
        self.comparer = Comparer()
        self.asset_analyzer = AssetAnalyzer()

    def load_portfolio(self, portfolio_name: str):
        self.portfolio = self.file_manager.load_portfolio(portfolio_name)

    def save_portfolio(self):
        self.file_manager.save_portfolio(self.portfolio)

    def new_portfolio(self, portfolio_name):
        self.portfolio = Portfolio(portfolio_name)

    def analyze_portfolio(self) -> AnalysisResult:
        analyzer = PortfolioAnalyzer(self.portfolio)
        return analyzer.analyze()

    def analyze_impact(self, ticker: str, quantity_change: int) -> tuple[AnalysisResult, AnalysisResult]:
        """Analyze the impact of a position change on portfolio metrics."""
        current_result = self.analyze_portfolio()
        modified_portfolio = self.portfolio.create_modified_copy(ticker, quantity_change)
        if not modified_portfolio.content:
            raise ValueError("The proposed change would leave the portfolio empty.")
        modified_portfolio.calculate()
        projected_result = PortfolioAnalyzer(modified_portfolio).analyze()
        return current_result, projected_result





