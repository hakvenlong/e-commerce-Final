import os
import time
import logging
import re
import qrcode
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, url_for, send_file
from datetime import datetime
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# KHQR SDK (Official)
# ----------------------------------------------------------------------
try:
    from bakong_khqr import KHQR
except ImportError as e:
    logger.error("bakong_khqr not installed. Run: pip install bakong-khqr")
    raise e

# ----------------------------------------------------------------------
# Load .env
# ----------------------------------------------------------------------
load_dotenv()
app = Flask(__name__, static_folder='static')
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')
token = os.getenv('BAKONG_TOKEN')
merchant_bank_account = os.getenv('MERCHANT_BANK_ACCOUNT')
merchant_phone = os.getenv('MERCHANT_PHONE')
merchant_city = os.getenv('MERCHANT_CITY', 'Phnom Penh')
merchant_name = os.getenv('MERCHANT_NAME', 'HAK VENLONG')
TELEGRAM_API = (
    f"https://api.telegram.org/bot{os.getenv('TELEGRAM_TOKEN')}/sendMessage"
    if os.getenv('TELEGRAM_TOKEN') and os.getenv('CHAT_ID') else None
)

# ----------------------------------------------------------------------
# Products
# ----------------------------------------------------------------------
products = [
    {'id': 1, 'name': 'Oversized Tee Black', 'brand': 'White Fox', 'price': 100/4060, 'image': 'https://whitefoxboutique.com/cdn/shop/files/white-fox-ready-to-go-oversized-tee-ready-to-go-lounge-shorts-black-15.10.25-01_1024x1024@2x.progressive.jpg?v=1762398368', 'description': 'Super soft oversized black t-shirt with a relaxed fit. Perfect for everyday casual wear or lounging.', 'categories': 'clothing,tshirt,oversized,womens', 'in_stock': True},
    
    {'id': 2, 'name': 'Topman relaxed for Going Nowhere print t-shirt in white', 'brand': 'Topman', 'price': 100/4060, 'image': 'https://images.asos-media.com/products/topman-relaxed-for-going-nowhere-print-t-shirt-in-white/209283505-2?$n_320w$&wid=317&fit=constrain', 'description': 'Relaxed-fit white cotton t-shirt featuring "Going Nowhere" chest print. Classic crew neck and short sleeves.', 'categories': 'clothing,tshirt,graphic,mens', 'in_stock': True},
    
    {'id': 3, 'name': 'BDG Bonfire Solid Zip-Up Hoodie Sweatshirt', 'brand': 'BDG', 'price': 100/4060, 'image': 'https://images.urbndata.com/is/image/UrbanOutfitters/90061540_001_b?$xlarge$&fit=constrain&fmt=webp&qlt=80&wid=960', 'description': 'Cozy black full-zip hoodie with drawstring hood and kangaroo pocket. Made from soft fleece for ultimate comfort.', 'categories': 'clothing,hoodie,zipup,unisex', 'in_stock': True},
    
    {'id': 4, 'name': 'BDG Printed Fleece Quarter Zip Sweatshirt', 'brand': 'BDG', 'price': 100/4060, 'image': 'https://images.urbndata.com/is/image/UrbanOutfitters/101845246_049_c2?$xlarge$&fit=constrain&fmt=webp&qlt=80&wid=960', 'description': 'Quarter-zip fleece pullover with all-over abstract print. Stand collar and relaxed fit for easy layering.', 'categories': 'clothing,sweatshirt,quarterzip,unisex', 'in_stock': True},
    
    {'id': 5, 'name': 'Rhythm High Plains Quarter-Zip Sweatshirt', 'brand': 'Rhythm', 'price': 100/4060, 'image': 'https://images.urbndata.com/is/image/UrbanOutfitters/105379440_016_b?$xlarge$&fit=constrain&fmt=webp&qlt=80&wid=960', 'description': 'Earthy-toned quarter-zip sweatshirt with woven label detail. Heavyweight cotton blend perfect for cooler days.', 'categories': 'clothing,sweatshirt,quarterzip,mens', 'in_stock': True},
    
    {'id': 6, 'name': 'Standard Cloth Jump Shot Hoodie Sweatshirt', 'brand': 'Standard Cloth', 'price': 100/4060, 'image': 'https://images.urbndata.com/is/image/UrbanOutfitters/91856542_062_b?$xlarge$&fit=constrain&fmt=webp&qlt=80&wid=960', 'description': 'Vintage-inspired blue hoodie with "Jump Shot" basketball graphic on front. Soft fleece lining and relaxed fit.', 'categories': 'clothing,hoodie,graphic,mens', 'in_stock': True},
    
    {'id': 7, 'name': 'True Religion Applique Shrunken Flannel Zip-Up Hoodie', 'brand': 'True Religion', 'price': 100/4060, 'image': 'https://images.urbndata.com/is/image/UrbanOutfitters/101409399_018_b?$xlarge$&fit=constrain&fmt=webp&qlt=80&wid=960', 'description': 'Cropped flannel zip-up hoodie with embroidered horseshoe logo. Plaid pattern and raw hem details.', 'categories': 'clothing,hoodie,flannel,womens', 'in_stock': True},
    
    {'id': 8, 'name': 'Nola Oversized Off-The-Shoulder Sweater', 'brand': 'Urban Outfitters', 'price': 100/4060, 'image': 'https://images.urbndata.com/is/image/UrbanOutfitters/100256221_012_b?$xlarge$&fit=constrain&fmt=webp&qlt=80&wid=960', 'description': 'Slouchy off-the-shoulder knit sweater in cream color. Ribbed cuffs and hem for a cozy oversized look.', 'categories': 'clothing,sweater,offshoulder,womens', 'in_stock': True},
    
    {'id': 9, 'name': 'Out From Under Clarity Cozy Knit Off-The-Shoulder', 'brand': 'Out From Under', 'price': 100/4060, 'image': 'https://images.urbndata.com/is/image/UrbanOutfitters/94325602_011_b?$xlarge$&fit=constrain&fmt=webp&qlt=80&wid=960', 'description': 'Ultra-soft off-the-shoulder cropped sweater in light beige. Perfect layering piece with a relaxed fit.', 'categories': 'clothing,sweater,crop,womens', 'in_stock': True},
    
    {'id': 10, 'name': 'BDG Kayla Cocoon Low-Rise Jean               ', 'brand': 'BDG', 'price': 100/4060, 'image': 'https://images.urbndata.com/is/image/UrbanOutfitters/100324151_005_b?$xlarge$&fit=constrain&fmt=webp&qlt=80&wid=960', 'description': 'Relaxed cocoon-fit low-rise jeans in light wash denim. Barrel leg silhouette with slight tapering at ankle.', 'categories': 'clothing,jeans,lowrise,womens', 'in_stock': True},
    
    {'id': 11, 'name': 'ReMADE By UO Painted Levis Slouchy Fit Jean', 'brand': 'ReMADE by UO', 'price': 100/4060, 'image': 'https://images.urbndata.com/is/image/UrbanOutfitters/105092589_009_b?$xlarge$&fit=constrain&fmt=webp&qlt=80&wid=960', 'description': 'One-of-a-kind hand-painted vintage Levi’s jeans. Baggy slouchy fit with unique splatter paint design.', 'categories': 'clothing,jeans,vintage,unisex', 'in_stock': True},
    
    {'id': 12, 'name': 'ReMADE By UO Bleached Flannel Shirt', 'brand': 'ReMADE by UO', 'price': 100/4060, 'image': 'https://images.urbndata.com/is/image/UrbanOutfitters/102377942_000_b?$xlarge$&fit=constrain&fmt=webp&qlt=80&wid=960', 'description': 'Upcycled flannel shirt with custom bleach tie-dye effect. Each piece is unique and perfectly oversized.', 'categories': 'clothing,shirt,flannel,unisex', 'in_stock': True},
    
    {'id': 13, 'name': 'Levi’s® Plaid Wool Shirt Jacket', 'brand': 'Levi’s', 'price': 100/4060, 'image': 'https://images.urbndata.com/is/image/UrbanOutfitters/101033504_037_b?$xlarge$&fit=constrain&fmt=webp&qlt=80&wid=960', 'description': 'Heavyweight wool-blend plaid shacket with button front and dual chest pockets. Ideal outerwear layer.', 'categories': 'clothing,shacket,jacket,unisex', 'in_stock': True}
]

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def validate_input(name, email, phone, address):
    if not all([name, email, phone, address]): return "All fields required."
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email): return "Invalid email."
    clean = phone.replace('+', '').replace(' ', '')
    if not clean.isdigit() or len(clean) < 8: return "Invalid phone."
    if len(address.strip()) < 5: return "Invalid address."
    return None

