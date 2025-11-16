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
📁 Project Structure
```
textproject-root/
├── /static
│ ├── /css → Bootstrap 5 + custom styles
│ ├── /fonts → Custom typography assets
│ ├── /images → Product images, logos, banners
│ └── /js → Cart interactions, form validation, AJAX utilities
│
├── /templates
│ ├── /includes
│ │ ├── head.html → Meta tags, CSS/JS includes
│ │ ├── navbar.html → Responsive navigation bar
│ │ └── footer.html → Site footer with links & copyright
│ │
│ ├── 500.html → Custom internal server error page
│ ├── cart.html → Shopping cart with quantity controls
│ ├── checkout.html → Customer details & order summary
│ ├── contact.html → Contact/inquiry page
│ ├── customer_thanks.html → Order confirmation / thank-you page
│ ├── error.html → Generic error fallback
│ ├── index.html → Homepage with featured products
│ ├── payment.html → KHQR/Payway payment instructions
│ ├── product_detail.html → Dynamic single product view
│ └── shop.html → Product catalog with filtering & pagination ready
│
├── /invoices → Generated PDF receipts (on successful orders)
├── /qr_codes → Dynamically generated KHQR images
│ └── qr.png → Example/placeholder QR
│
├── app.py → Core Flask application (routes, logic, config)
├── requirements.txt → All Python dependencies
├── vercel.json → Vercel serverless deployment configuration
├── .env → Environment variables (secret keys, payment configs)
└── README.md → You are here
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
Payments: KHQR (QR code generation)
Deployment: Vercel (or any WSGI-compatible host)

▶️ Local Development Setup
# 1. Clone the repository
git```cd flask-ecommerce```
# 2. Create and activate virtual environment
```python -m venv venv```
```source venv/bin/activate ``` # Linux/macOS
```venv\Scripts\activate``` # Windows
# 3. Install dependencies
```pip install -r requirements.txt```
# 4. Set up environment variables (copy .env.example → .env and configure)
# 5. Run the application
```python app.py```
Server will be available at:
http://127.0.0.1:5000

🌐 Deploying to Vercel
The included vercel.json is pre-configured:
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
textReady to launch your online store in Cambodia or beyond — fast, clean, and professional.
Feel free to fork, customize, and scale!
Contributions and improvements are welcome. ⭐
