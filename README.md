# KHQR E-Commerce Flask – Production-Ready Template

A beautiful, fast, and fully functional e-commerce web application built with **Flask (Python)**, specially optimized for the Cambodian market with native**t**ive **KHQR** payment support.

Perfect for small-to-medium online stores, or as a solid foundation for custom e-commerce projects.

Live Demo: [https://flask-ecommerce-kh.vercel.app  ](https://e-commerce-final-kappa.vercel.app/)
(Deployed on Vercel – uses Payway API mode so KHQR is 100% scannable)

## Features

- Responsive product catalog & detailed product pages  
- Session-based shopping cart (add, remove, update quantity)  
- Clean multi-step checkout with order summary  
- Automatic KHQR generation + ABA Payway integration  
- PDF invoice generation on successful orders  
- Mobile-first, Bootstrap 5 design  
- Flash messages & custom error pages (500, 404)  
- Ready for Vercel, Render, Railway, or any WSGI server  

## Important: KHQR on Overseas Servers (Vercel, Render, etc.)

ABA Payway mobile app **blocks QR scanning** when the QR image is served from a non-Cambodian IP (this restriction still exists in 2025).

This repo now ships with **two payment modes** that solve the problem completely:

| Mode | Description | Works on Vercel? | Recommended |
|------|-------------|------------------|-------------|
| 1. Payway Checkout API (Dynamic QR) | Uses official ABA Payway API → QR is hosted in Cambodia | Yes | Strongly recommended |
| 2. Static KHQR (fallback) | Generates QR locally (beautiful, but blocked on overseas hosts) | Only on KH/SEA servers | Only for local hosting |

**Default mode on Vercel = Payway API** → customers can always scan.

## Quick Start (Local)

```bash
git clone https://github.com/hakvenlong/e-commerce-Final.git
cd e-commerce-Final

python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env        # then edit with your keys
python app.py
Open http://127.0.0.1:5000
Deploy to Vercel in 1 Click
Deploy with Vercel
After deploying:

Go to Project Settings → Environment Variables
Add these keys (get them from your ABA Payway merchant dashboard):

textPAYWAY_MERCHANT_ID = your_merchant_id
PAYWAY_API_KEY     = your_api_key
SECRET_KEY         = any_random_string
That’s it – KHQR will work worldwide.
(If you don’t have a Payway merchant account yet, the site gracefully falls back to manual bank details.)
Project Structure
text├── static/          → CSS, JS, images
├── templates/       → Jinja2 templates + includes
├── invoices/        → Generated PDF receipts
├── qr_codes/        → Only used in static KHQR mode
├── app.py           → Main Flask app
├── requirements.txt
├── vercel.json      → Zero-config Vercel setup
└── .env.example
Tech Stack

Backend: Flask (Python 3.9+)
Frontend: Bootstrap 5 + Vanilla JS
Payments: ABA Payway Checkout API (dynamic QR) + static KHQR fallback
Deployment: Vercel, Render, Railway, or any WSGI host

Want to Use Your Own Design or Add a Database?
This project is intentionally lightweight and easy to extend:

Replace session cart → SQLite/PostgreSQL + Flask-SQLAlchemy in < 100 lines
Swap Bootstrap → Tailwind / Alpine.js / React (frontend only)
Add admin panel, user accounts, shipping options, etc.

License
MIT – feel free to fork, modify, and use commercially.
Support the Project
If this template saved you time, give it a star. It helps a lot!
Contributions (bug fixes, Khmer/English translations, new features) are very welcome.
Made with love in Cambodia.
textThis version is shorter, more professional, highlights the fix for Vercel users right at the top, and has a big shiny "Deploy with Vercel" button – people love that.

Copy-paste this directly into your README.md and you’re good to go!
