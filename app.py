from flask import Flask, request, jsonify, session, redirect
from datetime import datetime
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
EMAIL_PASSWORD = 'isbf qvjp lmmz aevv'
FONNTE_API_KEY = ''  # ⏸️ WA dimatikan sementara
ADMIN_PASSWORD = 'admin123'

PRODUCT_NAME = 'Kelas Formula YouTube Monet'
HARGA_CORET = 599000  # Harga coret (selalu tampil)

# ============================================================
# 🎯 SISTEM GELOMBANG HARGA
# Setiap kelipatan "KUOTA_PER_FASE" user, harga naik 1 tingkat
# ============================================================
KUOTA_PER_FASE = 100  # Setiap 100 member, harga naik

FASE_HARGA = [
    {'nama': 'Fase 1 - Early Bird', 'harga': 99000},   # 0-99 member
    {'nama': 'Fase 2',              'harga': 149000},  # 100-199 member
    {'nama': 'Fase 3',              'harga': 199000},  # 200-299 member
    {'nama': 'Fase 4',              'harga': 249000},  # 300-399 member
    {'nama': 'Fase 5',              'harga': 299000},  # 400-499 member
    {'nama': 'Harga Normal',        'harga': 599000},  # 500+ member
]

# PEMBAYARAN
BANK_NAME = 'Bank Jago'
BANK_ACCOUNT = '106371536422'
BANK_HOLDER = 'Deny Prasetyo'
QRIS_URL = "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjdEuaeTQp9-oYTbkTybyGb4hV23Gbdi12E9p9x3SJNlzJCfweazzWg2Tr6iSXHFXlSxi845dqwVbRZQ8CPnI63_mtQ9wNltEb_gDtJtP5GiI_YeIZLWnBVw_AZ1Glo_0RfuHBupJFra28Gf1M3idWT6l9G_edl1DNSjZ5P9DLhT5CFzwCIkG7pWGHLYSk/w398-h400/photo_2026-05-14_06-29-01.jpg"

USERS_FILE = '/tmp/users.json'

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

# ========================== GELOMBANG HARGA ====================
def get_harga_sekarang():
    """
    Hitung harga berdasarkan jumlah user terdaftar.
    Setiap KUOTA_PER_FASE user, harga naik 1 tingkat.
    """
    users = load_json(USERS_FILE)
    total_user = len(users)
    
    # Hitung fase: 0 = Fase 1, 1 = Fase 2, dst
    fase_index = total_user // KUOTA_PER_FASE
    
    # Kalau fase_index lebih dari jumlah fase, pakai fase terakhir
    if fase_index >= len(FASE_HARGA):
        fase_index = len(FASE_HARGA) - 1
    
    fase = FASE_HARGA[fase_index]
    harga = fase['harga']
    harga_display = f"{harga:,}".replace(',', '.')
    harga_coret_display = f"{HARGA_CORET:,}".replace(',', '.')
    
    # Hitung sisa slot sampai harga naik berikutnya
    slot_terpakai_di_fase_ini = total_user % KUOTA_PER_FASE
    sisa_slot = KUOTA_PER_FASE - slot_terpakai_di_fase_ini
    
    # Kalau sudah fase terakhir (Harga Normal), tidak ada sisa slot
    is_last_fase = (fase_index == len(FASE_HARGA) - 1)
    if is_last_fase:
        sisa_slot = 0
    
    is_discount = harga < HARGA_CORET  # True kalau masih ada diskon
    
    return {
        'harga': harga,
        'harga_display': harga_display,
        'harga_coret': HARGA_CORET,
        'harga_coret_display': harga_coret_display,
        'fase_nama': fase['nama'],
        'fase_index': fase_index,
        'fase_number': fase_index + 1,
        'total_user': total_user,
        'sisa_slot': sisa_slot,
        'is_discount': is_discount,
        'is_last_fase': is_last_fase,
        'kuota_per_fase': KUOTA_PER_FASE
    }