def send_telegram_message(name, email, phone, address, cart, total_price, payment_method, bill_number):
    if not TELEGRAM_API: return False
    try:
        lines = [
            f"*New Order* at {datetime.now():%Y-%m-%d %H:%M:%S}",
            f"{name}\n{email}\n{phone}\n{address}",
            f"{payment_method.title()}\nBill: {bill_number}",
            "*Items:*"
        ] + [f"• {i['name']} x{i['quantity']} - ${i['price']*i['quantity']:.2f}" for i in cart] + [f"*Total:* ${total_price:.2f}"]
        res = requests.get(TELEGRAM_API, params={'chat_id': os.getenv('CHAT_ID'), 'text': '\n'.join(lines), 'parse_mode': 'Markdown'})
        return res.status_code == 200
    except Exception as e:
        logger.error(f"Telegram error: {e}")
        return False

def notify_paid(transaction):
    if transaction.get('paid_notified', False): return False
    if not TELEGRAM_API: return False
    try:
        lines = [
            f"PAID ORDER CONFIRMED",
            f"{transaction['name']}\n{transaction['email']}\n{transaction['phone']}\n{transaction['address']}",
            f"Bill: {transaction['bill_number']}",
            f"Amount: {transaction['total_khr']:.2f} KHR",
            f"Time: {datetime.now():%Y-%m-%d %H:%M:%S}"
        ]
        res = requests.get(TELEGRAM_API, params={'chat_id': os.getenv('CHAT_ID'), 'text': '\n'.join(lines), 'parse_mode': 'Markdown'})
        if res.status_code == 200:
            transaction['paid_notified'] = True
            session['transaction'] = transaction
            session.modified = True
            logger.info("Telegram: Payment confirmed")
            return True
    except Exception as e:
        logger.error(f"Telegram paid notify error: {e}")
    return False

