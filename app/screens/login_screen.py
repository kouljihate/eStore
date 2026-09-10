import flet as ft
from app.database import user_count, create_user, authenticate_user
from app.translations import get_translation as t
from app.version import VERSION


class LoginScreen(ft.Container):
    def __init__(self, page: ft.Page, on_login_success):
        super().__init__()
        self._page = page
        self.on_login_success = on_login_success
        self.expand = True
        self.bgcolor = page.theme.bgcolor if hasattr(page.theme, "bgcolor") else None
        self._build()

    def _build(self):
        lang = self._page.session.store.get("lang") or "ar"
        is_first_run = user_count() == 0
        self.show_login = not is_first_run

        self.email_input = ft.TextField(
            label=t(lang, "email"),
            prefix_icon=ft.Icons.EMAIL,
            keyboard_type=ft.KeyboardType.EMAIL,
            expand=True,
            text_align=ft.TextAlign.RIGHT,
        )
        self.password_input = ft.TextField(
            label=t(lang, "password"),
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            expand=True,
            text_align=ft.TextAlign.RIGHT,
        )
        self.name_input = ft.TextField(
            label=t(lang, "name"),
            prefix_icon=ft.Icons.PERSON,
            expand=True,
            visible=is_first_run,
            text_align=ft.TextAlign.RIGHT,
        )
        self.error_text = ft.Text("", color="red", size=13, text_align=ft.TextAlign.CENTER)
        self.title_text = ft.Text(
            t(lang, "first_run_title" if is_first_run else "login"),
            size=28,
            weight=ft.FontWeight.BOLD,
        )
        self.subtitle_text = ft.Text(
            t(lang, "first_run_msg" if is_first_run else "login_subtitle"),
            size=14,
            opacity=0.7,
            text_align=ft.TextAlign.CENTER,
        )
        self.action_btn = ft.FilledButton(
            t(lang, "register_btn" if is_first_run else "login_btn"),
            expand=True,
            height=48,
            on_click=self._handle_action,
        )
        self.toggle_text = ft.TextButton(
            t(lang, "has_account" if is_first_run else "no_account"),
            on_click=self._toggle_mode,
        )

        self.lang_bar = ft.SegmentedButton(
            selected=[lang],
            segments=[
                ft.Segment("en", label=ft.Text("EN", size=10)),
                ft.Segment("ar", label=ft.Text("AR", size=10)),
                ft.Segment("fr", label=ft.Text("FR", size=10)),
            ],
            on_change=self._on_lang_change,
        )

        self.content = ft.Stack(
            [
                ft.Column(
                    [
                        ft.Container(height=60),
                        ft.Icon(ft.Icons.STORE, size=64, color=ft.Colors.TEAL),
                        ft.Container(height=10),
                        self.title_text,
                        self.subtitle_text,
                        ft.Container(height=20),
                        self.name_input,
                        self.email_input,
                        self.password_input,
                        self.error_text,
                        ft.Container(height=10),
                        self.action_btn,
                        self.toggle_text,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    scroll=ft.ScrollMode.AUTO,
                ),
                ft.Container(
                    content=self.lang_bar,
                    left=5,
                    bottom=5,
                ),
                ft.Text(f"v{VERSION}", size=11, opacity=0.5, right=10, bottom=5),
            ],
            expand=True,
        )

    def _on_lang_change(self, e):
        selected = e.data
        lang = "ar"
        if "en" in selected:
            lang = "en"
        elif "fr" in selected:
            lang = "fr"
        self._page.session.store.set("lang", lang)
        self._page.rtl = lang == "ar"
        self._build()
        self.update()

    def _handle_action(self, e):
        lang = self._page.session.store.get("lang") or "ar"
        name = self.name_input.value.strip()
        email = self.email_input.value.strip()
        password = self.password_input.value.strip()

        if not email or not password:
            self.error_text.value = t(lang, "fill_fields")
            self.update()
            return

        if self.show_login:
            user = authenticate_user(email, password)
            if user:
                self._page.session.store.set("user_id", user["id"])
                self._page.session.store.set("user_name", user["name"])
                self.on_login_success()
            else:
                self.error_text.value = t(lang, "wrong_credentials")
                self.update()
        else:
            if not name:
                self.error_text.value = t(lang, "fill_fields")
                self.update()
                return
            user_id = create_user(name, email, password)
            if user_id:
                self._page.session.store.set("user_id", user_id)
                self._page.session.store.set("user_name", name)
                self.on_login_success()
            else:
                self.error_text.value = t(lang, "email_exists")
                self.update()

    def _toggle_mode(self, e):
        lang = self._page.session.store.get("lang") or "ar"
        self.show_login = not self.show_login
        self.title_text.value = t(lang, "login" if self.show_login else "register")
        self.subtitle_text.value = t(lang, "login_subtitle" if self.show_login else "register_subtitle")
        self.name_input.visible = not self.show_login
        self.action_btn.text = t(lang, "login_btn" if self.show_login else "register_btn")
        self.toggle_text.text = t(lang, "no_account" if self.show_login else "has_account")
        self.error_text.value = ""
        self.update()
