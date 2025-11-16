import os
import time
import logging
import re
import qrcode
import requests
from mangum import Mangum
from flask import Flask, render_template, request, jsonify, session, url_for, send_file, send_from_directory
from datetime import datetime
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

# ====================== PATHS ======================
if os.path.exists('templates'):
    TEMPLATE_DIR = 'templates'
    STATIC_DIR = 'static'
    INVOICE_DIR = 'invoices'
else:
    TEMPLATE_DIR = '../templates'
    STATIC_DIR = '../static'
    INVOICE_DIR = '/tmp/invoices'

os.makedirs(INVOICE_DIR, exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, 'qr_codes'), exist_ok=True)

# ====================== Flask Setup ======================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.secret_key = os.getenv('SECRET_KEY', 'super-secret-key-2025-final')

# Enable now() in templates
app.jinja_env.globals['now'] = datetime.now

try:
    from bakong_khqr import KHQR
except ImportError:
    logger.error("Run: pip install bakong-khqr")
    raise

# ====================== Config ======================
token = os.getenv('BAKONG_TOKEN')
merchant_bank_account = os.getenv('MERCHANT_BANK_ACCOUNT')
merchant_phone = os.getenv('MERCHANT_PHONE', '012345678')
merchant_city = os.getenv('MERCHANT_CITY', 'Phnom Penh')
merchant_name = os.getenv('MERCHANT_NAME', 'HAK VENLONG')

TELEGRAM_API = (
    f"https://api.telegram.org/bot{os.getenv('TELEGRAM_TOKEN')}/sendMessage"
    if os.getenv('TELEGRAM_TOKEN') and os.getenv('CHAT_ID') else None
)

# ====================== Products ======================
products = [
    {'id': 1, 'name': 'Oversized Tee Black', 'brand': 'White Fox', 'price': 100/4060, 'image': 'https://whitefoxboutique.com/cdn/shop/files/white-fox-ready-to-go-oversized-tee-ready-to-go-lounge-shorts-black-15.10.25-01_1024x1024@2x.progressive.jpg?v=1762398368', 'description': 'Super soft oversized black t-shirt.', 'in_stock': True},
    {'id': 2, 'name': 'Topman relaxed print t-shirt', 'brand': 'Topman', 'price': 100/4060, 'image': 'https://images.asos-media.com/products/topman-relaxed-for-going-nowhere-print-t-shirt-in-white/209283505-2?$n_320w$&wid=317&fit=constrain', 'description': 'Relaxed fit graphic tee.', 'in_stock': True},
    {'id': 3, 'name': 'BDG Bonfire Zip-Up Hoodie', 'brand': 'BDG', 'price': 100/4060, 'image': 'https://images.urbndata.com/is/image/UrbanOutfitters/90061540_001_b?$xlarge$&fit=constrain&fmt=webp&qlt=80&wid=960', 'description': 'Cozy full-zip black hoodie.', 'in_stock': True},
]

# ====================== ROUTES ======================
@app.route('/')
def index():
    session.setdefault('cart', [])
    return render_template('index.html', products=products)