# ----------------------------------------------------------------------
# PDF Invoice
# ----------------------------------------------------------------------
def generate_pdf_invoice(transaction, cart):
    bill_number = transaction['bill_number']
    pdf_path = f"invoices/invoice_{bill_number}.pdf"
    os.makedirs('invoices', exist_ok=True)

    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    logo_path = "static/logo.png"
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=1.5*inch, height=1*inch)
        story.append(logo)
        story.append(Spacer(1, 12))

    story.append(Paragraph("<b>INVOICE</b>", styles['Title']))
    story.append(Spacer(1, 12))

    info_data = [
        [Paragraph("<b>Bill #:</b>", styles['Normal']), bill_number],
        [Paragraph("<b>Date:</b>", styles['Normal']), datetime.now().strftime("%Y-%m-%d %H:%M")],
        [Paragraph("<b>Customer:</b>", styles['Normal']), transaction['name']],
        [Paragraph("<b>Phone:</b>", styles['Normal']), transaction['phone']],
        [Paragraph("<b>Address:</b>", styles['Normal']), transaction['address']],
    ]
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))

    data = [["#", "Item", "Qty", "Price", "Total"]]
    total_usd = 0
    for idx, item in enumerate(cart, 1):
        price = item['price']
        qty = item['quantity']
        total = price * qty
        total_usd += total
        data.append([idx, item['name'], qty, f"${price:.4f}", f"${total:.4f}"])
    total_khr = transaction['total_khr']
    data.append(["", "", "", "Total (USD):", f"${total_usd:.2f}"])
    data.append(["", "", "", "Total (KHR):", f"{total_khr:.2f} KHR"])

    table = Table(data, colWidths=[0.5*inch, 3.5*inch, 0.7*inch, 1*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#d72323")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (1,1), (1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,-2), (-1,-1), colors.HexColor("#f0f0f0")),
    ]))
    story.append(table)
    story.append(Spacer(1, 20))
    story.append(Paragraph("Thank you for shopping with us!", styles['Normal']))

    doc.build(story)
    logger.info(f"PDF generated: {pdf_path}")
    return pdf_path

