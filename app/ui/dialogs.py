from __future__ import annotations

import customtkinter as ctk


class ThemedMessageBox:
    @classmethod
    def showerror(cls, title: str, message: str, parent=None):
        cls._show(title, message, parent, "Error")

    @classmethod
    def showwarning(cls, title: str, message: str, parent=None):
        cls._show(title, message, parent, "Warning")

    @classmethod
    def showinfo(cls, title: str, message: str, parent=None):
        cls._show(title, message, parent, "Information")

    @classmethod
    def _show(cls, title: str, message: str, parent, heading: str):
        dialog = ctk.CTkToplevel(parent)
        dialog.title(title)
        dialog.geometry("420x190")
        dialog.resizable(False, False)
        dialog.transient(parent)
        ctk.CTkLabel(dialog, text=heading, font=("", 18, "bold")).pack(pady=(20, 8))
        ctk.CTkLabel(dialog, text=message, wraplength=370).pack(padx=20, pady=8)
        ctk.CTkButton(dialog, text="OK", command=dialog.destroy).pack(pady=(8, 16))
        dialog.bind("<Return>", lambda _event: dialog.destroy())
        dialog.grab_set()
        dialog.wait_window()
