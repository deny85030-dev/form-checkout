from flask import Flask, request, render_template_string, redirect, session
from datetime import datetime
import os
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import wraps

app = Flask(__name__)
app.secret_key = 'morahshop-secret-key-2026'

# ========================== KONFIGURASI ====================
STORE_NAME = 'FORM CHECKOUT'
WHATSAPP_ADMIN = '6285138718594'
EMAIL_SENDER = 'morahshop@gmail.com'
EMAIL_PASSWORD = 'ewsv nupx pvem olmq'
FONNTE_API_KEY = 'aM5d4QEx2uEV2bjtt3ta3'
ADMIN_PASSWORD = 'admin123'

# Data produk
products = {
    'name': 'Cuan Digital Academy',
    'price': 10000,
    'description': 'Paket Marketing Komplit\n\n✅ YouTube Masterclass\n✅ TikTok Shop Masterclass\n✅ Shopee Top Creator\n✅ Organic Traffic Mastery\n✅ Meta Ads Simple System\n✅ AI Chatbot Selling\n\nBelajar step-by-step dengan materi simpel dan mudah dipraktikkan.\n\n🎯 Cocok untuk Pemula\n📱 Bisa Dipelajari dari HP\n⚡ Fokus Praktek & Hasil\n\n📌 7 Hari - 7 Kelas - 7 Strategi\n📌 Sistem jalan, cuan datang!',
    'payment_instructions': '🏦 Bank Jago\nNo. Rekening: 106371536422\na.n. Deny Prasetyo',
    'product_image': ''
}

QRIS_IMAGE_URL = "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjdEuaeTQp9-oYTbkTybyGb4hV23Gbdi12E9p9x3SJNlzJCfweazzWg2Tr6iSXHFXlSxi845dqwVbRZQ8CPnI63_mtQ9wNltEb_gDtJtP5GiI_YeIZLWnBVw_AZ1Glo_0RfuHBupJFra28Gf1M3idWT6l9G_edl1DNSjZ5P9DLhT5CFzwCIkG7pWGHLYSk/w398-h400/photo_2026-05-14_06-29-01.jpg"

orders = []

# ==================== FUNGSI KIRIM WA ====================
def send_whatsapp(phone_number, message):
    try:
        phone_number = ''.join(filter(str.isdigit, phone_number))
        if phone_number.startswith('0'):
            phone_number = '62' + phone_number[1:]
        if not phone_number.startswith('62'):
            phone_number = '62' + phone_number
        
        url = "https://api.fonnte.com/send"
        headers = {"Authorization": FONNTE_API_KEY, "Content-Type": "application/x-www-form-urlencoded"}
        data = {"target": phone_number, "message": message, "countryCode": "62"}
        
        response = requests.post(url, headers=headers, data=data)
        return response.json().get('status', False)
    except Exception as e:
        print(f"WA Error: {e}")
        return False