# ========================== WHATSAPP (DIMATIKAN) ====================
def send_whatsapp(phone, message):
    print(f"[WA SKIP] Belum ada saldo Fonnte. Target: {phone}")
    return False

# ========================== EMAIL ====================
def send_email(to_email, subject, html_body):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{STORE_NAME} <{EMAIL_SENDER}>"
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

# ========================== EMAIL: INVOICE CUSTOMER ====================
def build_invoice_email(nama, email, whatsapp, invoice, harga_data):
    harga_display = harga_data['harga_display']
    harga_coret_display = harga_data['harga_coret_display']
    fase_nama = harga_data['fase_nama']
    is_discount = harga_data['is_discount']
    
    diskon_row = ''
    if is_discount:
        diskon_row = f'<tr><td style="padding:6px 0;color:#555;">🏷️ Fase</td><td style="text-align:right;font-weight:bold;color:#16a34a;">{fase_nama}</td></tr>'
    
    harga_coret_html = ''
    if is_discount:
        harga_coret_html = f'<div style="text-align:right;font-size:14px;color:#999;text-decoration:line-through;">Rp {harga_coret_display}</div>'
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family:Arial,sans-serif;background:#f0f4f0;padding:20px;margin:0;">
    <div style="max-width:600px;margin:auto;background:white;border-radius:16px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.08);">
        <div style="background:linear-gradient(135deg,#16a34a,#15803d);padding:30px;text-align:center;color:white;">
            <h1 style="margin:0;font-size:26px;">🧾 INVOICE PESANAN</h1>
            <p style="margin:8px 0 0;opacity:0.9;font-size:14px;">{STORE_NAME}</p>
        </div>
        <div style="padding:30px;">
            <p style="font-size:15px;">Halo <b>{nama}</b>,</p>
            <p style="font-size:14px;color:#555;">Terima kasih telah mendaftar di <b>{STORE_NAME}</b>!</p>
            
            <div style="background:#f0fdf4;border-radius:12px;padding:20px;margin:20px 0;border-left:4px solid #16a34a;">
                <table style="width:100%;font-size:14px;border-collapse:collapse;">
                    <tr><td style="padding:6px 0;color:#555;">📋 Kode Invoice</td><td style="text-align:right;font-family:monospace;font-weight:bold;color:#15803d;font-size:16px;">{invoice}</td></tr>
                    <tr><td style="padding:6px 0;color:#555;">📅 Tanggal</td><td style="text-align:right;">{datetime.now().strftime('%d %B %Y %H:%M')}</td></tr>
                    <tr><td style="padding:6px 0;color:#555;">👤 Nama</td><td style="text-align:right;">{nama}</td></tr>
                    <tr><td style="padding:6px 0;color:#555;">📧 Email</td><td style="text-align:right;">{email}</td></tr>
                    <tr><td style="padding:6px 0;color:#555;">📱 WhatsApp</td><td style="text-align:right;">{whatsapp}</td></tr>
                    <tr><td style="padding:6px 0;color:#555;">📦 Produk</td><td style="text-align:right;">{PRODUCT_NAME}</td></tr>
                    {diskon_row}
                </table>
                
                <div style="border-top:2px solid #16a34a;margin-top:14px;padding-top:14px;">
                    {harga_coret_html}
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-weight:bold;font-size:15px;">💰 TOTAL BAYAR</span>
                        <span style="font-size:24px;font-weight:900;color:#16a34a;">Rp {harga_display}</span>
                    </div>
                </div>
            </div>
            
            <div style="text-align:center;margin:25px 0;">
                <p style="font-weight:bold;margin-bottom:12px;font-size:14px;">📱 Scan QRIS untuk pembayaran:</p>
                <img src="{QRIS_URL}" style="width:220px;border-radius:12px;border:2px solid #16a34a;" alt="QRIS">
            </div>
            
            <div style="background:#fef3c7;border-radius:12px;padding:18px;margin:20px 0;border-left:4px solid #f59e0b;">
                <p style="margin:0 0 10px;font-weight:bold;color:#78350f;font-size:14px;">🏦 Atau Transfer Bank:</p>
                <p style="margin:4px 0;font-size:14px;"><b>{BANK_NAME}</b></p>
                <p style="margin:4px 0;font-size:20px;font-family:monospace;font-weight:bold;letter-spacing:1px;">{BANK_ACCOUNT}</p>
                <p style="margin:4px 0;font-size:13px;color:#78350f;">a.n. {BANK_HOLDER}</p>
            </div>
            
            <div style="background:#fef2f2;border-radius:12px;padding:18px;margin:20px 0;border-left:4px solid #dc2626;">
                <p style="margin:0;font-weight:bold;color:#991b1b;font-size:14px;">⚠️ PENTING:</p>
                <p style="margin:8px 0 0;font-size:13px;color:#7f1d1d;">Setelah transfer, kirim bukti ke WhatsApp admin: <b>wa.me/{WHATSAPP_ADMIN}</b></p>
                <p style="margin:8px 0 0;font-size:13px;color:#7f1d1d;">Sertakan kode invoice <b>{invoice}</b> agar proses cepat.</p>
            </div>
            
            <p style="font-size:12px;color:#999;text-align:center;margin-top:30px;">Butuh bantuan? Hubungi: wa.me/{WHATSAPP_ADMIN}</p>
        </div>
        <div style="background:#111827;padding:18px;text-align:center;color:white;font-size:11px;">
            © 2026 {STORE_NAME} · Semua hak dilindungi
        </div>
    </div>
    </body>
    </html>
    """

# ========================== EMAIL: NOTIF ADMIN ====================
def build_admin_notif_email(nama, email, whatsapp, invoice, harga_data):
    harga_display = harga_data['harga_display']
    fase_nama = harga_data['fase_nama']
    total_user = harga_data['total_user']
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family:Arial,sans-serif;background:#f3f4f6;padding:20px;margin:0;">
    <div style="max-width:500px;margin:auto;background:white;border-radius:16px;overflow:hidden;">
        <div style="background:linear-gradient(135deg,#f59e0b,#d97706);padding:24px;text-align:center;color:white;">
            <h2 style="margin:0;font-size:20px;">🔔 PENDAFTARAN BARU!</h2>
            <p style="margin:6px 0 0;opacity:0.9;font-size:12px;">{STORE_NAME}</p>
        </div>
        <div style="padding:24px;">
            <table style="width:100%;font-size:14px;border-collapse:collapse;">
                <tr><td style="padding:8px 0;color:#666;">👤 Nama</td><td style="text-align:right;font-weight:bold;">{nama}</td></tr>
                <tr><td style="padding:8px 0;color:#666;">📧 Email</td><td style="text-align:right;font-weight:bold;font-size:12px;">{email}</td></tr>
                <tr><td style="padding:8px 0;color:#666;">📱 WhatsApp</td><td style="text-align:right;font-weight:bold;">{whatsapp}</td></tr>
                <tr><td style="padding:8px 0;color:#666;">📋 Invoice</td><td style="text-align:right;font-family:monospace;font-weight:bold;">{invoice}</td></tr>
                <tr><td style="padding:8px 0;color:#666;">🏷️ Fase</td><td style="text-align:right;font-weight:bold;color:#16a34a;">{fase_nama}</td></tr>
                <tr><td style="padding:8px 0;color:#666;">💰 Total</td><td style="text-align:right;font-weight:bold;color:#16a34a;font-size:16px;">Rp {harga_display}</td></tr>
                <tr><td style="padding:8px 0;color:#666;">👥 Total Member</td><td style="text-align:right;font-weight:bold;">{total_user}</td></tr>
                <tr><td style="padding:8px 0;color:#666;">🕐 Waktu</td><td style="text-align:right;">{datetime.now().strftime('%d/%m/%Y %H:%M')}</td></tr>
            </table>
            
            <div style="background:#f0fdf4;border-radius:10px;padding:14px;margin-top:18px;text-align:center;">
                <p style="margin:0;font-size:12px;color:#555;">Lihat semua user di:</p>
                <a href="https://form-checkout.vercel.app/admin" style="color:#16a34a;font-weight:bold;text-decoration:none;font-size:13px;">form-checkout.vercel.app/admin</a>
            </div>
            
            <p style="margin-top:18px;font-size:12px;color:#999;text-align:center;">Hubungi customer via WA:<br><b>wa.me/{whatsapp}</b></p>
        </div>
        <div style="background:#111827;padding:14px;text-align:center;color:white;font-size:11px;">
            © 2026 {STORE_NAME} · Admin Notification
        </div>
    </div>
    </body>
    </html>
    """

