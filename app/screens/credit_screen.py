import flet as ft
from app.database import (get_credit_notes, get_credit_note, get_credit_note_items,
                          add_credit_note, add_credit_payment, get_credit_payments,
                          get_credit_summary, get_customers, add_customer,
                          get_products)
from app.translations import get_translation as t
from app.theme import AppTheme
from app.currency import get_currency_symbol


class CreditScreen(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self._page = page
        self.expand = True
        self.bgcolor = page.theme.bgcolor if hasattr(page.theme, "bgcolor") else None
        self._status_filter = None
        self._build()

    def _build(self):
        lang = self._page.session.store.get("lang") or "ar"
        user_id = self._page.session.store.get("user_id")
        self.credit_notes = get_credit_notes(user_id, self._status_filter) if user_id else []
        summary = get_credit_summary(user_id) if user_id else {}

        is_dark = self._page.theme_mode == "dark" if hasattr(self._page, "theme_mode") else True
        surface = AppTheme.SURFACE_DARK if is_dark else AppTheme.SURFACE_LIGHT

        summary_card = ft.Container(
            content=ft.Column(
                [
                    ft.Text(t(lang, "credit_outstanding"), size=14, opacity=0.7),
                    ft.Text(f"{summary.get('total_outstanding', 0):.2f} {get_currency_symbol(self._page)}",
                            size=28, weight=ft.FontWeight.BOLD, color=AppTheme.ACCENT),
                    ft.Text(f"{summary.get('open_count', 0)} {t(lang, 'open')}",
                            size=13, opacity=0.6),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=surface,
            border_radius=12,
            padding=20,
            margin=ft.Margin(left=0, top=5, right=0, bottom=10),
        )

        filter_selected = ["all"] if self._status_filter is None else [self._status_filter]
        filter_row = ft.SegmentedButton(
            segments=[
                ft.Segment("all", label=ft.Text(t(lang, "all"))),
                ft.Segment("open", label=ft.Text(t(lang, "open"))),
                ft.Segment("closed", label=ft.Text(t(lang, "closed"))),
            ],
            selected=filter_selected,
            on_change=self._on_filter_change,
        )

        self.content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(t(lang, "credit_notes"), size=24, weight=ft.FontWeight.BOLD),
                        ft.FloatingActionButton(
                            icon=ft.Icons.ADD,
                            on_click=self._show_add_dialog,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                summary_card,
                filter_row,
                ft.Container(height=5),
                self._build_credit_list(lang),
            ],
            scroll=ft.ScrollMode.AUTO,
        )

    def _on_filter_change(self, e):
        selected = e.data
        if "all" in selected:
            self._status_filter = None
        elif "open" in selected:
            self._status_filter = "open"
        elif "closed" in selected:
            self._status_filter = "closed"
        self._refresh()

    def _build_credit_list(self, lang):
        if not self.credit_notes:
            return ft.Text(t(lang, "no_credit_notes"), opacity=0.5, italic=True)
        cards = []
        for cn in self.credit_notes:
            remaining = cn["total_amount"] - cn["paid_amount"]
            is_open = cn["status"] == "open"
            status_color = AppTheme.ACCENT if is_open else AppTheme.SUCCESS
            status_label = t(lang, "open" if is_open else "closed")
            cards.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text(cn["customer_name"], size=16, weight=ft.FontWeight.BOLD, expand=True),
                                        ft.Container(
                                            content=ft.Text(status_label, size=12, color="white"),
                                            bgcolor=status_color,
                                            border_radius=8,
                                            padding=ft.Padding(left=8, top=3, right=8, bottom=3),
                                        ),
                                    ],
                                ),
                                ft.Container(height=5),
                                ft.Row(
                                    [
                                        ft.Column([
                                            ft.Text(f"{t(lang, 'total')}: {cn['total_amount']:.2f}", size=13),
                                            ft.Text(f"{t(lang, 'paid')}: {cn['paid_amount']:.2f}", size=13, color=AppTheme.SUCCESS),
                                        ]),
                                        ft.Column([
                                            ft.Text(f"{t(lang, 'remaining')}: {remaining:.2f}", size=13,
                                                    color=AppTheme.ACCENT if remaining > 0 else AppTheme.SUCCESS,
                                                    weight=ft.FontWeight.BOLD),
                                            ft.Text(cn["created_at"][:10] if cn["created_at"] else "", size=12, opacity=0.6),
                                        ]),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                            ],
                            spacing=3,
                        ),
                        padding=15,
                        on_click=lambda e, cid=cn["id"]: self._show_detail_dialog(cid),
                    ),
                    margin=ft.Margin(left=0, top=5, right=0, bottom=5),
                )
            )
        return ft.Column(cards, scroll=ft.ScrollMode.AUTO)

    def _show_add_dialog(self, e):
        lang = self._page.session.store.get("lang") or "ar"
        user_id = self._page.session.store.get("user_id")
        customers = get_customers(user_id) if user_id else []
        products = get_products(user_id) if user_id else []

        customer_dd = ft.Dropdown(
            label=t(lang, "select_customer"),
            options=[ft.dropdown.Option(str(c["id"]), c["name"]) for c in customers],
            expand=True,
        )
        new_customer_name = ft.TextField(label=t(lang, "customer_name"), text_align=ft.TextAlign.RIGHT, expand=True, visible=False)
        new_customer_phone = ft.TextField(label=t(lang, "customer_phone"), text_align=ft.TextAlign.RIGHT, expand=True, visible=False)
        add_customer_btn = ft.TextButton(t(lang, "add_customer"), on_click=lambda e: self._toggle_new_customer(new_customer_name, new_customer_phone, add_customer_btn, customer_dd))

        product_dd = ft.Dropdown(
            label=t(lang, "select_product"),
            options=[ft.dropdown.Option(str(p["id"]), f"{p['name']} - {p['price']:.2f}") for p in products],
            expand=True,
        )
        qty_inp = ft.TextField(label=t(lang, "quantity"), value="1",
                                keyboard_type=ft.KeyboardType.NUMBER, text_align=ft.TextAlign.RIGHT, width=80)
        unit_price_inp = ft.TextField(label=t(lang, "unit_price"), value="0",
                                      keyboard_type=ft.KeyboardType.NUMBER, text_align=ft.TextAlign.RIGHT, width=100)

        def on_product_select(e):
            pid = int(product_dd.value) if product_dd.value else None
            if pid:
                p = next((p for p in products if p["id"] == pid), None)
                if p:
                    unit_price_inp.value = str(p["price"])
                    self._page.update()

        product_dd.on_change = on_product_select

        items_list = ft.Column(scroll=ft.ScrollMode.AUTO)
        added_items = []
        error_text = ft.Text("", color="red", size=13, text_align=ft.TextAlign.CENTER)

        def add_item(e):
            try:
                pid = int(product_dd.value) if product_dd.value else None
                qty = float(qty_inp.value or 0)
                up = float(unit_price_inp.value or 0)
                if qty <= 0 or up <= 0 or not pid:
                    return
                p = next((p for p in products if p["id"] == pid), None)
                if not p:
                    return
                total = qty * up
                added_items.append((pid, p["name"], qty, up, total))
                items_list.controls.append(
                    ft.Row(
                        [
                            ft.Text(f"{p['name']} x{qty} = {total:.2f}", expand=True),
                            ft.IconButton(ft.Icons.CLOSE, icon_size=16,
                                          on_click=lambda e, idx=len(added_items)-1: remove_item(idx)),
                        ]
                    )
                )
                self._page.update()
            except ValueError:
                pass

        def remove_item(idx):
            if 0 <= idx < len(added_items):
                added_items.pop(idx)
                self._show_add_dialog_refresh_items(items_list, added_items, lang)
                self._page.update()

        def do_save(e):
            nonlocal customers
            try:
                if not added_items:
                    return
                cid = None
                if new_customer_name.visible and new_customer_name.value.strip():
                    cid = add_customer(user_id, new_customer_name.value.strip(), new_customer_phone.value.strip())
                    customers = get_customers(user_id)
                    customer_dd.options = [ft.dropdown.Option(str(c["id"]), c["name"]) for c in customers]
                    customer_dd.value = str(cid)
                elif customer_dd.value:
                    cid = int(customer_dd.value)
                if not cid:
                    return

                add_credit_note(user_id, cid, added_items)

                self._page.pop_dialog()
                self._refresh()
            except ValueError as ex:
                error_text.value = str(ex) if str(ex) else t(lang, "error")
                error_text.update()

        content_items = ft.Column(
            [
                ft.Row([customer_dd], vertical_alignment=ft.CrossAxisAlignment.START),
                new_customer_name,
                new_customer_phone,
                add_customer_btn,
                ft.Divider(),
                ft.Row([product_dd], vertical_alignment=ft.CrossAxisAlignment.START),
                ft.Row([qty_inp, unit_price_inp, ft.IconButton(ft.Icons.ADD_CIRCLE, on_click=add_item)]),
                items_list,
                error_text,
            ],
            scroll=ft.ScrollMode.AUTO,
        )

        dlg = ft.AlertDialog(
            title=ft.Text(t(lang, "add_credit_note")),
            content=ft.Container(content=content_items, height=400),
            actions=[
                ft.TextButton(t(lang, "cancel"), on_click=lambda e: self._page.pop_dialog()),
                ft.FilledButton(t(lang, "save"), on_click=do_save),
            ],
        )
        self._page.show_dialog(dlg)

    def _show_add_dialog_refresh_items(self, items_list, added_items, lang):
        items_list.controls.clear()
        for idx, item in enumerate(added_items):
            items_list.controls.append(
                ft.Row(
                    [
                        ft.Text(f"{item[1]} x{item[2]} = {item[4]:.2f}", expand=True),
                        ft.IconButton(ft.Icons.CLOSE, icon_size=16,
                                      on_click=lambda e, i=idx: self._remove_item_from_list(i, items_list, added_items, lang)),
                    ]
                )
            )

    def _remove_item_from_list(self, idx, items_list, added_items, lang):
        if 0 <= idx < len(added_items):
            added_items.pop(idx)
            self._show_add_dialog_refresh_items(items_list, added_items, lang)
            self._page.update()

    def _toggle_new_customer(self, name_inp, phone_inp, btn, dd):
        is_visible = not name_inp.visible
        name_inp.visible = is_visible
        phone_inp.visible = is_visible
        dd.visible = not is_visible
        btn.text = t(self._page.session.store.get("lang") or "ar", "select_customer") if is_visible else t(self._page.session.store.get("lang") or "ar", "add_customer")
        self._page.update()

    def _show_detail_dialog(self, cn_id):
        lang = self._page.session.store.get("lang") or "ar"
        cn = get_credit_note(cn_id)
        if not cn:
            return
        items = get_credit_note_items(cn_id)
        payments = get_credit_payments(cn_id)
        remaining = cn["total_amount"] - cn["paid_amount"]
        is_open = cn["status"] == "open"

        remaining_color = AppTheme.ACCENT if remaining > 0 else AppTheme.SUCCESS
        status_color = AppTheme.ACCENT if is_open else AppTheme.SUCCESS

        items_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text(t(lang, "product_name"))),
                ft.DataColumn(ft.Text(t(lang, "quantity"))),
                ft.DataColumn(ft.Text(t(lang, "unit_price"))),
                ft.DataColumn(ft.Text(t(lang, "total"))),
            ],
            rows=[
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(it["product_name"])),
                    ft.DataCell(ft.Text(str(it["quantity"]))),
                    ft.DataCell(ft.Text(f"{it['unit_price']:.2f}")),
                    ft.DataCell(ft.Text(f"{it['total_price']:.2f}")),
                ])
                for it in items
            ],
        )

        payments_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text(t(lang, "amount"))),
                ft.DataColumn(ft.Text(t(lang, "date"))),
                ft.DataColumn(ft.Text(t(lang, "note"))),
            ],
            rows=[
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(f"{pm['amount']:.2f}", color=AppTheme.SUCCESS)),
                    ft.DataCell(ft.Text(pm["date"][:10] if pm["date"] else "")),
                    ft.DataCell(ft.Text(pm.get("note", ""))),
                ])
                for pm in payments
            ] if payments else [ft.DataRow(cells=[ft.DataCell(ft.Text(t(lang, "no_data"), opacity=0.5))] * 3)],
        )

        header = ft.Row(
            [
                ft.Text(cn["customer_name"], size=18, weight=ft.FontWeight.BOLD, expand=True),
                ft.Container(
                    content=ft.Text(t(lang, "open" if is_open else "closed"), size=12, color="white"),
                    bgcolor=status_color,
                    border_radius=8,
                    padding=ft.Padding(left=8, top=3, right=8, bottom=3),
                ),
            ],
        )

        info = ft.Column(
            [
                ft.Row([ft.Text(f"{t(lang, 'total')}: {cn['total_amount']:.2f}", weight=ft.FontWeight.BOLD)]),
                ft.Row([ft.Text(f"{t(lang, 'paid')}: {cn['paid_amount']:.2f}", color=AppTheme.SUCCESS)]),
                ft.Row([ft.Text(f"{t(lang, 'remaining')}: {remaining:.2f}", color=remaining_color, weight=ft.FontWeight.BOLD)]),
                ft.Row([ft.Text(f"{cn['created_at'][:10] if cn['created_at'] else ''}", opacity=0.6)]),
            ],
            spacing=2,
        )

        content = ft.Column(
            [
                header,
                ft.Divider(),
                info,
                ft.Divider(),
                ft.Text(t(lang, "credit_items"), size=16, weight=ft.FontWeight.BOLD),
                items_table,
                ft.Divider(),
                ft.Text(t(lang, "payment_history"), size=16, weight=ft.FontWeight.BOLD),
                payments_table,
            ],
            scroll=ft.ScrollMode.AUTO,
        )

        actions = [ft.TextButton(t(lang, "cancel"), on_click=lambda e: self._page.pop_dialog())]

        if is_open:
            actions.insert(0, ft.FilledButton(t(lang, "add_payment"), on_click=lambda e: self._show_payment_dialog(cn_id)))

        dlg = ft.AlertDialog(
            title=ft.Text(f"{t(lang, 'credit_notes')} #{cn_id}"),
            content=ft.Container(content=content, width=400, height=500),
            actions=actions,
        )
        self._page.show_dialog(dlg)

    def _show_payment_dialog(self, cn_id):
        lang = self._page.session.store.get("lang") or "ar"
        cn = get_credit_note(cn_id)
        if not cn:
            return
        remaining = cn["total_amount"] - cn["paid_amount"]
        amt_inp = ft.TextField(label=t(lang, "amount"), value=str(remaining),
                                keyboard_type=ft.KeyboardType.NUMBER, text_align=ft.TextAlign.RIGHT, expand=True)
        note_inp = ft.TextField(label=t(lang, "note"), text_align=ft.TextAlign.RIGHT, expand=True)
        remaining_text = ft.Text(f"{t(lang, 'remaining')}: {remaining:.2f}", size=14, color=AppTheme.ACCENT)
        error_text = ft.Text("", color="red", size=13, text_align=ft.TextAlign.CENTER)

        def do_pay(e):
            try:
                amt = float(amt_inp.value or 0)
                add_credit_payment(cn_id, amt, note_inp.value.strip())
                self._page.pop_dialog()
                self._page.pop_dialog()
                self._refresh()
            except ValueError as ex:
                error_text.value = str(ex) if str(ex) else t(lang, "error")
                error_text.update()

        dlg = ft.AlertDialog(
            title=ft.Text(t(lang, "add_payment")),
            content=ft.Column([remaining_text, amt_inp, note_inp, error_text]),
            actions=[
                ft.TextButton(t(lang, "cancel"), on_click=lambda e: self._page.pop_dialog()),
                ft.FilledButton(t(lang, "save"), on_click=do_pay),
            ],
        )
        self._page.show_dialog(dlg)

    def _refresh(self):
        user_id = self._page.session.store.get("user_id")
        self.credit_notes = get_credit_notes(user_id, self._status_filter) if user_id else []
        self._build()
        self.update()
