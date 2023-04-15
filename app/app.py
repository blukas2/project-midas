import tkinter as tk
from tkinter import ttk

import matplotlib as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class AppWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Midas v0.0.1")
        self.dropdown_menu = DropdownMenu(self.window)
        self.main_window = MainWindowComponents(self.window)
    
    def run(self):
        self.window.mainloop()


class DropdownMenu:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.menu = tk.Menu(self.root)
        root.config(menu=self.menu)
        
        self.portfolio_menu = tk.Menu(self.menu)
        self.menu.add_cascade(label='Portfolio', menu=self.portfolio_menu)
        self.portfolio_menu.add_command(label="New")
        self.portfolio_menu.add_command(label="Open")
        self.portfolio_menu.add_command(label="Save")
        self.portfolio_menu.add_command(label="Save as...")
        self.portfolio_menu.add_command(label="Exit", command=self._exit_command)

    def _exit_command(self):
        self.root.destroy()


class MainWindowComponents:
    def __init__(self, window):
        self._define_buttons(window)
        self._define_asset_table(window)
        self._define_main_plot(window)
        self._define_returns_plot(window)
        self._place_components()

    def _place_components(self):
        self.btn_add_asset.grid(row = 1, column = 1, columnspan = 1)
        self.btn_remove_asset.grid(row = 1, column = 2, columnspan = 1)
        self.btn_recalculate_portfolio.grid(row = 1, column = 3, columnspan = 1)
        self.asset_table.grid(row = 2, column = 1, columnspan = 5)
        self.main_plot_canvas.get_tk_widget().grid(row = 2, column = 6, columnspan = 4)
        self.returns_plot_canvas.get_tk_widget().grid(row = 3, column = 6, columnspan = 4)

    def _define_buttons(self, window):
        self.btn_add_asset = tk.Button(window, text="Add Asset", command=self.add_asset)
        self.btn_remove_asset = tk.Button(window, text="Remove Asset", command=self.remove_asset)
        self.btn_recalculate_portfolio = tk.Button(window, text="Recalculate Portfolio", command=self.recalculate_portfolio)

    def _define_asset_table(self, window):
        self.asset_table = ttk.Treeview(window)
        self.asset_table['columns'] = ('ticker', 'name', 'quantity', 'current_price', 'value')        

        self.asset_table.column("#0", width=0,  stretch='NO')
        self.asset_table.column("ticker",width=80)
        self.asset_table.column("name",width=80)
        self.asset_table.column("quantity",width=80)
        self.asset_table.column("current_price",width=80)
        self.asset_table.column("value",width=80)

        self.asset_table.heading("#0",text="")
        self.asset_table.heading("ticker",text='Ticker')
        self.asset_table.heading("name",text='Name')
        self.asset_table.heading("quantity",text='Quantity')
        self.asset_table.heading("current_price",text='Current Price')
        self.asset_table.heading("value",text='Value')

    def _define_main_plot(self, window):
        data = {
            'Python': 11.27,
            'C': 11.16,
            'Java': 10.46,
            'C++': 7.5,
            'C#': 5.26
        }
        languages = data.keys()
        popularity = data.values()

        figure = Figure(figsize=(6, 4), dpi=100)
        self.main_plot_canvas = FigureCanvasTkAgg(figure, window)
        axes = figure.add_subplot()
        axes.line(languages, popularity)
        #axes.bar(languages, popularity)
        axes.set_title('Top 5 Programming Languages')
        axes.set_ylabel('Popularity')

    def _define_returns_plot(self, window):
        data = {
            '1m': -12.23,
            '6m': -3.13,
            '1y': 2.23,
            '5y': 7.5,
            '10y': 5.26,
            'YTD': -6.22
        }
        periods = data.keys()
        returns = data.values()

        figure = Figure(figsize=(6, 3), dpi=100)
        self.returns_plot_canvas = FigureCanvasTkAgg(figure, window)
        axes = figure.add_subplot()
        axes.bar(periods, returns)
        axes.set_title('Portfolio Returns')
        axes.set_ylabel('annualized %')

    def add_asset(self):
        pass

    def remove_asset(self):
        pass

    def recalculate_portfolio(self):
        pass

app = AppWindow()
app.run()