# ==================== FUNGSI KIRIM EMAIL ====================
def send_email(to_email, customer_name, invoice_number, product_name, price, qris_url):
    try:
        email_html = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="font-family:Arial;background:#f3f4f6;padding:20px;">
        <div style="max-width:500px;margin:auto;background:white;border-radius:16px;overflow:hidden;">
            <div style="background:#764ba2;padding:30px;text-align:center;color:white;">
                <h2>🧾 INVOICE PESANAN</h2>
            </div>
            <div style="padding:30px;">
                <p>Halo <b>{customer_name}</b>,</p>
                <p>Terima kasih telah berbelanja di <b>{STORE_NAME}</b>.</p>
                
                <div style="background:#f8f9fa;border-radius:12px;padding:20px;margin:20px 0;">
                    <b>📋 Invoice:</b> {invoice_number}<br><br>
                    <b>📅 Tanggal:</b> {datetime.now().strftime('%d %B %Y %H:%M')}<br><br>
                    <b>📦 Produk:</b> {product_name}<br><br>
                    <b>💰 Total:</b> <span style="font-size:20px;font-weight:bold;color:#764ba2;">Rp {price}</span><br><br>
                    <b>📊 Status:</b> 
                    <span style="background:#fef3c7;padding:5px 15px;border-radius:50px;">⏳ Menunggu Pembayaran</span>
                </div>
                
                <div style="text-align:center;margin:25px 0;">
                    <img src="{qris_url}" style="width:200px;" alt="QRIS">
                    <p style="font-size:12px;color:#666;">Scan QRIS di atas untuk pembayaran</p>
                </div>
                
                <div style="background:#f0fdf4;border-radius:12px;padding:15px;margin:20px 0;">
                    <b>🏦 Transfer Bank Jago</b><br>
                    No. Rekening: 106371536422<br>
                    a.n. Deny Prasetyo
                </div>
                
                <hr style="margin:25px 0;">
                <p style="font-size:12px;color:#999;text-align:center;">
                    Butuh bantuan? Hubungi: wa.me/{WHATSAPP_ADMIN}
                </p>
            </div>
            <div style="background:#111827;padding:15px;text-align:center;color:white;font-size:11px;">
                © 2026 {STORE_NAME}
            </div>
        </div>
        </body>
        </html>
        """
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Invoice {invoice_number} - {STORE_NAME}"
        msg['From'] = EMAIL_SENDER
        msg['To'] = to_email
        msg.attach(MIMEText(email_html, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, to_email, msg.as_string())
        server.quit()
        
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

# ==================== DEKORATOR PROTECT ADMIN ====================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect('/admin-login')
        return f(*args, **kwargs)
    return decorated_function

# ==================== TEMPLATE HTML ====================

HOME_TEMPLATE = '''
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ store }} - Belajar Digital Marketing</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }
        
        .container {
            max-width: 500px;
            margin: 0 auto;
        }
        
        .card {
            background: white;
            border-radius: 32px;
            overflow: hidden;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        }
        
        .product-image {
            width: 100%;
            max-height: 300px;
            object-fit: cover;
            background: #f3f4f6;
        }
        
        .product-info {
            padding: 28px;
        }
        
        .store-name {
            font-size: 12px;
            color: #764ba2;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }
        
        .product-title {
            font-size: 28px;
            font-weight: 700;
            color: #1f2937;
            margin-bottom: 8px;
            line-height: 1.2;
        }
        
        .price {
            font-size: 32px;
            font-weight: 700;
            color: #764ba2;
            margin-bottom: 24px;
        }
        
        .description {
            color: #374151;
            line-height: 1.6;
            margin-bottom: 28px;
            font-size: 15px;
        }
        
        .description br {
            display: block;
            content: "";
            margin: 4px 0;
        }
        
        .btn {
            display: block;
            width: 100%;
            background: #764ba2;
            color: white;
            text-align: center;
            padding: 16px;
            border-radius: 60px;
            text-decoration: none;
            font-weight: 600;
            font-size: 18px;
            transition: transform 0.2s, background 0.2s;
            border: none;
            cursor: pointer;
        }
        
        .btn:hover {
            background: #5b3a7e;
            transform: scale(0.98);
        }
        
        .footer-note {
            font-size: 12px;
            color: #9ca3af;
            text-align: center;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            {% if product_image and product_image != '' %}
            <img src="{{ product_image }}" class="product-image" alt="{{ product_name }}">
            {% endif %}
            <div class="product-info">
                <div class="store-name">{{ store }}</div>
                <h1 class="product-title">{{ product_name }}</h1>
                <div class="price">Rp {{ product_price }}</div>
                <div class="description">{{ product_desc|safe }}</div>
                <a href="/checkout" class="btn">🛒 Beli Sekarang</a>
                <div class="footer-note">✅ 100% Garansi | ✅ Support 24/7</div>
            </div>
        </div>
    </div>
</body>
</html>
'''

CHECKOUT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Checkout - {{ store }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }
        
        .container {
            max-width: 500px;
            margin: 0 auto;
        }
        
        .card {
            background: white;
            border-radius: 32px;
            padding: 32px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        }
        
        h2 {
            font-size: 24px;
            font-weight: 700;
            color: #1f2937;
            margin-bottom: 8px;
        }
        
        .subtitle {
            color: #6b7280;
            font-size: 14px;
            margin-bottom: 24px;
        }
        
        .product-summary {
            background: #f9fafb;
            border-radius: 20px;
            padding: 20px;
            margin-bottom: 24px;
            text-align: center;
        }
        
        .product-summary .name {
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 8px;
        }
        
        .product-summary .price {
            font-size: 28px;
            font-weight: 700;
            color: #764ba2;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            font-weight: 600;
            color: #374151;
            margin-bottom: 8px;
            font-size: 14px;
        }
        
        input {
            width: 100%;
            padding: 14px 16px;
            border: 1.5px solid #e5e7eb;
            border-radius: 16px;
            font-size: 16px;
            transition: border-color 0.2s;
        }
        
        input:focus {
            outline: none;
            border-color: #764ba2;
        }
        
        button {
            width: 100%;
            background: #764ba2;
            color: white;
            padding: 16px;
            border: none;
            border-radius: 60px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, background 0.2s;
            margin-top: 12px;
        }
        
        button:hover {
            background: #5b3a7e;
            transform: scale(0.98);
        }
        
        .back-link {
            text-align: center;
            margin-top: 20px;
        }
        
        .back-link a {
            color: #6b7280;
            text-decoration: none;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h2>🛒 Checkout</h2>
            <div class="subtitle">Lengkapi data untuk melanjutkan</div>
            
            <div class="product-summary">
                <div class="name">{{ product_name }}</div>
                <div class="price">Rp {{ product_price }}</div>
            </div>
            
            <form method="POST" action="/process-checkout">
                <div class="form-group">
                    <label>Nama Lengkap</label>
                    <input type="text" name="customer" placeholder="Contoh: Deny Prasetyo" required>
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" name="email" placeholder="email@example.com" required>
                </div>
                <div class="form-group">
                    <label>Nomor WhatsApp</label>
                    <input type="tel" name="whatsapp" placeholder="08123456789" required>
                </div>
                <button type="submit">✅ Konfirmasi Pesanan</button>
            </form>
            
            <div class="back-link">
                <a href="/">← Kembali ke Toko</a>
            </div>
        </div>
    </div>
</body>
</html>
'''

SUCCESS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sukses - {{ store }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .card {
            background: white;
            border-radius: 32px;
            padding: 40px 32px;
            max-width: 400px;
            text-align: center;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        }
        
        .check-icon {
            font-size: 72px;
            margin-bottom: 20px;
        }
        
        h2 {
            font-size: 28px;
            color: #1f2937;
            margin-bottom: 12px;
        }
        
        .invoice {
            background: #f3f4f6;
            padding: 12px;
            border-radius: 12px;
            font-family: monospace;
            font-size: 14px;
            margin: 20px 0;
        }
        
        .info-box {
            background: #e8f4f8;
            border-radius: 20px;
            padding: 20px;
            text-align: left;
            margin: 20px 0;
            font-size: 14px;
            line-height: 1.8;
        }
        
        .btn {
            display: inline-block;
            background: #764ba2;
            color: white;
            padding: 14px 28px;
            border-radius: 60px;
            text-decoration: none;
            font-weight: 600;
            margin-top: 12px;
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="check-icon">✅</div>
        <h2>Pesanan Berhasil!</h2>
        <p>Terima kasih telah berbelanja</p>
        
        <div class="invoice">
            📋 Invoice: <strong>{{ invoice }}</strong>
        </div>
        
        <div class="info-box">
            📧 Email invoice sudah dikirim ke email Anda<br>
            📱 WhatsApp juga sudah kami kirim<br><br>
            💳 Silakan transfer ke:<br>
            <strong>Bank Jago</strong><br>
            106371536422<br>
            a.n. Deny Prasetyo
        </div>
        
        <a href="/" class="btn">Kembali ke Toko</a>
    </div>
</body>
</html>
'''

ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel - {{ store }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f3f4f6;
            padding: 40px 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        
        .card {
            background: white;
            border-radius: 24px;
            padding: 32px;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        h2 {
            font-size: 24px;
            color: #1f2937;
            margin-bottom: 8px;
        }
        
        h3 {
            font-size: 18px;
            color: #374151;
            margin: 24px 0 16px 0;
            padding-bottom: 8px;
            border-bottom: 2px solid #e5e7eb;
        }
        
        .logout {
            text-align: right;
            margin-bottom: 20px;
        }
        
        .logout a {
            color: #ef4444;
            text-decoration: none;
            font-size: 14px;
        }
        
        input, textarea {
            width: 100%;
            padding: 12px 14px;
            margin: 8px 0;
            border: 1.5px solid #e5e7eb;
            border-radius: 12px;
            font-size: 14px;
            font-family: inherit;
        }
        
        textarea {
            font-family: monospace;
            line-height: 1.5;
        }
        
        input:focus, textarea:focus {
            outline: none;
            border-color: #764ba2;
        }
        
        button {
            background: #764ba2;
            color: white;
            padding: 12px 20px;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 12px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }
        
        th {
            background: #f9fafb;
            font-weight: 600;
            color: #374151;
        }
        
        .help-text {
            background: #fef3c7;
            padding: 12px 16px;
            border-radius: 12px;
            font-size: 13px;
            margin-bottom: 20px;
            color: #92400e;
        }
        
        .current-img {
            max-width: 100px;
            border-radius: 12px;
            margin: 8px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logout">
            <a href="/admin-logout">🚪 Logout</a>
        </div>
        
        <div class="card">
            <h2>⚙️ Admin Panel</h2>
            <p style="color: #6b7280; margin-bottom: 20px;">Kelola produk dan lihat pesanan</p>
            
            <div class="help-text">
                💡 <strong>CARA MENULIS DESKRIPSI:</strong><br>
                Tekan ENTER 1x untuk pindah baris. Jarak akan rapi dan tidak berlebihan.
            </div>
            
            <h3>📦 Edit Produk</h3>
            <form method="POST" action="/update-product">
                <input type="text" name="name" placeholder="Nama Produk" value="{{ product.name }}" required>
                <input type="number" name="price" placeholder="Harga" value="{{ product.price }}" required>
                
                <label style="font-weight:600; margin-top:12px; display:block;">📝 Deskripsi Produk:</label>
                <textarea name="description" placeholder="Tulis deskripsi di sini..." rows="12" style="font-family:monospace; line-height:1.5;">{{ product.description }}</textarea>
                
                <textarea name="payment_instructions" placeholder="Instruksi Pembayaran" rows="3">{{ product.payment_instructions }}</textarea>
                
                <label style="font-weight:600; margin-top:16px; display:block;">🖼️ Link Foto Produk:</label>
                <input type="text" name="product_image" placeholder="https://i.imgur.com/xxxxx.jpg" value="{{ product.product_image }}">
                
                {% if product.product_image and product.product_image != '' %}
                <div style="margin:12px 0;">
                    <img src="{{ product.product_image }}" class="current-img">
                    <small style="color:#6b7280;">Preview gambar</small>
                </div>
                {% endif %}
                
                <p style="font-size:12px; color:#6b7280; margin-top:8px;">
                    📌 Upload gambar ke <strong>imgur.com</strong> → Copy link → Paste di atas
                </p>
                
                <button type="submit">💾 Simpan Perubahan</button>
            </form>
            
            <h3>📋 Daftar Pesanan ({{ orders|length }})</h3>
            {% if orders %}
            <table style="width:100%; border-collapse:collapse;">
                <tr style="background:#764ba2; color:white;">
                    <th style="padding:10px;">Invoice</th>
                    <th style="padding:10px;">Customer</th>
                    <th style="padding:10px;">Total</th>
                </tr>
                {% for order in orders %}
                <tr style="border-bottom:1px solid #ddd;">
                    <td style="padding:10px;">{{ order.invoice }}</td>
                    <td style="padding:10px;">{{ order.customer_name }}</td>
                    <td style="padding:10px;">Rp {{ order.price }}</td>
                </tr>
                {% endfor %}
            </table>
            {% else %}
            <p style="color: #9ca3af; text-align: center; padding: 40px;">✨ Belum ada pesanan</p>
            {% endif %}
        </div>
    </div>
</body>
</html>
'''

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .card {
            background: white;
            border-radius: 32px;
            padding: 40px;
            width: 100%;
            max-width: 400px;
            text-align: center;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        }
        
        h2 {
            font-size: 28px;
            color: #1f2937;
            margin-bottom: 24px;
        }
        
        input {
            width: 100%;
            padding: 14px 16px;
            border: 1.5px solid #e5e7eb;
            border-radius: 16px;
            font-size: 16px;
            margin-bottom: 20px;
        }
        
        input:focus {
            outline: none;
            border-color: #764ba2;
        }
        
        button {
            width: 100%;
            background: #764ba2;
            color: white;
            padding: 14px;
            border: none;
            border-radius: 60px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
        }
        
        .error {
            color: #ef4444;
            margin-bottom: 16px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="card">
        <h2>🔐 Admin Login</h2>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <input type="password" name="password" placeholder="Masukkan password" required>
            <button type="submit">Login</button>
        </form>
    </div>
</body>
</html>
'''

# ==================== ROUTES ====================

@app.route('/')
def home():
    # Konversi newline ke <br> dengan jarak normal
    desc_html = products['description'].replace('\n', '<br>')
    return render_template_string(HOME_TEMPLATE, 
        store=STORE_NAME,
        product_name=products['name'],
        product_price=f"{products['price']:,}",
        product_desc=desc_html,
        product_image=products.get('product_image', '')
    )

@app.route('/checkout')
def checkout():
    return render_template_string(CHECKOUT_TEMPLATE, 
        store=STORE_NAME,
        product_name=products['name'],
        product_price=f"{products['price']:,}"
    )

@app.route('/process-checkout', methods=['POST'])
def process_checkout():
    customer = request.form['customer']
    email = request.form['email']
    whatsapp = request.form['whatsapp']
    
    whatsapp_clean = ''.join(filter(str.isdigit, whatsapp))
    if whatsapp_clean.startswith('0'):
        whatsapp_clean = '62' + whatsapp_clean[1:]
    if not whatsapp_clean.startswith('62'):
        whatsapp_clean = '62' + whatsapp_clean
    
    invoice_number = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    order_data = {
        'invoice': invoice_number,
        'customer_name': customer,
        'customer_email': email,
        'customer_whatsapp': whatsapp_clean,
        'product_name': products['name'],
        'price': f"{products['price']:,}",
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    }
    orders.insert(0, order_data)
    
    send_email(email, customer, invoice_number, products['name'], f"{products['price']:,}", QRIS_IMAGE_URL)
    
    wa_msg = f"""📋 INVOICE PESANAN - {STORE_NAME}

