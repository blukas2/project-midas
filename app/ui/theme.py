from __future__ import annotations

import weakref

import customtkinter as ctk
from tkinter import ttk


class ChartStyler:
    def __init__(self):
        self._dashboards = weakref.WeakSet()

    def register(self, dashboard):
        self._dashboards.add(dashboard)

    def refresh(self):
        mode = ctk.get_appearance_mode()
        for dashboard in tuple(self._dashboards):
            dashboard.set_theme(mode)


chart_styler = ChartStyler()


def configure_theme():
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")


def configure_native_widget_theme():
    style = ttk.Style()
    style.theme_use("clam")
    _configure_treeview_colors(style)
    _configure_treeview_selection(style)


def _configure_treeview_colors(style: ttk.Style):
    dark_mode = ctk.get_appearance_mode() == "Dark"
    background = "#2b2b2b" if dark_mode else "#f0f0f0"
    foreground = "#f2f2f2" if dark_mode else "#1f1f1f"
    selected = "#1f6aa5" if dark_mode else "#3b8ed0"
    style.configure(
        "Treeview",
        background=background,
        fieldbackground=background,
        foreground=foreground,
        rowheight=28,
    )
    style.configure("Treeview.Heading", background=selected, foreground="#ffffff", relief="flat")


def _configure_treeview_selection(style: ttk.Style):
    dark_mode = ctk.get_appearance_mode() == "Dark"
    selected = "#1f6aa5" if dark_mode else "#3b8ed0"
    style.map(
        "Treeview",
        background=[("selected", selected)],
        foreground=[("selected", "#ffffff")],
    )
    style.map("Treeview.Heading", background=[("active", selected)])


def toggle_appearance_mode() -> str:
    current_mode = ctk.get_appearance_mode()
    next_mode = "Light" if current_mode == "Dark" else "Dark"
    ctk.set_appearance_mode(next_mode)
    configure_native_widget_theme()
    chart_styler.refresh()
    return next_mode
