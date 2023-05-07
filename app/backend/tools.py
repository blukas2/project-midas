import os
import json

from backend.globals.settings import FOLDER
from backend.portfolio.portfolio import Portfolio


class FileManager:
    def __init__(self):
        self.folder = FOLDER
    
    def save_portfolio(self, portfolio: Portfolio):        
        component_data = portfolio.retrieve_component_data()
        file_name = portfolio.name + '.json'
        file_path = f"{self.folder}/{file_name}"
        with open(file_path, mode="w+") as file:
            file.write(json.dumps(component_data))

    def load_portfolio(self, portfolio_name):
        file_name = portfolio_name + '.json'
        file_path = f"{self.folder}/{file_name}"
        with open(file_path) as file:
            component_data = json.load(file)
        portfolio = Portfolio(portfolio_name)
        for ticker, quantity in component_data.items():
            portfolio.add_asset(ticker, quantity)
        portfolio.calculate()
        return portfolio

    def list_portfolio_names(self):
        self.portfolio_names_list = [file[:-5] for file in os.listdir(self.folder) if file[-5:]=='.json']
