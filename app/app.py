import tkinter as tk


class AppWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Midas v0.0.1")
        self.dropdown_menu = DropdownMenu(self.window)
    
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


app = AppWindow()
app.run()