import os
import json
import pandas as pd

from backend.globals.config import PORTFOLIOS_FOLDER
from backend.portfolio.portfolio import Portfolio


class FileManager:
    def __init__(self):
        self.folder = PORTFOLIOS_FOLDER
    
    def save_portfolio(self, portfolio: Portfolio):        
        component_data = portfolio.retrieve_component_data()
        file_name = portfolio.name.replace(" (custom)", "") + '.json'
        file_path = f"{self.folder}/{file_name}"
        with open(file_path, mode="w+") as file:
            file.write(json.dumps(component_data))

    def load_portfolio(self, portfolio_name: str):
        if portfolio_name.endswith(" (custom)"):
            file_name = portfolio_name.replace(" (custom)", "") + ".json"
            file_path = f"{self.folder}/{file_name}"
            with open(file_path) as file:
                component_data = json.load(file)
            portfolio = Portfolio(portfolio_name)
            for ticker, quantity in component_data.items():
                portfolio.add_asset(ticker, quantity)
            portfolio.calculate()
            return portfolio
        else:
            portfolio_files = os.listdir(f"{self.folder}/{portfolio_name}")
            portfolio_dates_and_files = {
                self._get_date_value_from_filename(filename): filename 
                for filename in portfolio_files
            }
            latest_date = max(portfolio_dates_and_files.keys())
            file_name = portfolio_dates_and_files[latest_date]
            portfolio_df = pd.read_csv(f"{self.folder}/{portfolio_name}/{file_name}", sep=";", encoding="utf-16")
            portfolio_df.rename({
                "ISIN": "isin",
                "Titel": "name",
                "Menge": "quantity"
            }, inplace=True)
            portfolio_df = [["isin", "name", "quantity"]]

    def _get_date_value_from_filename(self, filename: str):
        filename_wo_extension = filename.split(".")[0]
        date_text = filename_wo_extension.split("_")[-1]
        date_value = int(date_text.replace("-", ""))
        return date_value

    def list_portfolio_names(self):
        names_list = []
        for item_name in os.listdir(self.folder):
            if item_name.endswith(".json"):
                names_list.append(item_name.replace(".json", "") + " (custom)")
            elif "." not in item_name:
                names_list.append(item_name)
            else:
                raise ValueError("Invalid portfolio item.")                
        self.portfolio_names_list = names_list
