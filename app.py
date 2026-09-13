from flask import Flask, request, jsonify, session, redirect
from datetime import datetime, timedelta
import os, json, requests, smtplib, random, string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import wraps
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = 'morahshop-secret-key-2026'

CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# ========================== KONFIGURASI ====================
STORE_NAME = 'Formula YouTube Monet'
WHATSAPP_ADMIN = '6285138718594'
EMAIL_SENDER = 'morahshop@gmail.com'
EMAIL_PASSWORD = 'ewsv nupx pvem olmq'
FONNTE_API_KEY = 'aM5d4QEx2uEV2bjtt3ta3'
ADMIN_PASSWORD = 'admin123'

PRODUCT_NAME = 'Kelas Formula YouTube Monet'
HARGA_PROMO = 99000
HARGA_NORMAL = 330000
DURASI_PROMO_MENIT = 10

BANK_NAME = 'Bank Jago'
BANK_ACCOUNT = '106371536422'
BANK_HOLDER = 'Deny Prasetyo'
QRIS_URL = "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjdEuaeTQp9-oYTbkTybyGb4hV23Gbdi12E9p9x3SJNlzJCfweazzWg2Tr6iSXHFXlSxi845dqwVbRZQ8CPnI63_mtQ9wNltEb_gDtJtP5GiI_YeIZLWnBVw_AZ1Glo_0RfuHBupJFra28Gf1M3idWT6l9G_edl1DNSjZ5P9DLhT5CFzwCIkG7pWGHLYSk/w398-h400/photo_2026-05-14_06-29-01.jpg"

USERS_FILE = '/tmp/users.json'
PROMO_FILE = '/tmp/promo.json'

# ========================== STORAGE ====================
def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, 'r') as f: return json.load(f)
        except: return []
    return []

def save_json(path, data):
    try:
        with open(path, 'w') as f: json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Save error: {e}")

# ========================== PROMO ====================
def get_promo_status():
    data = load_json(PROMO_FILE)
    now = datetime.now()
    if not data or 'waktu_selesai' not in data:
        waktu_selesai = now + timedelta(minutes=DURASI_PROMO_MENIT)
        save_json(PROMO_FILE, {'waktu_selesai': waktu_selesai.isoformat()})
        return True, DURASI_PROMO_MENIT * 60, waktu_selesai.isoformat()
    waktu_selesai = datetime.fromisoformat(data['waktu_selesai'])
    selisih = (waktu_selesai - now).total_seconds()
    if selisih > 0:
        return True, int(selisih), waktu_selesai.isoformat()
    else:
        return False, 0, waktu_selesai.isoformat()

def get_harga_sekarang():
    is_aktif, _, _ = get_promo_status()
    if is_aktif:
        return HARGA_PROMO, f"{HARGA_PROMO:,}".replace(',', '.'), True
    else:
        return HARGA_NORMAL, f"{HARGA_NORMAL:,}".replace(',', '.'), False

# ========================== WHATSAPP ====================
def send_whatsapp(phone, message):
    try:
        phone = ''.join(filter(str.isdigit, phone))
        if phone.startswith('0'): phone = '62' + phone[1:]
        if not phone.startswith('62'): phone = '62' + phone
        url = "https://api.fonnte.com/send"
        headers = {"Authorization": FONNTE_API_KEY}
        data = {"target": phone, "message": message, "countryCode": "62"}
        r = requests.post(url, headers=headers, data=data, timeout=15)
        print(f"WA Response: {r.text}")
        return r.json().get('status', False)
    except Exception as e:
        print(f"WA Error: {e}")
        return False