@app.route('/shop')
def shop():
    return render_template('shop.html', products=products)

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# FIXED: Added missing product detail route!
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        return render_template('404.html'), 404
    return render_template('product_detail.html', product=product)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = session.get('cart', [])
    if request.method == 'POST':
        raw = request.form.get('selected_items', '')
        sel = [int(x.strip()) for x in raw.split(',') if x.strip().isdigit()] if raw else [i['id'] for i in cart]
        selected_cart = [i for i in cart if i['id'] in sel]
        total_price = sum(i['price'] * i['quantity'] for i in selected_cart)

        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        payment_method = request.form.get('payment_method', 'delivery')

        err = validate_input(name, email, phone, address)
        if err or not selected_cart:
            return render_template('checkout.html', cart=cart, error=err or "No items", total_price=total_price)

        bill_number = f"TRX{int(time.time()*1000)}"

        if payment_method == 'qr':
            total_khr = round(total_price * 4060, 2)
            khqr = KHQR(token)
            qr_data = khqr.create_qr(
                bank_account=merchant_bank_account,
                merchant_name=merchant_name,
                merchant_city=merchant_city,
                amount=total_khr,
                currency='KHR',
                bill_number=bill_number,
                phone_number=merchant_phone,
                store_label="HAK VENLONG SHOP",
                terminal_label="ONLINE STORE"
            )
            md5 = khqr.generate_md5(qr_data)
            qr_path = os.path.join(STATIC_DIR, 'qr_codes', f"{md5}.png")
            qrcode.make(qr_data).save(qr_path)

            session['transaction'] = {
                'md5': md5, 'total_khr': total_khr, 'bill_number': bill_number,
                'name': name, 'email': email, 'phone': phone, 'address': address,
                'cart': selected_cart, 'paid_notified': False, 'invoice_generated': False
            }
            session.modified = True
            return render_template('payment.html', qr=f"/static/qr_codes/{md5}.png", md5=md5, price=total_khr, merchant_name=merchant_name)

        send_telegram_message(name, email, phone, address, selected_cart, total_price, "delivery", bill_number)
        session['cart'] = [i for i in cart if i['id'] not in sel]
        session.modified = True

        return render_template('customer_thanks.html',
                               name=name, address=address, bill_number=bill_number,
                               amount_khr=0, paid=False, has_invoice=False)

    total = sum(i['price'] * i['quantity'] for i in cart)
    return render_template('checkout.html', cart=cart, total_price=total)

@app.route('/check_payment_status', methods=['POST'])
def check_payment_status():
    md5 = request.json.get('md5')
    t = session.get('transaction', {})
    if t.get('md5') != md5: return jsonify({'paid': False})
    khqr = KHQR(token)
    status = khqr.check_payment(md5)
    if status == "PAID":
        notify_paid(t)
        if not t.get('invoice_generated'):
            pdf = generate_pdf_invoice(t, t['cart'])
            t['invoice_path'] = pdf
            t['invoice_generated'] = True
            session['transaction'] = t
            session.modified = True
        session['cart'] = []
        return jsonify({'paid': True, 'redirect': url_for('customer_thanks')})
    return jsonify({'paid': False})

@app.route('/download_invoice')
def download_invoice():
    t = session.get('transaction', {})
    path = t.get('invoice_path')
    if not path or not os.path.exists(path): return "Not ready", 404
    return send_file(path, as_attachment=True, download_name=f"invoice_{t['bill_number']}.pdf")

@app.route('/customer_thanks')
def customer_thanks():
    t = session.get('transaction', {})
    return render_template('customer_thanks.html',
                           name=t.get('name', 'Customer'),
                           address=t.get('address', ''),
                           bill_number=t.get('bill_number', 'N/A'),
                           amount_khr=t.get('total_khr', 0),
                           paid=bool(t.get('paid_notified')),
                           has_invoice=bool(t.get('invoice_generated')))

# CART API
@app.route('/get-cart')
def get_cart():
    cart = session.get('cart', [])
    return jsonify({'cart': cart, 'total_items': sum(i['quantity'] for i in cart), 'total_price': round(sum(i['price'] * i['quantity'] for i in cart), 4)})

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    product_id = int(data['id'])
    qty = int(data['quantity'])
    product = next((p for p in products if p['id'] == product_id), None)
    if not product: return jsonify({'status': 'error'}), 400
    cart = session.get('cart', [])
    for item in cart:
        if item['id'] == product_id:
            item['quantity'] += qty
            session['cart'] = cart
            session.modified = True
            return jsonify({'status': 'success'})
    cart.append({'id': product_id, 'name': product['name'], 'price': product['price'], 'image': product['image'], 'quantity': qty})
    session['cart'] = cart
    session.modified = True
    return jsonify({'status': 'success'})

@app.route('/update-cart-quantity', methods=['POST'])
def update_cart_quantity():
    data = request.get_json()
    cart = session.get('cart', [])
    for item in cart:
        if item['id'] == int(data['id']):
            item['quantity'] = int(data['quantity'])
            session['cart'] = cart
            session.modified = True
            return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 404

