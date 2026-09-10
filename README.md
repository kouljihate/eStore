# eDrogery

A cross-platform inventory and cash management application for small shop owners, built with Python and [Flet](https://flet.dev).

## Features

- **Dashboard** — Real-time KPIs: stock value, cash balance, potential profit, product count, low stock alerts, credit outstanding
- **Stock Management** — Add/edit/delete products, stock in/out movements with full history, search & filter
- **Cash Management** — Track income & expenses, view balance and transaction history
- **Credit System** — Create credit notes for customers, track payments, manage outstanding balances
- **Barcode Support** — Generate unique barcodes for products, print sticker labels (PDF)
- **Supplier Tracking** — Store supplier name, WhatsApp, and email per product
- **Multi-language** — Arabic, French, English
- **Dark & Light Themes** — Toggle between dark and light mode
- **Multi-currency** — MAD, EUR, USD, GBP
- **Local Database** — SQLite, no internet required

## Screenshots

*(Add screenshots here)*

## Requirements

- Python 3.8+

## Installation & Usage

```bash
# Clone the repository
git clone https://github.com/kouljihate/eDrogery.git
cd eDrogery

# Run (auto-installs dependencies)
python run.py
```

Or manually:

```bash
pip install -r requirements.txt
python main.py
```

## Project Structure

```
eDrogery/
├── app/
│   ├── screens/          # UI screens (login, dashboard, stock, cash, credit, settings)
│   ├── database.py       # SQLite database operations & migrations
│   ├── theme.py          # App theme and colors
│   ├── translations.py   # Multi-language translations (AR/FR/EN)
│   ├── version.py        # Version info
│   ├── barcode.py        # Barcode generation
│   ├── currency.py       # Currency symbol mapping
│   └── printing.py       # PDF sticker printing
├── assets/
│   ├── fonts/            # Custom fonts
│   └── icon.png          # App icon
├── data/                 # SQLite database directory
├── main.py               # Application entry point
├── run.py                # Launcher script
└── requirements.txt      # Python dependencies
```

## Versioning

Current version: **1.5.0**

## License

MIT
