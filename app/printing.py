import io
import os
import tempfile
import subprocess
from fpdf import FPDF
from app.barcode import generate_barcode_image


STICKER_W = 95
STICKER_H = 42
MARGIN = 5
COLS = 2
ROWS = 5


def print_stickers(products: list):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)
    x_start = MARGIN
    y_start = MARGIN

    for idx, p in enumerate(products):
        col = idx % COLS
        row = (idx // COLS) % ROWS
        if col == 0 and row == 0 and idx > 0:
            pdf.add_page()

        x = x_start + col * (STICKER_W + 3)
        y = y_start + row * (STICKER_H + 3)

        pdf.set_xy(x, y)
        pdf.set_font("Helvetica", "B", 9)
        name = p["name"][:28]
        pdf.cell(STICKER_W, 4, name, align="C")

        pdf.set_xy(x, y + 5)
        pdf.set_font("Helvetica", "", 7)
        price_text = f"Price: {p.get('price', 0):.2f}"
        pdf.cell(STICKER_W, 3, price_text, align="C")

        barcode = p.get("barcode", "")
        if barcode:
            try:
                img_bytes = generate_barcode_image(barcode)
                img_path = os.path.join(tempfile.gettempdir(), f"bc_{p['id']}.png")
                with open(img_path, "wb") as f:
                    f.write(img_bytes)
                pdf.image(img_path, x=x + 8, y=y + 10, w=STICKER_W - 16, h=18)
                os.remove(img_path)
            except Exception:
                pass

        pdf.set_xy(x, y + 30)
        pdf.set_font("Helvetica", "", 6)
        pdf.cell(STICKER_W, 3, barcode, align="C")

        pdf.set_draw_color(200, 200, 200)
        pdf.rect(x, y, STICKER_W, STICKER_H)

    pdf_path = os.path.join(tempfile.gettempdir(), "eDrogery_stickers.pdf")
    pdf.output(pdf_path)
    _open_file(pdf_path)


def _open_file(path: str):
    import sys
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass
