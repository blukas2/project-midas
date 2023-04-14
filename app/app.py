import tkinter as tk
from tkinter import ttk


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
        self.btn_add_asset = tk.Button(window, text="Add Asset", command=self.add_asset)
        self.btn_remove_asset = tk.Button(window, text="Remove Asset", command=self.remove_asset)
        self.btn_recalculate_portfolio = tk.Button(window, text="Recalculate Portfolio", command=self.recalculate_portfolio)

        self._define_asset_table(window)

        self.btn_add_asset.grid(row = 1, column = 1, columnspan = 1)
        self.btn_remove_asset.grid(row = 1, column = 2, columnspan = 1)
        self.btn_recalculate_portfolio.grid(row = 1, column = 3, columnspan = 1)
        self.asset_table.grid(row = 2, column = 1, columnspan = 5)



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

    def add_asset(self):
        pass

    def remove_asset(self):
        pass

    def recalculate_portfolio(self):
        pass

app = AppWindow()
app.run()