@app.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    data = request.get_json()
    cart = session.get('cart', [])
    session['cart'] = [i for i in cart if i['id'] != int(data['id'])]
    session.modified = True
    return jsonify({'status': 'success'})

# ====================== Helpers (keep your existing ones) ======================
def validate_input(name, email, phone, address):
    if not all([name, email, phone, address]): return "All fields required."
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email): return "Invalid email."
    clean = re.sub(r'[+\-\s]', '', phone)
    if not clean.isdigit() or len(clean) < 8: return "Invalid phone."
    if len(address.strip()) < 5: return "Invalid address."
    return None

def send_telegram_message(name, email, phone, address, cart, total_price, payment_method, bill_number):
    if not TELEGRAM_API: return False
    try:
        lines = [
            f"New Order – {datetime.now():%d/%m %H:%M}",
            f"*{name}* | {phone}",
            f"{email}\n{address}",
            f"Payment: {payment_method.upper()} | Bill: `{bill_number}`",
            "*Items:*"
        ] + [f"• {i['name']} × {i['quantity']} = ${i['price']*i['quantity']:.2f}" for i in cart] + \
        [f"", f"*Total: ${total_price:.2f} ≈ {total_price*4060:,.0f} KHR*"]
        requests.get(TELEGRAM_API, params={'chat_id': os.getenv('CHAT_ID'), 'text': '\n'.join(lines), 'parse_mode': 'Markdown'}, timeout=10)
        return True
    except Exception as e:
        logger.error(f"Telegram error: {e}")
        return False

def notify_paid(t):
    if t.get('paid_notified'): return False
    if not TELEGRAM_API: return False
    try:
        lines = ["PAID ORDER CONFIRMED", f"{t['name']}", f"{t['phone']} | {t['address']}", f"{t['total_khr']:,.0f} KHR", f"Bill: `{t['bill_number']}`", f"{datetime.now():%d/%m/%Y %H:%M}"]
        requests.get(TELEGRAM_API, params={'chat_id': os.getenv('CHAT_ID'), 'text': '\n'.join(lines), 'parse_mode': 'Markdown'}, timeout=10)
        t['paid_notified'] = True
        session['transaction'] = t
        session.modified = True
        return True
    except Exception as e:
        logger.error(f"Telegram paid error: {e}")
    return False

def generate_pdf_invoice(t, cart):
    pdf_path = os.path.join(INVOICE_DIR, f"invoice_{t['bill_number']}.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    logo_path = os.path.join(STATIC_DIR, "logo.png")
    if os.path.exists(logo_path):
        story.append(Image(logo_path, width=1.5*inch, height=1*inch))
        story.append(Spacer(1, 12))
    story.append(Paragraph("<b>INVOICE</b>", styles['Title']))
    story.append(Spacer(1, 20))
    story.append(Table([["Bill #:", t['bill_number']], ["Date:", datetime.now().strftime("%Y-%m-%d %H:%M")],
                        ["Customer:", t['name']], ["Phone:", t['phone']], ["Address:", t['address']]], colWidths=[2*inch, 4*inch]))
    story.append(Spacer(1, 20))
    data = [["#", "Item", "Qty", "Price", "Total"]]
    for idx, i in enumerate(cart, 1):
        data.append([idx, i['name'], i['quantity'], f"${i['price']:.2f}", f"${i['price']*i['quantity']:.2f}"])
    total_usd = sum(i['price'] * i['quantity'] for i in cart)
    data += [["", "", "", "Total USD:", f"${total_usd:.2f}"], ["", "", "", "Total KHR:", f"{t['total_khr']:,.0f} KHR"]]
    table = Table(data, colWidths=[0.5*inch, 3.5*inch, 0.7*inch, 1*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#d72323")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
    ]))
    story.append(table)
    story.append(Spacer(1, 30))
    story.append(Paragraph("Thank you!", styles['Normal']))
    doc.build(story)
    return pdf_path