# ========================== EMAIL ====================
def send_email(to_email, subject, html_body):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_SENDER
        msg['To'] = to_email
        msg.attach(MIMEText(html_body, 'html'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect('/admin-login')
        return f(*args, **kwargs)
    return wrapper

def generate_invoice():
    date_part = datetime.now().strftime('%Y%m%d')
    random_part = ''.join(random.choices(string.digits, k=4))
    return f"INV-{date_part}-{random_part}"

def build_invoice_email(nama, email, whatsapp, invoice, price_display, is_promo):
    promo_badge = '<span style="background:#16a34a;color:white;padding:4px 10px;border-radius:8px;font-size:11px;">PROMO</span>' if is_promo else '<span style="background:#dc2626;color:white;padding:4px 10px;border-radius:8px;font-size:11px;">HARGA NORMAL</span>'
    return f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family:Arial,sans-serif;background:#f0f4f0;padding:20px;margin:0;">
    <div style="max-width:600px;margin:auto;background:white;border-radius:16px;overflow:hidden;">
        <div style="background:linear-gradient(135deg,#16a34a,#15803d);padding:30px;text-align:center;color:white;">
            <h1 style="margin:0;font-size:24px;">🧾 INVOICE PESANAN</h1>
            <p style="margin:8px 0 0;opacity:0.9;font-size:14px;">{STORE_NAME}</p>
        </div>
        <div style="padding:30px;">
            <p>Halo <b>{nama}</b>,</p>
            <p>Terima kasih telah mendaftar di <b>{STORE_NAME}</b>!</p>
            <div style="background:#f0fdf4;border-radius:12px;padding:20px;margin:20px 0;border-left:4px solid #16a34a;">
                <table style="width:100%;font-size:14px;">
                    <tr><td style="padding:6px 0;"><b>📋 Invoice</b></td><td style="text-align:right;font-family:monospace;font-weight:bold;color:#15803d;font-size:16px;">{invoice}</td></tr>
                    <tr><td style="padding:6px 0;"><b>📅 Tanggal</b></td><td style="text-align:right;">{datetime.now().strftime('%d %B %Y %H:%M')}</td></tr>
                    <tr><td style="padding:6px 0;"><b>👤 Nama</b></td><td style="text-align:right;">{nama}</td></tr>
                    <tr><td style="padding:6px 0;"><b>📧 Email</b></td><td style="text-align:right;">{email}</td></tr>
                    <tr><td style="padding:6px 0;"><b>📱 WhatsApp</b></td><td style="text-align:right;">{whatsapp}</td></tr>
                    <tr><td style="padding:6px 0;"><b>📦 Produk</b></td><td style="text-align:right;">{PRODUCT_NAME} {promo_badge}</td></tr>
                    <tr style="border-top:2px solid #16a34a;"><td style="padding:12px 0 0;"><b>💰 TOTAL</b></td><td style="text-align:right;padding:12px 0 0;"><span style="font-size:22px;font-weight:900;color:#16a34a;">Rp {price_display}</span></td></tr>
                </table>
            </div>
            <div style="text-align:center;margin:25px 0;">
                <p style="font-weight:bold;margin-bottom:12px;">📱 Scan QRIS:</p>
                <img src="{QRIS_URL}" style="width:220px;border-radius:12px;border:2px solid #16a34a;">
            </div>
            <div style="background:#fef3c7;border-radius:12px;padding:18px;margin:20px 0;border-left:4px solid #f59e0b;">
                <p style="margin:0 0 10px;font-weight:bold;color:#78350f;">🏦 Atau Transfer:</p>
                <p style="margin:4px 0;font-size:14px;"><b>{BANK_NAME}</b></p>
                <p style="margin:4px 0;font-size:18px;font-family:monospace;font-weight:bold;letter-spacing:1px;">{BANK_ACCOUNT}</p>
                <p style="margin:4px 0;font-size:13px;color:#78350f;">a.n. {BANK_HOLDER}</p>
            </div>
            <div style="background:#fef2f2;border-radius:12px;padding:18px;margin:20px 0;border-left:4px solid #dc2626;">
                <p style="margin:0;font-weight:bold;color:#991b1b;">⚠️ PENTING:</p>
                <p style="margin:8px 0 0;font-size:13px;color:#7f1d1d;">Setelah transfer, kirim bukti ke: <b>wa.me/{WHATSAPP_ADMIN}</b></p>
                <p style="margin:8px 0 0;font-size:13px;color:#7f1d1d;">Sertakan invoice <b>{invoice}</b>.</p>
            </div>
        </div>
        <div style="background:#111827;padding:18px;text-align:center;color:white;font-size:11px;">
            © 2026 {STORE_NAME}
        </div>
    </div>
    </body>
    </html>
    """

# ========================== API PROMO STATUS ====================
@app.route('/api/promo-status', methods=['GET', 'OPTIONS'])
def api_promo_status():
    if request.method == 'OPTIONS':
        return '', 200
    is_aktif, sisa_detik, waktu_selesai = get_promo_status()
    harga, harga_display, _ = get_harga_sekarang()
    return jsonify({
        'aktif': is_aktif,
        'sisa_detik': sisa_detik,
        'harga': harga,
        'harga_display': harga_display,
        'waktu_selesai': waktu_selesai
    })

# ========================== API REGISTER ====================
@app.route('/api/register', methods=['POST', 'OPTIONS'])
def api_register():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        data = request.get_json()
        nama = (data.get('nama') or '').strip()
        email = (data.get('email') or '').strip()
        whatsapp = (data.get('whatsapp') or '').strip()
        password = data.get('password') or ''

        if len(nama) < 3:
            return jsonify({'success': False, 'message': 'Nama minimal 3 karakter'}), 400
        if '@' not in email or '.' not in email:
            return jsonify({'success': False, 'message': 'Email tidak valid'}), 400

        whatsapp_clean = ''.join(filter(str.isdigit, whatsapp))
        if whatsapp_clean.startswith('0'): whatsapp_clean = '62' + whatsapp_clean[1:]
        if not whatsapp_clean.startswith('62'): whatsapp_clean = '62' + whatsapp_clean
        if len(whatsapp_clean) < 10:
            return jsonify({'success': False, 'message': 'Nomor WhatsApp tidak valid'}), 400

        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Password minimal 6 karakter'}), 400

        users = load_json(USERS_FILE)
        if any(u['email'].lower() == email.lower() for u in users):
            return jsonify({'success': False, 'message': 'Email sudah terdaftar'}), 400

        harga, harga_display, is_promo = get_harga_sekarang()
        invoice = generate_invoice()

        new_user = {
            'nama': nama,
            'email': email,
            'whatsapp': whatsapp_clean,
            'password': password,
            'invoice': invoice,
            'product': PRODUCT_NAME,
            'price': harga_display,
            'is_promo': is_promo,
            'status': 'pending_payment',
            'registered_at': datetime.now().isoformat()
        }
        users.append(new_user)
        save_json(USERS_FILE, users)

        promo_text = "🔥 *HARGA PROMO*" if is_promo else "💰 *HARGA NORMAL*"
        wa_customer = (
            f"🧾 *INVOICE PESANAN*\n_{STORE_NAME}_\n\n"
            f"Halo *{nama}*,\n\nTerima kasih telah mendaftar!\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📋 *Invoice:* {invoice}\n"
            f"📦 *Produk:* {PRODUCT_NAME}\n"
            f"{promo_text}\n"
            f"💰 *Total:* Rp {harga_display}\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"*CARA PEMBAYARAN:*\n\n"
            f"🏦 *{BANK_NAME}*\n"
            f"No. Rek: *{BANK_ACCOUNT}*\n"
            f"a.n. {BANK_HOLDER}\n\n"
            f"📱 *Atau scan QRIS* (cek email)\n\n"
            f"⚠️ Setelah transfer, kirim bukti ke admin:\n"
            f"wa.me/{WHATSAPP_ADMIN}\n\n"
            f"Sertakan invoice *{invoice}*"
        )
        wa_result = send_whatsapp(whatsapp_clean, wa_customer)
        print(f"WA customer result: {wa_result}")

        invoice_html = build_invoice_email(nama, email, whatsapp_clean, invoice, harga_display, is_promo)
        email_result = send_email(email, f"🧾 Invoice {invoice} - {STORE_NAME}", invoice_html)
        print(f"Email result: {email_result}")

        admin_msg = (
            f"🔔 *PENDAFTARAN BARU!*\n\n"
            f"👤 {nama}\n📧 {email}\n📱 {whatsapp_clean}\n"
            f"📋 {invoice}\n💰 Rp {harga_display} ({'PROMO' if is_promo else 'NORMAL'})\n\n"
            f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
        send_whatsapp(WHATSAPP_ADMIN, admin_msg)

        return jsonify({
            'success': True,
            'message': 'Pendaftaran berhasil!',
            'invoice': invoice,
            'nama': nama,
            'email': email,
            'whatsapp': whatsapp_clean,
            'product': PRODUCT_NAME,
            'price': harga_display,
            'is_promo': is_promo,
            'bank_name': BANK_NAME,
            'bank_account': BANK_ACCOUNT,
            'bank_holder': BANK_HOLDER,
            'qris_url': QRIS_URL,
            'admin_wa': WHATSAPP_ADMIN,
            'wa_sent': wa_result,
            'email_sent': email_result
        })

    except Exception as e:
        print(f"Register error: {e}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

# ========================== ADMIN ====================
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['password'] == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect('/admin')
        return "Password salah! <a href='/admin-login'>Coba lagi</a>"
    return '''
    <form method="POST" style="font-family:Arial;max-width:400px;margin:100px auto;padding:40px;background:#f3f4f6;border-radius:20px;text-align:center;">
        <h2>🔐 Admin Login</h2>
        <input type="password" name="password" placeholder="Password" required style="width:100%;padding:14px;border-radius:12px;border:1px solid #ccc;margin:16px 0;box-sizing:border-box;">
        <button type="submit" style="width:100%;padding:14px;background:#16a34a;color:white;border:none;border-radius:12px;font-weight:bold;cursor:pointer;">Login</button>
    </form>
    '''

@app.route('/admin-logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect('/admin-login')

@app.route('/admin')
@login_required
def admin():
    users = load_json(USERS_FILE)
    rows = ''
    for u in users:
        status_color = '#f59e0b' if u.get('status') == 'pending_payment' else '#16a34a'
        promo_tag = ' 🔥' if u.get('is_promo') else ''
        rows += f"<tr><td>{u.get('invoice','-')}</td><td>{u['nama']}</td><td>{u['email']}</td><td>{u.get('whatsapp','-')}</td><td>Rp {u.get('price','-')}{promo_tag}</td><td><span style='background:{status_color};color:white;padding:4px 10px;border-radius:10px;font-size:11px;'>{u.get('status','-')}</span></td><td>{u.get('registered_at','-')[:10]}</td></tr>"
    if not rows:
        rows = '<tr><td colspan="7" style="text-align:center;padding:40px;color:#999;">Belum ada user</td></tr>'
    return f"""
    <!DOCTYPE html><html><head><title>Admin Panel</title>
    <style>
        body {{ font-family:Arial;background:#f3f4f6;padding:20px;margin:0; }}
        .card {{ background:white;border-radius:20px;padding:30px;max-width:1100px;margin:auto; }}
        h2 {{ color:#1f2937; }}
        table {{ width:100%;border-collapse:collapse;margin-top:16px;font-size:13px; }}
        th {{ background:#16a34a;color:white;padding:12px;text-align:left; }}
        td {{ padding:10px;border-bottom:1px solid #eee; }}
        a.logout {{ color:#dc2626;text-decoration:none;float:right;font-size:14px; }}
        .stat {{ display:inline-block;background:#f0fdf4;border-radius:12px;padding:12px 20px;margin-right:10px;margin-bottom:10px; }}
        .stat b {{ color:#16a34a;font-size:24px;display:block; }}
        a.btn {{ display:inline-block;background:#f59e0b;color:white;padding:10px 16px;border-radius:10px;text-decoration:none;margin-top:10px;font-size:13px;font-weight:bold; }}
    </style></head><body>
    <div class="card">
        <a class="logout" href="/admin-logout">🚪 Logout</a>
        <h2>⚙️ Admin Panel</h2>
        <div>
            <div class="stat">👥 Total User<b>{len(users)}</b></div>
            <div class="stat">⏳ Menunggu Bayar<b>{sum(1 for u in users if u.get('status')=='pending_payment')}</b></div>
            <div class="stat">🔥 Beli Promo<b>{sum(1 for u in users if u.get('is_promo'))}</b></div>
        </div>
        <a class="btn" href="/admin-reset-promo">🔄 Reset Timer Promo</a>
        <table>
            <tr><th>Invoice</th><th>Nama</th><th>Email</th><th>WA</th><th>Total</th><th>Status</th><th>Tanggal</th></tr>
            {rows}
        </table>
    </div></body></html>
    """

@app.route('/admin-reset-promo')
@login_required
def admin_reset_promo():
    if os.path.exists(PROMO_FILE):
        os.remove(PROMO_FILE)
    return "✅ Promo direset. Timer 10 menit dimulai lagi. <a href='/admin'>Kembali ke Admin</a>"

# ========================== TEST ====================
@app.route('/test-wa')
def test_wa():
    result = send_whatsapp(WHATSAPP_ADMIN, "🧪 Test: WA dari Vercel OK!")
    return f"{'✅ WA OK' if result else '❌ WA GAGAL - Cek saldo Fonnte / log Vercel'}"

@app.route('/test-email')
def test_email():
    result = send_email(
        EMAIL_SENDER,
        "Test Email dari Vercel",
        "<h2>Test</h2><p>Kalau email ini masuk, berarti Gmail App Password OK.</p>"
    )
    return f"{'✅ EMAIL OK' if result else '❌ EMAIL GAGAL - Cek Gmail App Password / log Vercel'}"

if __name__ == '__main__':
    app.run(debug=True)
