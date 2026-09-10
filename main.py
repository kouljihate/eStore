import flet as ft
import os
from app.database import init_db
from app.translations import get_translation as t
from app.theme import AppTheme, ARABIC_FONT
from app.screens.login_screen import LoginScreen
from app.screens.dashboard_screen import DashboardScreen
from app.screens.stock_screen import StockScreen
from app.screens.cash_screen import CashScreen
from app.screens.settings_screen import SettingsScreen
from app.screens.credit_screen import CreditScreen


def main(page: ft.Page):
    init_db()

    font_path = os.path.join(os.path.dirname(__file__), "assets", "fonts", "VIP_RAWY_THIN.ttf")
    page.fonts = {ARABIC_FONT: font_path}

    page.title = "eDrogery"
    page.theme_mode = page.session.store.get("theme_mode") or "dark"
    page.rtl = (page.session.store.get("lang") or "ar") == "ar"
    page.window.width = 360
    page.window.height = 780
    page.window.resizable = True
    page.padding = 10

    if not page.session.store.get("lang"):
        page.session.store.set("lang", "ar")
    if not page.session.store.get("theme_mode"):
        page.session.store.set("theme_mode", "dark")
    if not page.session.store.get("currency"):
        page.session.store.set("currency", "MAD")

    def _apply_theme():
        lang = page.session.store.get("lang") or "ar"
        mode = page.session.store.get("theme_mode") or "dark"
        page.theme = AppTheme.get_theme(mode, lang)

    def navigate_to(screen_index):
        nav_bar.selected_index = screen_index
        _update_screen(screen_index)

    def _update_screen(index):
        _apply_theme()
        lang = page.session.store.get("lang") or "ar"
        page.views.clear()
        user_id = page.session.store.get("user_id")

        if not user_id:
            view = ft.View(route="/", controls=[LoginScreen(page, on_login_success=lambda: navigate_to(0))], padding=10)
            page.views.append(view)
            page.update()
            return

        screens = [
            DashboardScreen(page),
            StockScreen(page),
            CashScreen(page),
            CreditScreen(page),
            SettingsScreen(page, on_logout=_logout, on_theme_change=_on_theme_change,
                            on_lang_change=_on_lang_change,
                            on_currency_change=lambda: _update_screen(nav_bar.selected_index)),
        ]

        titles = [t(lang, "dashboard"), t(lang, "stock"), t(lang, "cash"), t(lang, "credit"), t(lang, "settings")]
        icons = [ft.Icons.DASHBOARD, ft.Icons.INVENTORY, ft.Icons.ACCOUNT_BALANCE_WALLET, ft.Icons.CREDIT_CARD, ft.Icons.SETTINGS]

        content = screens[index] if index < len(screens) else screens[0]
        view = ft.View(
            route="/",
            controls=[
                ft.Container(content=content, expand=True),
            ],
            navigation_bar=nav_bar,
            padding=10,
        )
        page.views.append(view)
        page.update()

    def _logout():
        page.session.store.set("user_id", None)
        page.session.store.set("user_name", None)
        page.views.clear()
        _apply_theme()
        page.views.append(ft.View(route="/", controls=[LoginScreen(page, on_login_success=lambda: navigate_to(0))]))
        page.update()

    def _on_theme_change(mode):
        page.theme_mode = mode
        page.session.store.set("theme_mode", mode)
        _apply_theme()
        _update_screen(nav_bar.selected_index)

    def _on_lang_change(lang):
        page.rtl = lang == "ar"
        page.session.store.set("lang", lang)
        _apply_theme()
        _update_screen(nav_bar.selected_index)

    def _nav_change(e):
        _update_screen(e.control.selected_index)

    nav_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.DASHBOARD, label=t(page.session.store.get("lang") or "ar", "dashboard")),
            ft.NavigationBarDestination(icon=ft.Icons.INVENTORY, label=t(page.session.store.get("lang") or "ar", "stock")),
            ft.NavigationBarDestination(icon=ft.Icons.ACCOUNT_BALANCE_WALLET, label=t(page.session.store.get("lang") or "ar", "cash")),
            ft.NavigationBarDestination(icon=ft.Icons.CREDIT_CARD, label=t(page.session.store.get("lang") or "ar", "credit")),
            ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label=t(page.session.store.get("lang") or "ar", "settings")),
        ],
        selected_index=0,
        on_change=_nav_change,
    )

    _apply_theme()
    _update_screen(0)


if __name__ == "__main__":
    ft.run(main)
