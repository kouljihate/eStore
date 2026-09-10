import flet as ft

ARABIC_FONT = "VIP_RAWY_THIN"


def get_font_family(lang: str = "ar") -> str:
    return ARABIC_FONT if lang == "ar" else None


class AppTheme:
    PRIMARY = "#00897B"
    PRIMARY_DARK = "#00695C"
    PRIMARY_LIGHT = "#4DB6AC"
    ACCENT = "#FF5722"
    ACCENT_DARK = "#D84315"
    ACCENT_LIGHT = "#FF8A65"
    BG_LIGHT = "#F5F5F5"
    BG_DARK = "#121212"
    SURFACE_LIGHT = "#FFFFFF"
    SURFACE_DARK = "#1E1E1E"
    TEXT_LIGHT = "#212121"
    TEXT_DARK = "#E0E0E0"
    ERROR = "#D32F2F"
    SUCCESS = "#388E3C"
    WARNING = "#F57C00"
    LOW_STOCK = "#FF6F00"

    @staticmethod
    def _font(lang: str = "ar"):
        if lang == "ar":
            return ft.TextStyle(font_family=ARABIC_FONT)
        return None

    @staticmethod
    def get_theme(theme_mode: str, lang: str = "ar") -> ft.Theme:
        is_dark = theme_mode == "dark"
        font = AppTheme._font(lang)
        text_color = AppTheme.TEXT_DARK if is_dark else AppTheme.TEXT_LIGHT

        def ts(**kwargs):
            if font:
                return ft.TextStyle(color=text_color, font_family=font.font_family)
            return ft.TextStyle(color=text_color)

        return ft.Theme(
            color_scheme_seed=AppTheme.PRIMARY,
            brightness=ft.Brightness.DARK if is_dark else ft.Brightness.LIGHT,
            primary_color=AppTheme.PRIMARY,
            primary_color_dark=AppTheme.PRIMARY_DARK,
            primary_color_light=AppTheme.PRIMARY_LIGHT,
            secondary_color=AppTheme.ACCENT,
            bgcolor=AppTheme.BG_DARK if is_dark else AppTheme.BG_LIGHT,
            surface_tint_color=AppTheme.SURFACE_DARK if is_dark else AppTheme.SURFACE_LIGHT,
            error_color=AppTheme.ERROR,
            text_theme=ft.TextTheme(
                body_large=ts(),
                body_medium=ts(),
                body_small=ts(),
                headline_large=ts(),
                headline_medium=ts(),
                headline_small=ts(),
                title_large=ts(),
                title_medium=ts(),
                title_small=ts(),
            ),
        )
