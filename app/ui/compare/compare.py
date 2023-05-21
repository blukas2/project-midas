import tkinter as tk

class CompareWindow:
    def __init__(self, master):
        self.window = tk.Toplevel(master)
        self.window.title("Compare assets")
        self._define_components()
        self._place_components()


    def _define_components(self):
        self.lbl_asset1_title = tk.Label(self.window, text="Asset 1: ") 
        self.lbl_asset2_title = tk.Label(self.window, text="Asset 2: ")
        self.entry_asset1_ticker = tk.Entry(self.window, width = 10, borderwidth = 5)
        self.entry_asset2_ticker = tk.Entry(self.window, width = 10, borderwidth = 5)
        self.btn_compare = tk.Button(self.window,text ="Compare!")

    def _place_components(self):
        self.lbl_asset1_title.grid(row = 1, column = 1, columnspan = 1)
        self.lbl_asset2_title.grid(row = 1, column = 3, columnspan = 1)
        self.entry_asset1_ticker.grid(row = 1, column = 2, columnspan = 1)
        self.entry_asset2_ticker.grid(row = 1, column = 4, columnspan = 1)
        self.btn_compare.grid(row = 2, column = 2, columnspan = 2)
