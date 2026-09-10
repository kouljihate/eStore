import flet as ft
from app.database import get_transactions, add_transaction, get_dashboard_data
from app.translations import get_translation as t
from app.theme import AppTheme
from app.currency import get_currency_symbol


class CashScreen(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self._page = page
        self.expand = True
        self.bgcolor = page.theme.bgcolor if hasattr(page.theme, "bgcolor") else None
        self._build()

    def _build(self):
        lang = self._page.session.store.get("lang") or "ar"
        user_id = self._page.session.store.get("user_id")
        self.transactions = get_transactions(user_id) if user_id else []
        data = get_dashboard_data(user_id) if user_id else {}

        is_dark = self._page.theme_mode == "dark" if hasattr(self._page, "theme_mode") else True
        surface = AppTheme.SURFACE_DARK if is_dark else AppTheme.SURFACE_LIGHT

        balance_card = ft.Container(
            content=ft.Column(
                [
                    ft.Text(t(lang, "balance"), size=14, opacity=0.7),
                    ft.Text(f"{data.get('cash_balance', 0):.2f} {get_currency_symbol(self._page)}", size=32, weight=ft.FontWeight.BOLD,
                            color=AppTheme.SUCCESS if data.get('cash_balance', 0) >= 0 else AppTheme.ERROR),
                    ft.Container(height=10),
                    ft.Row(
                        [
                            ft.Column([
                                ft.Text(t(lang, "total_income"), size=12, opacity=0.7),
                                ft.Text(f"{data.get('cash_income', 0):.2f} {get_currency_symbol(self._page)}",
                                        color=AppTheme.SUCCESS, size=16, weight=ft.FontWeight.BOLD),
                            ]),
                            ft.VerticalDivider(),
                            ft.Column([
                                ft.Text(t(lang, "total_expenses"), size=12, opacity=0.7),
                                ft.Text(f"{data.get('cash_expense', 0):.2f} {get_currency_symbol(self._page)}",
                                        color=AppTheme.ERROR, size=16, weight=ft.FontWeight.BOLD),
                            ]),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_AROUND,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=surface,
            border_radius=12,
            padding=20,
            margin=ft.Margin(left=0, top=10, right=0, bottom=10),
        )

        self.content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(t(lang, "cash"), size=24, weight=ft.FontWeight.BOLD),
                        ft.FloatingActionButton(
                            icon=ft.Icons.ADD,
                            on_click=self._show_add_dialog,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                balance_card,
                ft.Text(t(lang, "transaction_history"), size=18, weight=ft.FontWeight.BOLD),
                ft.Container(height=5),
                self._build_transactions_list(lang),
            ],
            scroll=ft.ScrollMode.AUTO,
        )

    def _build_transactions_list(self, lang):
        if not self.transactions:
            return ft.Text(t(lang, "no_data"), opacity=0.5, italic=True)
        rows = []
        for tr in self.transactions:
            color = AppTheme.SUCCESS if tr["type"] == "income" else AppTheme.ERROR
            label = t(lang, "income" if tr["type"] == "income" else "expense")
            sign = "+" if tr["type"] == "income" else "-"
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(label, color=color)),
                        ft.DataCell(ft.Text(f"{sign}{tr['amount']:.2f}", color=color,
                                            weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(tr.get("category", ""))),
                        ft.DataCell(ft.Text(tr.get("description", ""))),
                        ft.DataCell(ft.Text(tr["date"][:10] if tr["date"] else "")),
                    ]
                )
            )
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text(t(lang, "transaction_type"))),
                ft.DataColumn(ft.Text(t(lang, "amount"))),
                ft.DataColumn(ft.Text(t(lang, "category"))),
                ft.DataColumn(ft.Text(t(lang, "description"))),
                ft.DataColumn(ft.Text(t(lang, "date"))),
            ],
            rows=rows,
        )

    def _show_add_dialog(self, e):
        lang = self._page.session.store.get("lang") or "ar"
        ttype_dd = ft.Dropdown(
            label=t(lang, "transaction_type"),
            options=[
                ft.dropdown.Option("income", t(lang, "income")),
                ft.dropdown.Option("expense", t(lang, "expense")),
            ],
            value="income",
            expand=True,
        )
        amt_inp = ft.TextField(label=t(lang, "amount"), value="0",
                                keyboard_type=ft.KeyboardType.NUMBER, text_align=ft.TextAlign.RIGHT, expand=True)
        cat_inp = ft.TextField(label=t(lang, "category"), text_align=ft.TextAlign.RIGHT, expand=True)
        desc_inp = ft.TextField(label=t(lang, "description"), multiline=True, text_align=ft.TextAlign.RIGHT, expand=True)
        error_text = ft.Text("", color="red", size=13, text_align=ft.TextAlign.CENTER)

        def save(e):
            try:
                amt = float(amt_inp.value or 0)
                add_transaction(self._page.session.store.get("user_id"), ttype_dd.value, amt,
                                cat_inp.value.strip(), desc_inp.value.strip())
                self._page.pop_dialog()
                self._refresh()
            except ValueError as ex:
                error_text.value = str(ex) if str(ex) else t(lang, "error")
                error_text.update()

        dlg = ft.AlertDialog(
            title=ft.Text(t(lang, "add_transaction")),
            content=ft.Column([ttype_dd, amt_inp, cat_inp, desc_inp, error_text], scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton(t(lang, "cancel"), on_click=lambda e: self._page.pop_dialog()),
                ft.FilledButton(t(lang, "save"), on_click=save),
            ],
        )
        self._page.show_dialog(dlg)

    def _refresh(self):
        self.transactions = get_transactions(self._page.session.store.get("user_id")) if self._page.session.store.get("user_id") else []
        self._build()
        self.update()