# ----------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------
@app.route('/')
def index():
    session.setdefault('cart', [])
    return render_template('index.html', products=products)

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow}

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

@app.route('/shop')
def shop():
    session.setdefault('cart', [])
    return render_template('shop.html', products=products)

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/contact')
def contact():
    session.setdefault('cart', [])
    return render_template('contact.html')

@app.route('/product_detail/<int:product_id>')
def product_detail(product_id):
    product = next((p for p in products if p['id'] == product_id), None)
    return render_template('product_detail.html', product=product) if product else ("Not found", 404)

# ----------------------------------------------------------------------
# Cart API
# ----------------------------------------------------------------------
@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    try:
        data = request.get_json()
        required = ['id', 'name', 'price', 'image', 'quantity']
        if not all(k in data for k in required): return jsonify({'status': 'error', 'message': 'Invalid data'}), 400
        product_id = str(data['id'])
        qty = int(data['quantity'])
        if qty < 1: return jsonify({'status': 'error', 'message': 'Quantity ≥ 1'}), 400
        product = next((p for p in products if p['id'] == int(product_id) and p['in_stock']), None)
        if not product: return jsonify({'status': 'error', 'message': 'Out of stock'}), 404
        cart = session.get('cart', [])
        for item in cart:
            if item['id'] == product_id:
                item['quantity'] += qty
                session['cart'] = cart
                session.modified = True
                return jsonify({'status': 'success'})
        cart.append({'id': product_id, 'name': data['name'], 'price': float(data['price']), 'image': data['image'], 'quantity': qty})
        session['cart'] = cart
        session.modified = True
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Add to cart error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/update-cart-quantity', methods=['POST'])
def update_cart_quantity():
    try:
        data = request.get_json()
        qty = int(data.get('quantity'))
        if qty < 1: return jsonify({'status': 'error', 'message': 'Quantity ≥ 1'}), 400
        cart = session.get('cart', [])
        for item in cart:
            if item['id'] == str(data.get('id')):
                item['quantity'] = qty
                session['cart'] = cart
                session.modified = True
                return jsonify({'status': 'success'})
        return jsonify({'status': 'error', 'message': 'Not in cart'}), 404
    except Exception as e:
        logger.error(f"Update cart error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    try:
        product_id = str(request.get_json().get('id'))
        cart = session.get('cart', [])
        cart = [i for i in cart if i['id'] != product_id]
        session['cart'] = cart
        session.modified = True
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Remove from cart error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get-cart', methods=['GET'])
def get_cart():
    return jsonify({'status': 'success', 'cart': session.get('cart', [])})

# ----------------------------------------------------------------------
# Checkout
# ----------------------------------------------------------------------
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = session.get('cart', [])

    if request.method == 'POST':
        sel = [s for s in request.form.get('selected_items', '').split(',') if s]
        if not sel: sel = [str(i['id']) for i in cart]
        selected_cart = [i for i in cart if i['id'] in sel]
        total_price = sum(i['price'] * i['quantity'] for i in selected_cart)

        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        payment_method = request.form.get('payment_method')

        err = validate_input(name, email, phone, address)
        if err or not selected_cart:
            return render_template('checkout.html', cart=cart, error=err or 'Empty cart', total_price=total_price)
        if payment_method not in ('delivery', 'qr'):
            return render_template('checkout.html', cart=cart, error='Invalid payment method', total_price=total_price)

        bill_number = f"TRX{int(time.time()*1000)}"

        # === QR PAYMENT ===
        if payment_method == 'qr':
            try:
                total_khr = round(total_price * 4060, 2)
                khqr = KHQR(token)
                qr_data = khqr.create_qr(
                    bank_account=merchant_bank_account,
                    merchant_name=merchant_name,
                    merchant_city=merchant_city,
                    amount=total_khr,
                    currency='KHR',
                    store_label='SMOS-Store',
                    phone_number=merchant_phone,
                    bill_number=bill_number,
                    terminal_label='Cashier-01'
                )
                if not qr_data: raise ValueError("Empty QR")

                md5 = khqr.generate_md5(qr_data)
                qr_path = f"qr_codes/{md5}.png"
                full_path = os.path.join('static', qr_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                qrcode.make(qr_data).save(full_path)

                session['transaction'] = {
                    'md5': md5,
                    'total_khr': total_khr,
                    'bill_number': bill_number,
                    'name': name, 'email': email,
                    'phone': phone, 'address': address,
                    'created_at': time.time(),
                    'paid_notified': False,
                    'cart': selected_cart,
                    'invoice_generated': False
                }
                session.modified = True
                logger.info(f"QR generated: {qr_path}")

                return render_template(
                    'payment.html',
                    qr=qr_path,
                    md5=md5,
                    price=total_khr,
                    currency='KHR',
                    merchant_name=merchant_name
                )
            except Exception as e:
                logger.error(f"QR generation failed: {e}")
                return render_template('checkout.html', cart=cart, error=f'QR failed: {e}', total_price=total_price)

        # === CASH ON DELIVERY ===
        send_telegram_message(name, email, phone, address, selected_cart, total_price, payment_method, bill_number)
        session['cart'] = [i for i in cart if i['id'] not in sel]
        session.modified = True
        logger.info(f"COD order placed: {bill_number}")
        return render_template('customer_thanks.html', name=name, address=address, paid=False)

    total_price = sum(i['price'] * i['quantity'] for i in cart)
    return render_template('checkout.html', cart=cart, total_price=total_price)

# ----------------------------------------------------------------------
# Payment Status – OFFICIAL SDK
# ----------------------------------------------------------------------
@app.post('/check_payment_status')
def check_payment_status():
    md5 = request.get_json().get('md5')
    if not md5:
        return jsonify({'error': 'md5 missing'}), 400

    transaction = session.get('transaction', {})
    if transaction.get('md5') != md5:
        return jsonify({'error': 'Invalid md5'}), 400

    try:
        khqr = KHQR(token)
        status = khqr.check_payment(md5)  # "PAID" or "UNPAID"

        if status == "PAID":
            notify_paid(transaction)

            if not transaction.get('invoice_generated', False):
                pdf_path = generate_pdf_invoice(transaction, transaction.get('cart', []))
                transaction['invoice_path'] = pdf_path
                transaction['invoice_generated'] = True
                session['transaction'] = transaction
                session.modified = True

            session['cart'] = []
            session.modified = True
            logger.info(f"Payment CONFIRMED → {md5}")
            return jsonify({'paid': True, 'redirect': url_for('customer_thanks')})

        return jsonify({'paid': False})
    except Exception as e:
        logger.error(f"SDK check_payment error: {e}")
        return jsonify({'error': str(e)}), 500

# ----------------------------------------------------------------------
# Download Invoice
# ----------------------------------------------------------------------
@app.route('/download_invoice')
def download_invoice():
    transaction = session.get('transaction', {})
    pdf_path = transaction.get('invoice_path')
    if not pdf_path or not os.path.exists(pdf_path):
        return "Invoice not found.", 404

    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"invoices/invoice_{transaction['bill_number']}.pdf"
    )

# ----------------------------------------------------------------------
# Thank You Page
# ----------------------------------------------------------------------
@app.get('/customer_thanks')
def customer_thanks():
    transaction = session.get('transaction', {})
    if not transaction:
        return render_template(
            'customer_thanks.html',
            name="Customer", address="", bill_number="N/A",
            amount_khr=0, paid=False, has_invoice=False
        )

    return render_template(
        'customer_thanks.html',
        name=transaction.get('name', 'Customer'),
        address=transaction.get('address', ''),
        bill_number=transaction.get('bill_number', 'N/A'),
        amount_khr=transaction.get('total_khr', 0),
        paid=True,
        has_invoice=transaction.get('invoice_generated', False)
    )

# ----------------------------------------------------------------------


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)