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
    def get_theme(theme_mode: str, lang: str = "ar") -> ft.Theme:
        is_dark = theme_mode == "dark"
        text_color = AppTheme.TEXT_DARK if is_dark else AppTheme.TEXT_LIGHT
        font = ARABIC_FONT if lang == "ar" else None

        def ts():
            return ft.TextStyle(color=text_color, font_family=font)

        return ft.Theme(
            color_scheme_seed=AppTheme.PRIMARY,
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
                display_large=ts(),
                display_medium=ts(),
                display_small=ts(),
                headline_large=ts(),
                headline_medium=ts(),
                headline_small=ts(),
                label_large=ts(),
                label_medium=ts(),
                label_small=ts(),
                title_large=ts(),
                title_medium=ts(),
                title_small=ts(),
            ),
        )