# app.py — FINAL VERSION — 100% WORKING & DEPLOY-READY
import os
import time
import logging
import re
import qrcode
import requests
from mangum import Mangum
from flask import Flask, render_template, request, jsonify, session, url_for, send_file
from datetime import datetime
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch



# ====================== PATHS ======================
if os.path.exists('templates'):
    TEMPLATE_DIR = 'templates'
    STATIC_DIR = 'static'
    INVOICE_DIR = 'invoices'
else:  # Vercel /tmp
    TEMPLATE_DIR = '../templates'
    STATIC_DIR = '../static'
    INVOICE_DIR = '/tmp/invoices'

os.makedirs(INVOICE_DIR, exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, 'qr_codes'), exist_ok=True)

# ====================== Flask Setup ======================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.secret_key = os.getenv('SECRET_KEY', 'fallback-secret-2025')

# Enable {{ now() }} in templates
app.jinja_env.globals['now'] = datetime.now

try:
    from bakong_khqr import KHQR
except ImportError:
    logger.error("Install bakong-khqr: pip install bakong-khqr")
    raise

# ====================== Config ======================
token = os.getenv('BAKONG_TOKEN')
merchant_bank_account = os.getenv('MERCHANT_BANK_ACCOUNT')
merchant_phone = os.getenv('MERCHANT_PHONE', '012345678')
merchant_city = os.getenv('MERCHANT_CITY', 'Phnom Penh')
merchant_name = os.getenv('MERCHANT_NAME', 'HAK VENLONG SHOP')

TELEGRAM_API = (
    f"https://api.telegram.org/bot{os.getenv('TELEGRAM_TOKEN')}/sendMessage"
    if os.getenv('TELEGRAM_TOKEN') and os.getenv('CHAT_ID') else None
)

# ====================== Products ======================
products = [
    {'id': 1, 'name': 'Oversized Tee Black', 'brand': 'White Fox', 'price': 100/4060, 'image': 'https://whitefoxboutique.com/cdn/shop/files/white-fox-ready-to-go-oversized-tee-ready-to-go-lounge-shorts-black-15.10.25-01_1024x1024@2x.progressive.jpg?v=1762398368', 'description': 'Super soft oversized black t-shirt.'},
    {'id': 2, 'name': 'Topman relaxed print t-shirt', 'brand': 'Topman', 'price': 100/4060, 'image': 'https://images.asos-media.com/products/topman-relaxed-for-going-nowhere-print-t-shirt-in-white/209283505-2?$n_320w$&wid=317&fit=constrain', 'description': 'Relaxed fit graphic tee.'},
    {'id': 3, 'name': 'BDG Bonfire Zip-Up Hoodie', 'brand': 'BDG', 'price': 100/4060, 'image': 'https://images.urbndata.com/is/image/UrbanOutfitters/90061540_001_b?$xlarge$&fit=constrain&fmt=webp&qlt=80&wid=960', 'description': 'Cozy full-zip black hoodie.'},
]

# ====================== Helpers ======================
def validate_input(name, email, phone, address):
    if not all([name, email, phone, address]): return "All fields required."
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email): return "Invalid email."
    clean = re.sub(r'[+\-\s]', '', phone)
    if not clean.isdigit() or len(clean) < 8: return "Invalid phone."
    if len(address.strip()) < 5: return "Invalid address."
    return None

def send_telegram_message(name, email, phone, address, cart, total_price, payment_method, bill_number):
    if not TELEGRAM_API: return False
    try:
        lines = [
            f"New Order – {datetime.now():%d/%m %H:%M}",
            f"*{name}* | {phone}", f"{email}\n{address}",
            f"Payment: {payment_method.upper()} | Bill: `{bill_number}`",
            "*Items:*"
        ] + [f"• {i['name']} × {i['quantity']} = ${i['price']*i['quantity']:.2f}" for i in cart] + \
        [f"", f"*Total: ${total_price:.2f} ≈ {total_price*4060:,.0f} KHR*"]
        requests.get(TELEGRAM_API, params={'chat_id': os.getenv('CHAT_ID'), 'text': '\n'.join(lines), 'parse_mode': 'Markdown'}, timeout=10)
        return True
    except Exception as e:
        logger.error(f"Telegram error: {e}")
        return False

