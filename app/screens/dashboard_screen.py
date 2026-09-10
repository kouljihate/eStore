import flet as ft
from app.database import get_dashboard_data, get_stock_movements, get_transactions
from app.translations import get_translation as t
from app.theme import AppTheme
from app.currency import get_currency_symbol


class DashboardScreen(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self._page = page
        self.expand = True
        self.bgcolor = page.theme.bgcolor if hasattr(page.theme, "bgcolor") else None
        self._build()

    def _build(self):
        lang = self._page.session.store.get("lang") or "ar"
        user_id = self._page.session.store.get("user_id")
        data = get_dashboard_data(user_id) if user_id else {}
        movements = get_stock_movements(user_id, 5) if user_id else []
        transactions = get_transactions(user_id, 5) if user_id else []

        kpi_cards = ft.ResponsiveRow(
            [
                self._kpi_card(t(lang, "total_stock_value"), f"{data.get('stock_value', 0):.2f} {get_currency_symbol(self._page)}",
                               ft.Icons.INVENTORY, AppTheme.PRIMARY, col={"sm": 6, "md": 3}),
                self._kpi_card(t(lang, "potential_profit"), f"{data.get('potential_profit', 0):.2f} {get_currency_symbol(self._page)}",
                               ft.Icons.TRENDING_UP, AppTheme.SUCCESS, col={"sm": 6, "md": 3}),
                self._kpi_card(t(lang, "cash_balance"), f"{data.get('cash_balance', 0):.2f} {get_currency_symbol(self._page)}",
                               ft.Icons.ACCOUNT_BALANCE_WALLET, AppTheme.ACCENT, col={"sm": 6, "md": 3}),
                self._kpi_card(t(lang, "total_products"), str(data.get("product_count", 0)),
                               ft.Icons.CATEGORY, AppTheme.PRIMARY, col={"sm": 6, "md": 3}),
                self._kpi_card(t(lang, "low_stock_alerts"), str(data.get("low_stock_count", 0)),
                               ft.Icons.WARNING_AMBER, AppTheme.LOW_STOCK, col={"sm": 6, "md": 3}),
                self._kpi_card(t(lang, "credit_outstanding"), f"{data.get('credit_outstanding', 0):.2f} {get_currency_symbol(self._page)}",
                               ft.Icons.CREDIT_CARD, AppTheme.ACCENT, col={"sm": 6, "md": 3}),
            ],
            spacing=10,
        )

        self.content = ft.Column(
            [
                ft.Text(t(lang, "dashboard"), size=24, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                kpi_cards,
                ft.Container(height=10),
                ft.Text(t(lang, "recent_movements"), size=18, weight=ft.FontWeight.BOLD),
                ft.Container(height=5),
                self._movements_table(movements, lang),
                ft.Container(height=10),
                ft.Text(t(lang, "recent_transactions"), size=18, weight=ft.FontWeight.BOLD),
                ft.Container(height=5),
                self._transactions_table(transactions, lang),
            ],
            scroll=ft.ScrollMode.AUTO,
        )

    def _kpi_card(self, title, value, icon, color, **kwargs):
        is_dark = self._page.theme_mode == "dark" if hasattr(self._page, "theme_mode") else True
        surface = AppTheme.SURFACE_DARK if is_dark else AppTheme.SURFACE_LIGHT
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row([ft.Icon(icon, color=color, size=28)], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=5),
                    ft.Text(value, size=22, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ft.Text(title, size=12, opacity=0.7, text_align=ft.TextAlign.CENTER),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
            ),
            bgcolor=surface,
            border_radius=12,
            padding=15,
            **kwargs,
        )

    def _movements_table(self, movements, lang):
        if not movements:
            return ft.Text(t(lang, "no_movements"), opacity=0.5, italic=True)
        rows = []
        for m in movements:
            color = AppTheme.SUCCESS if m["type"] == "in" else AppTheme.ERROR
            label = t(lang, "stock_in" if m["type"] == "in" else "stock_out")
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(m.get("product_name", ""))),
                        ft.DataCell(ft.Text(label, color=color)),
                        ft.DataCell(ft.Text(str(m["quantity"]))),
                        ft.DataCell(ft.Text(m["date"][:10] if m["date"] else "")),
                    ]
                )
            )
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text(t(lang, "product_name"))),
                ft.DataColumn(ft.Text(t(lang, "movement_type"))),
                ft.DataColumn(ft.Text(t(lang, "quantity"))),
                ft.DataColumn(ft.Text(t(lang, "date"))),
            ],
            rows=rows,
        )

    def _transactions_table(self, transactions, lang):
        if not transactions:
            return ft.Text(t(lang, "no_transactions"), opacity=0.5, italic=True)
        rows = []
        for tr in transactions:
            color = AppTheme.SUCCESS if tr["type"] == "income" else AppTheme.ERROR
            label = t(lang, "income" if tr["type"] == "income" else "expense")
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(label, color=color)),
                        ft.DataCell(ft.Text(f"{tr['amount']:.2f}")),
                        ft.DataCell(ft.Text(tr.get("category", ""))),
                        ft.DataCell(ft.Text(tr["date"][:10] if tr["date"] else "")),
                    ]
                )
            )
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text(t(lang, "transaction_type"))),
                ft.DataColumn(ft.Text(t(lang, "amount"))),
                ft.DataColumn(ft.Text(t(lang, "category"))),
                ft.DataColumn(ft.Text(t(lang, "date"))),
            ],
            rows=rows,
        )
