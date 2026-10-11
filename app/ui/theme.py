from __future__ import annotations

import weakref

import customtkinter as ctk
from tkinter import ttk


class ChartStyler:
    def __init__(self):
        self._figures = weakref.WeakSet()

    def register(self, figure):
        self._figures.add(figure)
        self._style_figure(figure)

    def refresh(self):
        for figure in tuple(self._figures):
            self._style_figure(figure)

    def _style_figure(self, figure):
        dark_mode = ctk.get_appearance_mode() == "Dark"
        background = "#2b2b2b" if dark_mode else "#ffffff"
        foreground = "#f2f2f2" if dark_mode else "#222222"
        figure.set_facecolor(background)
        for axes in figure.axes:
            self._style_axes(axes, background, foreground)
        figure.canvas.draw_idle()

    def _style_axes(self, axes, background: str, foreground: str):
        axes.set_facecolor(background)
        axes.tick_params(colors=foreground)
        axes.xaxis.label.set_color(foreground)
        axes.yaxis.label.set_color(foreground)
        axes.title.set_color(foreground)
        for text in axes.texts:
            text.set_color(foreground)
        for spine in axes.spines.values():
            spine.set_color(foreground)
        legend = axes.get_legend()
        if legend is not None:
            legend.get_frame().set_facecolor(background)
            legend.get_frame().set_edgecolor(foreground)
            for text in legend.get_texts():
                text.set_color(foreground)


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
    style.configure(
        "Treeview.Heading",
        background=selected,
        foreground="#ffffff",
        relief="flat",
    )


def _configure_treeview_selection(style: ttk.Style):
    dark_mode = ctk.get_appearance_mode() == "Dark"
    selected = "#1f6aa5" if dark_mode else "#3b8ed0"
    style.map(
        "Treeview",
        background=[("selected", selected)],
        foreground=[("selected", "#ffffff")],
    )
    style.map("Treeview.Heading", background=[("active", selected)])


def style_chart(figure):
    chart_styler.register(figure)


def toggle_appearance_mode() -> str:
    current_mode = ctk.get_appearance_mode()
    next_mode = "Light" if current_mode == "Dark" else "Dark"
    ctk.set_appearance_mode(next_mode)
    configure_native_widget_theme()
    chart_styler.refresh()
    return next_mode