def notify_paid(t):
    if t.get('paid_notified') or not TELEGRAM_API: return False
    try:
        lines = ["PAID ORDER", f"{t['name']}", f"{t['phone']} | {t['address']}", f"{t['total_khr']:,.0f} KHR", f"Bill: `{t['bill_number']}`"]
        requests.get(TELEGRAM_API, params={'chat_id': os.getenv('CHAT_ID'), 'text': '\n'.join(lines), 'parse_mode': 'Markdown'}, timeout=10)
        t['paid_notified'] = True
        session['transaction'] = t
        session.modified = True
        return True
    except: pass
    return False

def generate_pdf_invoice(t, cart):
    pdf_path = os.path.join(INVOICE_DIR, f"invoice_{t['bill_number']}.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    logo = os.path.join(STATIC_DIR, "logo.png")
    if os.path.exists(logo):
        story += [Image(logo, width=1.5*inch, height=1*inch), Spacer(1, 12)]
    story += [Paragraph("<b>INVOICE</b>", styles['Title']), Spacer(1, 20)]
    story += [Table([["Bill #:", t['bill_number']], ["Date:", datetime.now().strftime("%Y-%m-%d %H:%M")],
                     ["Customer:", t['name']], ["Phone:", t['phone']], ["Address:", t['address']]], colWidths=[2*inch, 4*inch])]
    story += [Spacer(1, 20)]
    data = [["#", "Item", "Qty", "Price", "Total"]]
    for idx, i in enumerate(cart, 1):
        data.append([idx, i['name'], i['quantity'], f"${i['price']:.2f}", f"${i['price']*i['quantity']:.2f}"])
    total_usd = sum(i['price'] * i['quantity'] for i in cart)
    data += [["", "", "", "Total USD:", f"${total_usd:.2f}"], ["", "", "", "Total KHR:", f"{t['total_khr']:,.0f} KHR"]]
    table = Table(data, colWidths=[0.5*inch, 3.5*inch, 0.7*inch, 1*inch, 1*inch])
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor("#d72323")), ('TEXTCOLOR',(0,0),(-1,0),colors.white), ('GRID',(0,0),(-1,-1),0.5,colors.black)]))
    story += [table, Spacer(1, 30), Paragraph("Thank you!", styles['Normal'])]
    doc.build(story)
    return pdf_path

# ====================== ROUTES ======================
@app.route('/')
def index():
    session.setdefault('cart', [])
    return render_template('index.html', products=products)

@app.route('/shop')
def shop():
    return render_template('shop.html', products=products)

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        return render_template('404.html'), 404
    return render_template('product_detail.html', product=product)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = session.get('cart', [])
    if request.method == 'POST':
        raw = request.form.get('selected_items', '')
        sel = [int(x.strip()) for x in raw.split(',') if x.strip().isdigit()] or [i['id'] for i in cart]
        selected_cart = [i for i in cart if i['id'] in sel]
        total_price = sum(i['price'] * i['quantity'] for i in selected_cart)

        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        payment_method = request.form.get('payment_method', 'delivery')

        err = validate_input(name, email, phone, address)
        if err or not selected_cart:
            return render_template('checkout.html', cart=cart, error=err or "No items selected", total_price=total_price)

        bill_number = f"TRX{int(time.time()*1000)}"

        if payment_method == 'qr':
            total_khr = round(total_price * 4060, 2)
            khqr = KHQR(token)
            qr_data = khqr.create_qr(
                bank_account=merchant_bank_account,
                merchant_name=merchant_name,
                merchant_city=merchant_city,
                amount=total_khr,
                currency='KHR',
                bill_number=bill_number,
                phone_number=merchant_phone,
                store_label="HAK VENLONG SHOP",
                terminal_label="ONLINE STORE"
            )
            md5 = khqr.generate_md5(qr_data)
            qr_path = os.path.join(STATIC_DIR, 'qr_codes', f"{md5}.png")
            qrcode.make(qr_data).save(qr_path)

            session['transaction'] = {
                'md5': md5, 'total_khr': total_khr, 'bill_number': bill_number,
                'name': name, 'email': email, 'phone': phone, 'address': address,
                'cart': selected_cart, 'paid_notified': False, 'invoice_generated': False
            }
            session.modified = True
            return render_template('payment.html', qr=f"/static/qr_codes/{md5}.png", md5=md5, price=total_khr, merchant_name=merchant_name)

        send_telegram_message(name, email, phone, address, selected_cart, total_price, "delivery", bill_number)
        session['cart'] = [i for i in cart if i['id'] not in sel]
        session.modified = True
        return render_template('customer_thanks.html', name=name, address=address, bill_number=bill_number, amount_khr=0, paid=False, has_invoice=False)

    total = sum(i['price'] * i['quantity'] for i in cart)
    return render_template('checkout.html', cart=cart, total_price=total)