Halo {customer},

Terima kasih telah berbelanja!

━━━━━━━━━━━━━━━━━━
📦 Produk: {products['name']}
💰 Harga: Rp {products['price']:,}
📋 Invoice: {invoice_number}
━━━━━━━━━━━━━━━━━━

🏦 Cara Bayar:
Bank Jago - 106371536422
a.n. Deny Prasetyo

📧 Cek email untuk QRIS & invoice lengkap!

Admin: wa.me/{WHATSAPP_ADMIN}"""
    
    send_whatsapp(whatsapp_clean, wa_msg)
    send_whatsapp(WHATSAPP_ADMIN, f"🔔 PESANAN BARU!\n\n👤 {customer}\n📱 {whatsapp_clean}\n📧 {email}\n📋 {invoice_number}\n💰 Rp {products['price']:,}")
    
    return render_template_string(SUCCESS_TEMPLATE, store=STORE_NAME, invoice=invoice_number)

# ==================== ROUTES ADMIN ====================

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['password'] == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect('/admin')
        return render_template_string(LOGIN_TEMPLATE, error='Password salah!')
    return render_template_string(LOGIN_TEMPLATE, error=None)

@app.route('/admin-logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect('/admin-login')

@app.route('/admin')
@login_required
def admin():
    return render_template_string(ADMIN_TEMPLATE, product=products, orders=orders, store=STORE_NAME)

@app.route('/update-product', methods=['POST'])
@login_required
def update_product():
    products['name'] = request.form['name']
    products['price'] = int(request.form['price'])
    products['description'] = request.form.get('description', '')
    products['payment_instructions'] = request.form.get('payment_instructions', '')
    products['product_image'] = request.form.get('product_image', '')
    
    return redirect('/admin')

@app.route('/test-wa')
def test_wa():
    result = send_whatsapp(WHATSAPP_ADMIN, "🧪 Test FORM-CHECKOUT: WA OK!")
    return "✅ WA OK" if result else "❌ WA GAGAL"

@app.route('/test-email')
def test_email():
    result = send_email(EMAIL_SENDER, "Test", "TEST-001", "Test", "50000", QRIS_IMAGE_URL)
    return "✅ EMAIL OK" if result else "❌ EMAIL GAGAL"

if __name__ == '__main__':
    app.run()
