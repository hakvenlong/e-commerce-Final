🛒 Flask E-Commerce Project – Professional Overview
A fully functional, production-ready e-commerce web application built with Flask (Python). Designed with clean architecture, modern UI, session-based cart management, and integrated Cambodian payment gateways (KHQR & Payway).
Ideal for small-to-medium online stores, MVPs, or as a robust starting template for custom e-commerce solutions.

⚠️ Important Deployment Note for Payway / KHQR
ABA Payway mobile app cannot scan KHQR codes when the site is hosted on overseas cloud servers (Vercel, Render, Railway, Fly.io, AWS outside Southeast Asia, etc.).
This is a known restriction imposed by ABA Bank:
The Payway app performs a geo-check and blocks QR scanning if the image is served from a non-Cambodian IP address.
Recommended Solutions (choose one)

Option,Description,Recommended For
1. Host on a Cambodian or SEA-based server,"Use providers with Cambodia/Singapore IPs: Khmer24 Hosting, Ezecom, SmartHost, VPS Server KH, or Cloudflare + Singapore edge",Production (strongly recommended)
2. Use Dynamic QR via ABA Payway API,Replace static KHQR with official Payway checkout API (returns a Cambodian-hosted QR),Best long-term solution (requires Payway merchant account & API integration)
3. Fallback to manual payment instructions,Show QR image + bank details and let customers open their banking app manually,Quick fix for overseas deployment
4. Proxy QR through a Cambodian endpoint,Route /qr_codes/* through a small Cambodian VPS or Cloudflare Worker,Temporary workaround

Bottom line: For live stores accepting real payments via ABA Payway, do not deploy the current KHQR flow on Vercel or any overseas platform if you rely on customers scanning the QR directly from the thank-you page.
The rest of the application (cart, checkout form, design, etc.) works perfectly worldwide.

📁 Project Structure
```
project-root/
├── /static
│   ├── /css          → Bootstrap 5 + custom styles
│   ├── /fonts        → Custom typography assets
│   ├── /images       → Product images, logos, banners
│   └── /js           → Cart interactions, form validation, AJAX utilities
│
├── /templates
│   ├── /includes
│   │   ├── head.html     → Meta tags, CSS/JS includes
│   │   ├── navbar.html   → Responsive navigation bar
│   │   └── footer.html   → Site footer with links & copyright
│   │
│   ├── 500.html          → Custom internal server error page
│   ├── cart.html         → Shopping cart with quantity controls
│   ├── checkout.html     → Customer details & order summary
│   ├── contact.html      → Contact/inquiry page
│   ├── customer_thanks.html → Order confirmation / thank-you page
│   ├── error.html        → Generic error fallback
│   ├── index.html        → Homepage with featured products
│   ├── payment.html      → KHQR/Payway payment instructions
│   ├── product_detail.html → Dynamic single product view
│   └── shop.html         → Product catalog with filtering & pagination ready
│
├── /invoices             → Generated PDF receipts (on successful orders)
├── /qr_codes             → Dynamically generated KHQR images
│   └── qr.png            → Example/placeholder QR
│
├── app.py                → Core Flask application (routes, logic, config)
├── requirements.txt      → All Python dependencies
├── vercel.json           → Vercel serverless deployment configuration
├── .env                  → Environment variables (secret keys, payment configs)
└── README.md             → You are here
```
🚀 Key Features
🛍️ Shopping Experience

Responsive product catalog (/shop)
Detailed product pages with images, pricing, and descriptions
Clean, reusable Jinja2 template partials

🛒 Session-Based Cart System

Add / remove products
Update quantities in real-time
Persistent cart during user session
Client-side validation & smooth UX via JavaScript

💳 Secure Checkout Process

Multi-step checkout flow
Customer information collection (name, phone, address, notes)
Order summary with total calculation
Integrated KHQR Payway payment support
Automatic QR code display for mobile banking payments
Success redirection to thank-you page

🛡️ Error Handling & User Experience

Custom styled 500 & generic error pages
Graceful fallbacks instead of default Flask errors
Flash messages for user feedback

📦 Deployment Ready

Fully compatible with Vercel (serverless Python)
requirements.txt for reproducible environments
Secure handling of secrets via .env
Zero-downtime deployment configuration

🛠 Tech Stack

Backend: Flask (Python 3.9+)
Frontend: Bootstrap 5, JS, Jinja2 templating
Payments: KHQR (QR code generation), ABA Payway ready
Deployment: Vercel (or any WSGI-compatible host)
Storage: Session-based (can be extended to database)


▶️ Local Development Setup
# 1. Clone the repository
```git clone https://github.com/hakvenlong/e-commerce-Final.git```
```cd flask-ecommerce```

# 2. Create and activate virtual environment
```python -m venv venv```
```source venv/bin/activate  ```        # Linux/macOS
```venv\Scripts\activate```         # Windows


# 3. Install dependencies
```pip install -r requirements.txt```
# 4. Set up environment variables (copy .env.example → .env and configure)

# 5. Run the application
```python app.py```

Server will be available at:
http://127.0.0.1:5000

🌐 Deploying to Vercel
The included vercel.json is pre-configured:

```
{
  "version": 2,
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ]
}
```

Ready to launch your online store in Cambodia or beyond — fast, clean, and professional.
Feel free to fork, customize, and scale!
Contributions and improvements are welcome. ⭐
