import flet as ft
import base64
from app.database import (get_products, add_product, update_product, delete_product,
                          add_stock_movement, get_stock_movements_by_product, get_product, add_transaction,
                          get_customers, add_customer, add_credit_note)
from app.translations import get_translation as t
from app.theme import AppTheme
from app.currency import get_currency_symbol
from app.barcode import generate_barcode_image, generate_unique_code
from app.printing import print_stickers as _print_stickers


class StockScreen(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self._page = page
        self.expand = True
        self.bgcolor = page.theme.bgcolor if hasattr(page.theme, "bgcolor") else None
        self._search_query = ""
        self._build()

    def _build(self):
        lang = self._page.session.store.get("lang") or "ar"
        self.products = get_products(self._page.session.store.get("user_id")) if self._page.session.store.get("user_id") else []
        self.content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(t(lang, "products"), size=24, weight=ft.FontWeight.BOLD),
                        ft.Row(
                            [
                                ft.IconButton(ft.Icons.LOCAL_PRINT_SHOP, tooltip=t(lang, "print_stickers"), on_click=self._show_print_dialog),
                                ft.FloatingActionButton(
                                    icon=ft.Icons.ADD,
                                    on_click=self._show_add_dialog,
                                ),
                            ],
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(height=5),
                ft.Row(
                    [
                        ft.TextField(
                            hint_text=t(lang, "search"),
                            prefix_icon=ft.Icons.SEARCH,
                            expand=True,
                            on_change=self._on_search_change,
                            text_align=ft.TextAlign.RIGHT,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CLEAR,
                            on_click=self._clear_search,
                        ),
                    ],
                ),
                ft.Container(height=5),
                self._build_product_list(lang),
            ],
            scroll=ft.ScrollMode.AUTO,
        )

    def _build_product_list(self, lang):
        filtered = [p for p in self.products
                    if not self._search_query or self._search_query.lower() in p["name"].lower()
                    or self._search_query.lower() in p.get("category", "").lower()]
        if not filtered:
            return ft.Text(t(lang, "no_data"), opacity=0.5, italic=True)
        cards = []
        for p in filtered:
            is_low = p["quantity"] <= p["low_stock_qty"]
            cards.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text(p["name"], size=16, weight=ft.FontWeight.BOLD, expand=True),
                                        ft.IconButton(ft.Icons.EDIT, on_click=lambda e, pid=p["id"]: self._show_edit_dialog(pid)),
                                        ft.IconButton(ft.Icons.DELETE, on_click=lambda e, pid=p["id"]: self._confirm_delete(pid)),
                                    ]
                                ),
                ft.Row(
                    [
                        ft.Text(f"{t(lang, 'quantity')}: {p['quantity']}"),
                        ft.Text(f"{t(lang, 'price')}: {p['price']:.2f} {get_currency_symbol(self._page)}"),
                        ft.Text(f"{t(lang, 'category')}: {p.get('category', '')}"),
                    ],
                    spacing=20,
                ),
                ft.Row(
                    [
                        ft.Text(f"{t(lang, 'buying_price')}: {p.get('buying_price', 0):.2f} {get_currency_symbol(self._page)}"),
                        ft.Text(f"{t(lang, 'supplier_name')}: {p.get('supplier_name', '') or '-'}"),
                    ],
                    spacing=20,
                ) if p.get('buying_price', 0) > 0 else ft.Container(),
                ft.Row(
                    [
                        ft.Text(f"{t(lang, 'barcode')}: {p.get('barcode', '')}", size=12, opacity=0.7),
                    ],
                ) if p.get('barcode', '') else ft.Container(),
                                ft.Row(
                                    [
                                        ft.IconButton(
                                            icon=ft.Icons.SHOPPING_CART,
                                            expand=True,
                                            on_click=lambda e, pid=p["id"]: self._show_sell_dialog(pid),
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.CREDIT_CARD,
                                            expand=True,
                                            tooltip=t(lang, "sell_on_credit"),
                                            on_click=lambda e, pid=p["id"]: self._show_credit_sell_dialog(pid),
                                        ),
                                    ],
                                    spacing=5,
                                ),
                                ft.Row(
                                    [
                                ft.IconButton(
                                    icon=ft.Icons.ADD_CIRCLE,
                                    expand=True,
                                    on_click=lambda e, pid=p["id"]: self._show_movement_dialog(pid, "in"),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.REMOVE_CIRCLE,
                                    expand=True,
                                    on_click=lambda e, pid=p["id"]: self._show_movement_dialog(pid, "out"),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.HISTORY,
                                    expand=True,
                                    on_click=lambda e, pid=p["id"]: self._show_movement_history(pid),
                                ),
                                    ],
                                    spacing=5,
                                ),
                                ft.Row(
                                    [ft.Icon(ft.Icons.WARNING, color=AppTheme.LOW_STOCK, size=16),
                                     ft.Text(t(lang, "low_stock_alerts"), size=12, color=AppTheme.LOW_STOCK)]
                                ) if is_low else ft.Container(),
                            ],
                            spacing=5,
                        ),
                        padding=15,
                    ),
                    margin=ft.Margin(left=0, top=5, right=0, bottom=5),
                )
            )
        return ft.Column(cards, scroll=ft.ScrollMode.AUTO)

    def _on_search_change(self, e):
        self._search_query = e.control.value or ""
        self._refresh()

    def _clear_search(self, e):
        self._search_query = ""
        self._build()
        self.update()

    def _show_add_dialog(self, e):
        self._show_product_dialog()

    def _show_edit_dialog(self, product_id):
        p = get_product(product_id)
        if p:
            self._show_product_dialog(product=p)

    def _confirm_delete(self, product_id):
        lang = self._page.session.store.get("lang") or "ar"
        dlg = ft.AlertDialog(
            title=ft.Text(t(lang, "confirm_delete")),
            content=ft.Text(t(lang, "confirm_delete_msg")),
            actions=[
                ft.TextButton(t(lang, "cancel"), on_click=lambda e: self._page.pop_dialog()),
                ft.FilledButton(t(lang, "delete"), on_click=lambda e: self._do_delete(product_id, dlg)),
            ],
        )
        self._page.show_dialog(dlg)

    def _do_delete(self, product_id, dlg):
        delete_product(product_id)
        self._page.pop_dialog()
        self._refresh()

    def _show_product_dialog(self, product=None):
        lang = self._page.session.store.get("lang") or "ar"
        is_edit = product is not None
        name_inp = ft.TextField(label=t(lang, "product_name"), value=product["name"] if is_edit else "",
                                text_align=ft.TextAlign.RIGHT, expand=True)
        qty_inp = ft.TextField(label=t(lang, "quantity"), value=str(product["quantity"]) if is_edit else "0",
                                keyboard_type=ft.KeyboardType.NUMBER, text_align=ft.TextAlign.RIGHT, expand=True)
        price_inp = ft.TextField(label=t(lang, "price"), value=str(product["price"]) if is_edit else "0",
                                 keyboard_type=ft.KeyboardType.NUMBER, text_align=ft.TextAlign.RIGHT, expand=True)
        buying_price_inp = ft.TextField(label=t(lang, "buying_price"), value=str(product.get("buying_price", 0)) if is_edit else "0",
                                        keyboard_type=ft.KeyboardType.NUMBER, text_align=ft.TextAlign.RIGHT, expand=True)
        cat_inp = ft.TextField(label=t(lang, "category"), value=product.get("category", "") if is_edit else "",
                               text_align=ft.TextAlign.RIGHT, expand=True)
        pkg_inp = ft.TextField(label=t(lang, "packaging"), value=product.get("packaging", "") if is_edit else "",
                               text_align=ft.TextAlign.RIGHT, expand=True)
        desc_inp = ft.TextField(label=t(lang, "description"), value=product.get("description", "") if is_edit else "",
                                multiline=True, text_align=ft.TextAlign.RIGHT, expand=True)
        low_inp = ft.TextField(label=t(lang, "low_stock_qty"),
                               value=str(product["low_stock_qty"]) if is_edit else "5",
                               keyboard_type=ft.KeyboardType.NUMBER, text_align=ft.TextAlign.RIGHT, expand=True)
        supplier_inp = ft.TextField(label=t(lang, "supplier_name"), value=product.get("supplier_name", "") if is_edit else "",
                                    text_align=ft.TextAlign.RIGHT, expand=True)
        supplier_wp_inp = ft.TextField(label=t(lang, "supplier_whatsapp"), value=product.get("supplier_whatsapp", "") if is_edit else "",
                                       text_align=ft.TextAlign.RIGHT, expand=True)
        supplier_em_inp = ft.TextField(label=t(lang, "supplier_email"), value=product.get("supplier_email", "") if is_edit else "",
                                       text_align=ft.TextAlign.RIGHT, expand=True)
        barcode_inp = ft.TextField(label=t(lang, "barcode"), value=product.get("barcode", "") if is_edit else "",
                                    text_align=ft.TextAlign.RIGHT, expand=True)
        barcode_img = ft.Image(src="", visible=False, height=50, fit=ft.BoxFit.CONTAIN)
        error_text = ft.Text("", color="red", size=13, text_align=ft.TextAlign.CENTER)

        def generate_code_action(e):
            existing = {p.get("barcode", "") for p in self.products if p.get("barcode")}
            code = generate_unique_code(existing)
            barcode_inp.value = code
            img_bytes = generate_barcode_image(code)
            b64 = base64.b64encode(img_bytes).decode()
            barcode_img.src_base64 = b64
            barcode_img.visible = True
            self._page.update()

        def on_barcode_change(e):
            val = barcode_inp.value.strip()
            if val:
                try:
                    img_bytes = generate_barcode_image(val)
                    b64 = base64.b64encode(img_bytes).decode()
                    barcode_img.src_base64 = b64
                    barcode_img.visible = True
                except Exception:
                    barcode_img.visible = False
            else:
                barcode_img.visible = False
            self._page.update()

        barcode_inp.on_change = on_barcode_change

        if is_edit and product.get("barcode"):
            try:
                img_bytes = generate_barcode_image(product["barcode"])
                b64 = base64.b64encode(img_bytes).decode()
                barcode_img.src_base64 = b64
                barcode_img.visible = True
            except Exception:
                pass

        def save_action(e):
            try:
                name_val = name_inp.value.strip()
                if not name_val:
                    error_text.value = t(lang, "fill_fields")
                    error_text.update()
                    return
                data = dict(
                    name=name_val,
                    quantity=float(qty_inp.value or 0),
                    price=float(price_inp.value or 0),
                    buying_price=float(buying_price_inp.value or 0),
                    category=cat_inp.value.strip(),
                    packaging=pkg_inp.value.strip(),
                    description=desc_inp.value.strip(),
                    low_stock_qty=float(low_inp.value or 5),
                    supplier_name=supplier_inp.value.strip(),
                    supplier_whatsapp=supplier_wp_inp.value.strip(),
                    supplier_email=supplier_em_inp.value.strip(),
                    barcode=barcode_inp.value.strip(),
                )
                if is_edit:
                    update_product(product["id"], **data)
                else:
                    add_product(self._page.session.store.get("user_id"), **data)
                self._page.pop_dialog()
                self._refresh()
            except ValueError as ex:
                error_text.value = str(ex) if str(ex) else t(lang, "error")
                error_text.update()

        dlg = ft.AlertDialog(
            title=ft.Text(t(lang, "edit_product" if is_edit else "add_product")),
            content=ft.Column([name_inp, qty_inp, price_inp, buying_price_inp, cat_inp, pkg_inp, desc_inp, low_inp,
                               supplier_inp, supplier_wp_inp, supplier_em_inp,
                               ft.Row([barcode_inp, ft.IconButton(ft.Icons.QR_CODE_SCANNER, on_click=generate_code_action)]),
                               barcode_img, error_text],
                              scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton(t(lang, "cancel"), on_click=lambda e: self._page.pop_dialog()),
                ft.FilledButton(t(lang, "save"), on_click=save_action),
            ],
        )
        self._page.show_dialog(dlg)

    def _show_sell_dialog(self, product_id):
        p = get_product(product_id)
        if not p:
            return
        lang = self._page.session.store.get("lang") or "ar"
        price_per_unit = p["price"]
        qty_inp = ft.TextField(label=t(lang, "sell_qty"), value="1",
                                keyboard_type=ft.KeyboardType.NUMBER, text_align=ft.TextAlign.RIGHT, expand=True)
        total_text = ft.Text(f"{t(lang, 'amount')}: {price_per_unit:.2f} {get_currency_symbol(self._page)}",
                             size=16, weight=ft.FontWeight.BOLD)
        error_text = ft.Text("", color="red", size=13, text_align=ft.TextAlign.CENTER)

        def on_qty_change(e):
            try:
                q = float(qty_inp.value or 0)
                total_text.value = f"{t(lang, 'amount')}: {q * price_per_unit:.2f} {get_currency_symbol(self._page)}"
                total_text.update()
            except ValueError:
                pass

        qty_inp.on_change = on_qty_change

        def do_sell(e):
            try:
                qty = float(qty_inp.value or 0)
                if qty <= 0:
                    return
                total = qty * price_per_unit
                add_stock_movement(product_id, self._page.session.store.get("user_id"), "out", qty, note="Sale")
                add_transaction(self._page.session.store.get("user_id"), "income", total,
                                "Sale", f"Sold {qty} x {p['name']}")
                self._page.pop_dialog()
                self._refresh()
            except ValueError as ex:
                error_text.value = str(ex) if str(ex) else t(lang, "error")
                error_text.update()

        dlg = ft.AlertDialog(
            title=ft.Text(f"{t(lang, 'sell')} - {p['name']}"),
            content=ft.Column([qty_inp, total_text, error_text], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions=[
                ft.TextButton(t(lang, "cancel"), on_click=lambda e: self._page.pop_dialog()),
                ft.FilledButton(t(lang, "save"), on_click=do_sell),
            ],
        )
        self._page.show_dialog(dlg)

    def _show_credit_sell_dialog(self, product_id):
        p = get_product(product_id)
        if not p:
            return
        lang = self._page.session.store.get("lang") or "ar"
        user_id = self._page.session.store.get("user_id")
        customers = get_customers(user_id) if user_id else []
        price_per_unit = p["price"]

        qty_inp = ft.TextField(label=t(lang, "sell_qty"), value="1",
                                keyboard_type=ft.KeyboardType.NUMBER, text_align=ft.TextAlign.RIGHT, expand=True)
        total_text = ft.Text(f"{t(lang, 'amount')}: {price_per_unit:.2f} {get_currency_symbol(self._page)}",
                             size=16, weight=ft.FontWeight.BOLD)
        error_text = ft.Text("", color="red", size=13, text_align=ft.TextAlign.CENTER)

        customer_dd = ft.Dropdown(
            label=t(lang, "select_customer"),
            options=[ft.dropdown.Option(str(c["id"]), c["name"]) for c in customers],
            expand=True,
        )
        new_name = ft.TextField(label=t(lang, "customer_name"), text_align=ft.TextAlign.RIGHT, expand=True, visible=not customers)
        new_phone = ft.TextField(label=t(lang, "customer_phone"), text_align=ft.TextAlign.RIGHT, expand=True, visible=not customers)
        toggle_btn = ft.TextButton(
            t(lang, "add_customer") if customers else t(lang, "select_customer"),
            on_click=lambda e: _toggle_customer(),
        )

        def _toggle_customer():
            if new_name.visible:
                new_name.visible = False
                new_phone.visible = False
                customer_dd.visible = True
                toggle_btn.text = t(lang, "add_customer")
            else:
                new_name.visible = True
                new_phone.visible = True
                customer_dd.visible = False
                toggle_btn.text = t(lang, "select_customer")
            self._page.update()

        def on_qty_change(e):
            try:
                q = float(qty_inp.value or 0)
                total_text.value = f"{t(lang, 'amount')}: {q * price_per_unit:.2f} {get_currency_symbol(self._page)}"
                total_text.update()
            except ValueError:
                pass
        qty_inp.on_change = on_qty_change

        def do_credit_sell(e):
            try:
                qty = float(qty_inp.value or 0)
                if qty <= 0:
                    return
                total = qty * price_per_unit
                cid = None
                if new_name.visible and new_name.value.strip():
                    cid = add_customer(user_id, new_name.value.strip(), new_phone.value.strip())
                elif customer_dd.value:
                    cid = int(customer_dd.value)
                else:
                    return
                items = [(product_id, p["name"], qty, price_per_unit, total)]
                add_credit_note(user_id, cid, items)
                self._page.pop_dialog()
                self._refresh()
            except ValueError as ex:
                error_text.value = str(ex) if str(ex) else t(lang, "error")
                error_text.update()

        dlg = ft.AlertDialog(
            title=ft.Text(f"{t(lang, 'sell_on_credit')} - {p['name']}"),
            content=ft.Column(
                [
                    ft.Row([customer_dd], vertical_alignment=ft.CrossAxisAlignment.START),
                    new_name, new_phone, toggle_btn,
                    ft.Divider(),
                    qty_inp, total_text, error_text,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            ),
            actions=[
                ft.TextButton(t(lang, "cancel"), on_click=lambda e: self._page.pop_dialog()),
                ft.FilledButton(t(lang, "save"), on_click=do_credit_sell),
            ],
        )
        self._page.show_dialog(dlg)

    def _show_movement_dialog(self, product_id, mtype):
        lang = self._page.session.store.get("lang") or "ar"
        qty_inp = ft.TextField(label=t(lang, "quantity"), value="0",
                               keyboard_type=ft.KeyboardType.NUMBER, text_align=ft.TextAlign.RIGHT, expand=True)
        note_inp = ft.TextField(label=t(lang, "note"), text_align=ft.TextAlign.RIGHT, expand=True)
        error_text = ft.Text("", color="red", size=13, text_align=ft.TextAlign.CENTER)

        def save_movement(e):
            try:
                qty = float(qty_inp.value or 0)
                add_stock_movement(product_id, self._page.session.store.get("user_id"), mtype, qty, note_inp.value.strip())
                self._page.pop_dialog()
                self._refresh()
            except ValueError as ex:
                error_text.value = str(ex) if str(ex) else t(lang, "error")
                error_text.update()

        dlg = ft.AlertDialog(
            title=ft.Text(t(lang, "stock_in" if mtype == "in" else "stock_out")),
            content=ft.Column([qty_inp, note_inp, error_text]),
            actions=[
                ft.TextButton(t(lang, "cancel"), on_click=lambda e: self._page.pop_dialog()),
                ft.FilledButton(t(lang, "save"), on_click=save_movement),
            ],
        )
        self._page.show_dialog(dlg)

    def _show_movement_history(self, product_id):
        lang = self._page.session.store.get("lang") or "ar"
        user_id = self._page.session.store.get("user_id")
        p_movements = get_stock_movements_by_product(user_id, product_id, 50) if user_id else []

        if not p_movements:
            content = ft.Text(t(lang, "no_movements"), opacity=0.5, italic=True)
        else:
            rows = []
            for m in p_movements:
                color = AppTheme.SUCCESS if m["type"] == "in" else AppTheme.ERROR
                label = t(lang, "stock_in" if m["type"] == "in" else "stock_out")
                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(label, color=color)),
                            ft.DataCell(ft.Text(str(m["quantity"]))),
                            ft.DataCell(ft.Text(m["date"][:16] if m["date"] else "")),
                            ft.DataCell(ft.Text(m.get("note", ""))),
                        ]
                    )
                )
            content = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text(t(lang, "movement_type"))),
                    ft.DataColumn(ft.Text(t(lang, "quantity"))),
                    ft.DataColumn(ft.Text(t(lang, "date"))),
                    ft.DataColumn(ft.Text(t(lang, "note"))),
                ],
                rows=rows,
            )

        dlg = ft.AlertDialog(
            title=ft.Text(t(lang, "movement_history")),
            content=ft.Container(content=content),
            actions=[ft.TextButton(t(lang, "cancel"), on_click=lambda e: self._page.pop_dialog())],
        )
        self._page.show_dialog(dlg)

    def _show_print_dialog(self, e):
        lang = self._page.session.store.get("lang") or "ar"
        filtered = [p for p in self.products
                    if not self._search_query or self._search_query.lower() in p["name"].lower()
                    or self._search_query.lower() in p.get("category", "").lower()]
        products_with_barcode = [p for p in filtered if p.get("barcode", "")]
        if not products_with_barcode:
            self._page.show_dialog(ft.SnackBar(ft.Text(t(lang, "no_data"))))
            return

        checks = {p["id"]: ft.Checkbox(label=p["name"], value=True) for p in products_with_barcode}

        def do_print(e):
            selected = [p for p in products_with_barcode if checks[p["id"]].value]
            if not selected:
                return
            self._page.pop_dialog()
            _print_stickers(selected)

        dlg = ft.AlertDialog(
            title=ft.Text(t(lang, "print_stickers")),
            content=ft.Column(
                list(checks.values()),
                scroll=ft.ScrollMode.AUTO,
                height=400,
            ),
            actions=[
                ft.TextButton(t(lang, "cancel"), on_click=lambda e: self._page.pop_dialog()),
                ft.FilledButton(t(lang, "print_stickers"), on_click=do_print),
            ],
        )
        self._page.show_dialog(dlg)

    def _refresh(self):
        self.products = get_products(self._page.session.store.get("user_id")) if self._page.session.store.get("user_id") else []
        self._build()
        self.update()