# ========================== API: HARGA & FASE ====================
@app.route('/api/harga', methods=['GET', 'OPTIONS'])
def api_harga():
    if request.method == 'OPTIONS':
        return '', 200
    harga_data = get_harga_sekarang()
    return jsonify(harga_data)

# Alias biar kompatibel dengan kode lama
@app.route('/api/promo-status', methods=['GET', 'OPTIONS'])
def api_promo_status():
    if request.method == 'OPTIONS':
        return '', 200
    harga_data = get_harga_sekarang()
    return jsonify({
        'aktif': harga_data['is_discount'],
        'sisa_detik': 0,
        'status': 'harga_bertahap',
        'harga': harga_data['harga'],
        'harga_display': harga_data['harga_display'],
        'harga_coret_display': harga_data['harga_coret_display'],
        'fase_nama': harga_data['fase_nama'],
        'total_user': harga_data['total_user'],
        'sisa_slot': harga_data['sisa_slot'],
        'is_discount': harga_data['is_discount']
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

        # Hitung harga DULU sebelum tambah user
        harga_data = get_harga_sekarang()
        invoice = generate_invoice()

        new_user = {
            'nama': nama,
            'email': email,
            'whatsapp': whatsapp_clean,
            'password': password,
            'invoice': invoice,
            'product': PRODUCT_NAME,
            'harga': harga_data['harga'],
            'harga_display': harga_data['harga_display'],
            'fase_nama': harga_data['fase_nama'],
            'fase_number': harga_data['fase_number'],
            'status': 'pending_payment',
            'registered_at': datetime.now().isoformat()
        }
        users.append(new_user)
        save_json(USERS_FILE, users)

        # Kirim email invoice ke customer
        invoice_html = build_invoice_email(nama, email, whatsapp_clean, invoice, harga_data)
        email_result = send_email(email, f"🧾 Invoice {invoice} - {STORE_NAME}", invoice_html)
        print(f"[EMAIL CUSTOMER] {email} → {email_result}")

        # Kirim email notif ke admin
        admin_email_html = build_admin_notif_email(nama, email, whatsapp_clean, invoice, harga_data)
        admin_email_result = send_email(EMAIL_SENDER, f"🔔 Pendaftaran Baru - {nama} - Rp {harga_data['harga_display']}", admin_email_html)
        print(f"[EMAIL ADMIN] {EMAIL_SENDER} → {admin_email_result}")

        send_whatsapp(whatsapp_clean, "[WA skip]")

        return jsonify({
            'success': True,
            'message': 'Pendaftaran berhasil!',
            'invoice': invoice,
            'nama': nama,
            'email': email,
            'whatsapp': whatsapp_clean,
            'product': PRODUCT_NAME,
            'price': harga_data['harga_display'],
            'harga_coret': harga_data['harga_coret_display'],
            'fase_nama': harga_data['fase_nama'],
            'is_promo': harga_data['is_discount'],
            'bank_name': BANK_NAME,
            'bank_account': BANK_ACCOUNT,
            'bank_holder': BANK_HOLDER,
            'qris_url': QRIS_URL,
            'admin_wa': WHATSAPP_ADMIN,
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
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8"><title>Admin Login</title>
    <style>
        body { font-family:Arial; background:linear-gradient(135deg,#16a34a,#15803d); min-height:100vh; display:flex; align-items:center; justify-content:center; margin:0; padding:20px; }
        .card { background:white; border-radius:20px; padding:40px; max-width:400px; width:100%; box-shadow:0 20px 60px rgba(0,0,0,0.3); text-align:center; }
        h2 { color:#1f2937; margin:0 0 20px; }
        input { width:100%; padding:14px; border:2px solid #e5e7eb; border-radius:12px; font-size:15px; box-sizing:border-box; margin-bottom:16px; }
        input:focus { outline:none; border-color:#16a34a; }
        button { width:100%; padding:14px; background:#16a34a; color:white; border:none; border-radius:12px; font-weight:bold; font-size:15px; cursor:pointer; }
        button:hover { background:#15803d; }
    </style></head><body>
    <div class="card">
        <h2>🔐 Admin Login</h2>
        <form method="POST">
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    </div>
    </body></html>
    '''

@app.route('/admin-logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect('/admin-login')

@app.route('/admin')
@login_required
def admin():
    users = load_json(USERS_FILE)
    harga_data = get_harga_sekarang()
    
    rows = ''
    for u in users:
        status_color = '#f59e0b' if u.get('status') == 'pending_payment' else '#16a34a'
        rows += f"<tr><td style='font-family:monospace;font-size:12px;'>{u.get('invoice','-')}</td><td>{u['nama']}</td><td style='font-size:12px;'>{u['email']}</td><td>{u.get('whatsapp','-')}</td><td><b>Rp {u.get('harga_display', u.get('price','-'))}</b></td><td style='font-size:11px;'>{u.get('fase_nama','-')}</td><td><span style='background:{status_color};color:white;padding:4px 10px;border-radius:10px;font-size:11px;'>{u.get('status','-')}</span></td><td>{u.get('registered_at','-')[:10]}</td></tr>"
    if not rows:
        rows = '<tr><td colspan="8" style="text-align:center;padding:40px;color:#999;">Belum ada user</td></tr>'
    
    # Bangun tabel fase
    fase_rows = ''
    for i, fase in enumerate(FASE_HARGA):
        user_di_fase = 0
        if i < len(FASE_HARGA) - 1:
            user_di_fase = sum(1 for u in users if u.get('fase_number') == i + 1)
            range_text = f"{i * KUOTA_PER_FASE} - {(i+1) * KUOTA_PER_FASE - 1}"
        else:
            user_di_fase = sum(1 for u in users if u.get('fase_number') == i + 1)
            range_text = f"{i * KUOTA_PER_FASE}+"
        
        is_active = (harga_data['fase_index'] == i)
        bg_color = '#fef3c7' if is_active else 'white'
        bold = 'font-weight:bold;' if is_active else ''
        
        fase_rows += f"<tr style='background:{bg_color};'><td style='padding:10px;{bold}'>{fase['nama']}</td><td style='padding:10px;text-align:center;'>{range_text}</td><td style='padding:10px;text-align:right;{bold}'>Rp {fase['harga']:,}</td><td style='padding:10px;text-align:center;'>{user_di_fase} user</td></tr>".replace(',', '.')
    
    return f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8"><title>Admin Panel</title>
    <style>
        body {{ font-family:Arial;background:#f3f4f6;padding:20px;margin:0; }}
        .card {{ background:white;border-radius:20px;padding:30px;max-width:1200px;margin:auto;box-shadow:0 4px 12px rgba(0,0,0,0.05); }}
        h2 {{ color:#1f2937;margin-top:0; }}
        h3 {{ color:#374151;margin-top:24px;border-bottom:2px solid #e5e7eb;padding-bottom:8px; }}
        table {{ width:100%;border-collapse:collapse;margin-top:16px;font-size:13px; }}
        th {{ background:#16a34a;color:white;padding:12px;text-align:left; }}
        td {{ padding:10px;border-bottom:1px solid #eee; }}
        a.logout {{ color:#dc2626;text-decoration:none;float:right;font-size:14px; }}
        .stat {{ display:inline-block;background:#f0fdf4;border-radius:12px;padding:14px 22px;margin-right:10px;margin-bottom:10px;text-align:center; }}
        .stat b {{ color:#16a34a;font-size:26px;display:block; }}
        .stat span {{ font-size:12px;color:#666; }}
        .info-box {{ background:#eff6ff;border-radius:12px;padding:16px;margin:16px 0;border-left:4px solid #3b82f6;font-size:13px;color:#1e40af; }}
    </style></head><body>
    <div class="card">
        <a class="logout" href="/admin-logout">🚪 Logout</a>
        <h2>⚙️ Admin Panel</h2>
        
        <div class="info-box">
            🎯 <b>Sistem Harga Bertahap Aktif</b><br>
            Setiap <b>{KUOTA_PER_FASE} member</b>, harga naik 1 tingkat. Total: <b>{len(users)} member</b>.
        </div>
        
        <div>
            <div class="stat"><b>{len(users)}</b><span>👥 Total Member</span></div>
            <div class="stat"><b>Rp {harga_data['harga_display']}</b><span>💰 Harga Sekarang</span></div>
            <div class="stat"><b>{harga_data['fase_nama']}</b><span>🏷️ Fase Aktif</span></div>
            <div class="stat"><b>{harga_data['sisa_slot']}</b><span>⏳ Slot Sampai Naik</span></div>
        </div>
        
        <h3>📊 Tabel Fase Harga</h3>
        <table>
            <tr><th>Fase</th><th style="text-align:center;">Rentang Member</th><th style="text-align:right;">Harga</th><th style="text-align:center;">Jumlah User</th></tr>
            {fase_rows}
        </table>
        
        <h3>👥 Daftar Member ({len(users)})</h3>
        <table>
            <tr><th>Invoice</th><th>Nama</th><th>Email</th><th>WA</th><th>Bayar</th><th>Fase</th><th>Status</th><th>Tanggal</th></tr>
            {rows}
        </table>
    </div></body></html>
    """

# ========================== TEST ====================
@app.route('/test-email')
def test_email():
    result = send_email(
        EMAIL_SENDER,
        "✅ Test Email dari Vercel",
        """
        <div style="font-family:Arial;max-width:500px;margin:auto;background:white;border-radius:16px;overflow:hidden;">
            <div style="background:linear-gradient(135deg,#16a34a,#15803d);padding:30px;text-align:center;color:white;">
                <h2 style="margin:0;">✅ EMAIL BERFUNGSI!</h2>
            </div>
            <div style="padding:30px;">
                <p>Kalau Anda menerima email ini, artinya <b>Gmail App Password sudah benar</b>.</p>
            </div>
        </div>
        """
    )
    if result:
        return "✅ EMAIL OK — Cek inbox morahshop@gmail.com"
    else:
        return "❌ EMAIL GAGAL — Cek Gmail App Password"

@app.route('/test-wa')
def test_wa():
    return "⏸️ WA dinonaktifkan sementara. Belum ada saldo Fonnte."

@app.route('/api/reset-users')
def api_reset_users():
    """⚠️ HATI-HATI: Hapus semua user (buat testing)"""
    save_json(USERS_FILE, [])
    return "✅ Semua user dihapus. Sekarang di Fase 1 (Rp 99.000). <a href='/admin'>Kembali ke Admin</a>"

if __name__ == '__main__':
    app.run(debug=True)