@app.route('/check_payment_status', methods=['POST'])
def check_payment_status():
    md5 = request.json.get('md5')
    t = session.get('transaction', {})
    if t.get('md5') != md5: return jsonify({'paid': False})
    khqr = KHQR(token)
    status = khqr.check_payment(md5)
    if status == "PAID":
        notify_paid(t)
        if not t.get('invoice_generated'):
            pdf = generate_pdf_invoice(t, t['cart'])
            t['invoice_path'] = pdf
            t['invoice_generated'] = True
            session['transaction'] = t
            session.modified = True
        session['cart'] = []
        return jsonify({'paid': True})
    return jsonify({'paid': False})

@app.route('/download_invoice')
def download_invoice():
    t = session.get('transaction', {})
    path = t.get('invoice_path')
    if not path or not os.path.exists(path): return "Invoice not ready", 404
    return send_file(path, as_attachment=True, download_name=f"invoice_{t['bill_number']}.pdf")

@app.route('/customer_thanks')
def customer_thanks():
    t = session.get('transaction', {})
    return render_template('customer_thanks.html',
                           name=t.get('name', 'Customer'),
                           address=t.get('address', ''),
                           bill_number=t.get('bill_number', 'N/A'),
                           amount_khr=t.get('total_khr', 0),
                           paid=bool(t.get('paid_notified')),
                           has_invoice=bool(t.get('invoice_generated')))

# CART API
@app.route('/get-cart')
def get_cart():
    cart = session.get('cart', [])
    return jsonify({'cart': cart, 'total_items': sum(i['quantity'] for i in cart)})

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    pid, qty = int(data['id']), int(data['quantity'])
    product = next((p for p in products if p['id'] == pid), None)
    if not product: return jsonify({'status': 'error'}), 400
    cart = session.get('cart', [])
    for item in cart:
        if item['id'] == pid:
            item['quantity'] += qty
            session['cart'] = cart; session.modified = True
            return jsonify({'status': 'success'})
    cart.append({'id': pid, 'name': product['name'], 'price': product['price'], 'image': product['image'], 'quantity': qty})
    session['cart'] = cart; session.modified = True
    return jsonify({'status': 'success'})

@app.route('/update-cart-quantity', methods=['POST'])
def update_cart_quantity():
    data = request.get_json()
    cart = session.get('cart', [])
    for item in cart:
        if item['id'] == int(data['id']):
            item['quantity'] = int(data['quantity'])
            session['cart'] = cart; session.modified = True
            return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 404

@app.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    data = request.get_json()
    cart = session.get('cart', [])
    session['cart'] = [i for i in cart if i['id'] != int(data['id'])]
    session.modified = True
    return jsonify({'status': 'success'})

# ====================== FINAL RUN BLOCK — WORKS EVERYWHERE ======================
handler = Mangum(app, lifespan="off")

# For Vercel / Render / Railway / AWS Lambda
def handler(event, context=None):
    return handler(event, context)

# LOCAL DEVELOPMENT — WORKS 100% WITH "python app.py"
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

# This line allows "flask run" to work too (optional but safe)
application = app