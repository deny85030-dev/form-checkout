from flask import Flask, request, render_template_string, redirect, session
from datetime import datetime
import os, json, smtplib, random, string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import wraps

app = Flask(__name__)
app.secret_key = 'kreatorpedia-secret-key-2026'

# ========================== KONFIGURASI ==========================
STORE_NAME = 'LABS Video Musik V9'
WHATSAPP_ADMIN = '6285138718594'
EMAIL_SENDER = 'kreatorpedia.official@gmail.com'
EMAIL_PASSWORD = 'moxx vval vnfu dezk'
ADMIN_PASSWORD = 'admin123'

PRODUCT_NAME = 'LABS Video Musik V9'
HARGA_CORET = 599000

KUOTA_PER_FASE = 100
FASE_HARGA = [
    {'nama': 'Fase 1 - Early Bird', 'harga': 59000},
    {'nama': 'Fase 2',              'harga': 99000},
    {'nama': 'Fase 3',              'harga': 149000},
    {'nama': 'Fase 4',              'harga': 199000},
    {'nama': 'Fase 5',              'harga': 249000},
    {'nama': 'Harga Normal',        'harga': 599000},
]

BANK_NAME = 'Bank Jago'
BANK_ACCOUNT = '1088 2371 6382'
BANK_HOLDER = 'MARIANI'

QRIS_URL = "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjPPV7BDPlGP-VrCsscNFc2hGCYA75CVZQZjjmBuABZIOvtDesN9jI4Si2h_fxwdzsP1YiyOz8VbIiOw8S3JPJ6eEvS_FwtwjVgfq6K0HyCEdiw2FCTyHVUy6xJKkVzKgB2mPewmuzYywqmdcMn9lk01O4HJ1KRWYip7RajJnCOYFDafRIhO9dCa_AZEjE/s320/QR%20KREATORPEDIA.jpg"
QRIS_HOLDER = 'KREATORPEDIA'

USERS_FILE = '/tmp/users.json'

# ========================== STORAGE ==========================
def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f: return json.load(f)
        except: return []
    return []

def save_users(data):
    try:
        with open(USERS_FILE, 'w') as f: json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Save error: {e}")

# ========================== HARGA ==========================
def get_harga():
    users = load_users()
    paid = sum(1 for u in users if u.get('status') == 'paid')
    idx = paid // KUOTA_PER_FASE
    if idx >= len(FASE_HARGA): idx = len(FASE_HARGA) - 1
    fase = FASE_HARGA[idx]
    harga = fase['harga']
    sisa = KUOTA_PER_FASE - (paid % KUOTA_PER_FASE)
    if idx == len(FASE_HARGA) - 1: sisa = 0
    return {
        'harga': harga,
        'harga_display': f"{harga:,}".replace(',', '.'),
        'harga_coret_display': f"{HARGA_CORET:,}".replace(',', '.'),
        'fase_nama': fase['nama'],
        'fase_number': idx + 1,
        'total_paid': paid,
        'total_pending': len(users) - paid,
        'sisa_slot': sisa,
        'is_discount': harga < HARGA_CORET,
    }

# ========================== EMAIL ==========================
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

def invoice_email(nama, email, wa, invoice, harga):
    return f"""
    <div style="font-family:Arial;max-width:600px;margin:auto;background:#f0f4f0;padding:20px;">
    <div style="background:white;border-radius:16px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#16a34a,#15803d);padding:30px;text-align:center;color:white;">
        <h1 style="margin:0;">🧾 INVOICE PESANAN</h1>
        <p style="margin:8px 0 0;font-size:14px;">{STORE_NAME}</p>
      </div>
      <div style="padding:30px;">
        <p>Halo <b>{nama}</b>,</p>
        <p>Terima kasih telah mendaftar!</p>
        <div style="background:#f0fdf4;border-radius:12px;padding:20px;margin:20px 0;border-left:4px solid #16a34a;">
          <table style="width:100%;font-size:14px;">
            <tr><td>📋 Invoice</td><td style="text-align:right;font-family:monospace;font-weight:bold;color:#15803d;">{invoice}</td></tr>
            <tr><td>👤 Nama</td><td style="text-align:right;">{nama}</td></tr>
            <tr><td>📧 Email</td><td style="text-align:right;">{email}</td></tr>
            <tr><td>📱 WA</td><td style="text-align:right;">{wa}</td></tr>
            <tr><td>🏷️ Fase</td><td style="text-align:right;color:#16a34a;font-weight:bold;">{harga['fase_nama']}</td></tr>
          </table>
          <div style="border-top:2px solid #16a34a;margin-top:14px;padding-top:14px;text-align:right;">
            <div style="font-size:14px;color:#999;text-decoration:line-through;">Rp {harga['harga_coret_display']}</div>
            <div style="font-size:24px;font-weight:900;color:#16a34a;">Rp {harga['harga_display']}</div>
          </div>
        </div>
        <div style="text-align:center;margin:25px 0;">
          <p style="font-weight:bold;">📱 Scan QRIS:</p>
          <img src="{QRIS_URL}" style="width:220px;border-radius:12px;border:2px solid #16a34a;">
          <p style="font-size:13px;color:#555;">a.n. <b>{QRIS_HOLDER}</b></p>
        </div>
        <div style="background:#fef3c7;border-radius:12px;padding:18px;border-left:4px solid #f59e0b;">
          <p style="margin:0 0 10px;font-weight:bold;color:#78350f;">🏦 Atau Transfer:</p>
          <p style="margin:4px 0;"><b>{BANK_NAME}</b></p>
          <p style="margin:4px 0;font-size:20px;font-family:monospace;font-weight:bold;">{BANK_ACCOUNT}</p>
          <p style="margin:4px 0;color:#78350f;">a.n. {BANK_HOLDER}</p>
        </div>
        <div style="background:#fef2f2;border-radius:12px;padding:18px;margin:20px 0;border-left:4px solid #dc2626;">
          <p style="margin:0;font-weight:bold;color:#991b1b;">⚠️ Setelah transfer, kirim bukti ke WA: <b>wa.me/{WHATSAPP_ADMIN}</b></p>
        </div>
      </div>
      <div style="background:#111827;padding:18px;text-align:center;color:white;font-size:11px;">© 2026 {STORE_NAME}</div>
    </div>
    </div>
    """

def aktivasi_email(nama, password):
    return f"""
    <div style="font-family:Arial;max-width:500px;margin:auto;background:white;border-radius:16px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#16a34a,#15803d);padding:30px;text-align:center;color:white;">
        <h1 style="margin:0;">🎉 AKUN AKTIF!</h1>
      </div>
      <div style="padding:30px;">
        <p>Halo <b>{nama}</b>,</p>
        <p>Pembayaran kamu sudah kami konfirmasi. Akun <b>AKTIF</b>!</p>
        <div style="background:#f0fdf4;border-radius:12px;padding:16px;margin:16px 0;border-left:4px solid #16a34a;">
          <p><b>Nama:</b> {nama}</p>
          <p><b>Password:</b> <code style="background:#e5e7eb;padding:2px 8px;border-radius:4px;">{password}</code></p>
        </div>
        <p style="text-align:center;margin-top:24px;">
          <a href="https://memberarea.kelasyoutube.my.id/?user={nama}&pass={password}"
             style="background:#16a34a;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold;">
             🚀 Masuk ke Member Area
          </a>
        </p>
      </div>
    </div>
    """

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect('/admin-login')
        return f(*args, **kwargs)
    return wrapper

def gen_invoice():
    return f"INV-{datetime.now().strftime('%Y%m%d')}-{''.join(random.choices(string.digits, k=4))}"

# ========================== TEMPLATES ==========================

LANDING = '''
<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Kelas Formula YouTube Monet</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f0f4f0;min-height:100vh;padding:12px;color:#0f1f0f;}
.app{max-width:600px;margin:0 auto;}
.hero{background:linear-gradient(160deg,#fff 0%,#f5faf5 100%);border-radius:28px;padding:24px 18px;border:1px solid #dce8dc;box-shadow:0 8px 30px rgba(0,20,0,.06);margin-bottom:16px;}
.badge{display:inline-flex;align-items:center;gap:8px;background:#e8f5e9;border:1px solid #c8e6c9;padding:5px 14px;border-radius:40px;font-size:10px;font-weight:700;color:#1B8A3F;text-transform:uppercase;margin-bottom:14px;}
.dot{width:7px;height:7px;background:#1B8A3F;border-radius:50%;animation:pulse 1.4s infinite;}
@keyframes pulse{50%{opacity:.3;transform:scale(.6);}}
h1{font-size:32px;font-weight:900;line-height:1.1;letter-spacing:-.6px;margin-bottom:6px;}
.grad{background:linear-gradient(135deg,#1B8A3F,#27ae60);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.sub{color:#4a6a4a;font-size:15px;line-height:1.6;margin-top:8px;}
.highlight{margin-top:18px;background:linear-gradient(135deg,#e8f5e9,#f0fdf4);border-radius:16px;padding:16px 18px;border:1px solid #c8e6c9;border-left:4px solid #1B8A3F;}
.highlight b{font-size:15px;font-weight:800;display:block;margin-bottom:6px;}
.highlight span{font-size:13px;color:#4a6a4a;line-height:1.6;}
.price-box{background:linear-gradient(135deg,#fafffa,#eaf5ea);border:2px solid #1B8A3F;border-radius:18px;padding:22px 18px;margin-top:16px;text-align:center;}
.price-label{font-size:12px;font-weight:700;color:#2d5a2d;text-transform:uppercase;letter-spacing:1px;}
.price-final{font-size:40px;font-weight:900;color:#0a1a0a;margin:8px 0 4px;letter-spacing:-1px;}
.price-final small{font-size:15px;font-weight:600;color:#4a6a4a;display:block;margin-top:4px;}
.price-note{font-size:13px;color:#4a6a4a;margin-top:10px;padding-top:12px;border-top:1px dashed rgba(27,138,63,.3);}
.price-coret{font-size:16px;color:#999;text-decoration:line-through;display:block;margin-bottom:2px;}
.btn{display:block;width:100%;background:linear-gradient(135deg,#1B8A3F,#27ae60);color:white;text-align:center;padding:16px;border-radius:60px;text-decoration:none;font-weight:800;font-size:16px;box-shadow:0 8px 30px rgba(27,138,63,.25);margin-top:18px;border:none;cursor:pointer;font-family:inherit;}
.btn:active{transform:scale(.97);}
.btn-blue{background:linear-gradient(135deg,#2c6b9c,#4a8ec4);box-shadow:0 6px 24px rgba(44,107,156,.15);}
.card{background:#fff;border-radius:22px;padding:24px 18px;margin-bottom:16px;border:1px solid #dce8dc;}
.card h2{font-size:20px;font-weight:700;color:#0a1a0a;margin-bottom:16px;padding-bottom:14px;border-bottom:1px dashed #dce8dc;}
.item{display:flex;gap:12px;padding:10px 12px;background:#f8fcf8;border-radius:12px;border:1px solid #eaf2ea;margin-bottom:10px;font-size:14px;line-height:1.5;color:#2d4a2d;}
.item b{color:#0a1a0a;}
.icon{color:#1B8A3F;font-weight:700;flex-shrink:0;width:24px;height:24px;background:#e8f5e9;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;}
.member-card{background:linear-gradient(135deg,#fafffa,#f0f8f0);border:2px solid #1B8A3F;border-radius:24px;padding:22px 18px;}
.member-card h3{font-size:19px;font-weight:700;margin-bottom:4px;}
.member-sub{color:#4a6a4a;font-size:14px;margin-bottom:18px;line-height:1.6;}
.tabs{display:flex;border-radius:14px;overflow:hidden;border:1px solid #dce8dc;margin-bottom:18px;}
.tab{flex:1;padding:12px;text-align:center;font-weight:700;font-size:14px;cursor:pointer;background:#f8fcf8;color:#4a6a4a;border:none;font-family:inherit;}
.tab.active{background:#1B8A3F;color:white;}
.form{display:none;}
.form.active{display:block;}
label{display:block;font-weight:600;font-size:13px;color:#1a3a1a;margin-bottom:4px;margin-top:12px;}
input{width:100%;padding:12px 16px;border:2px solid #dce8dc;border-radius:14px;font-size:15px;background:#fff;font-family:inherit;}
input:focus{outline:none;border-color:#1B8A3F;box-shadow:0 0 0 4px rgba(27,138,63,.06);}
.alert{padding:12px;border-radius:10px;margin-top:12px;font-size:13px;font-weight:600;text-align:center;display:none;}
.alert-error{background:#fdf0ed;color:#c0392b;border:1px solid #f5cdc5;}
.alert-success{background:#edf7ed;color:#1B8A3F;border:1px solid #c8e6c9;line-height:1.6;}
.switch-link{text-align:center;margin-top:14px;font-size:13px;color:#4a6a4a;}
.switch-link a{color:#1B8A3F;font-weight:700;text-decoration:none;cursor:pointer;}
.footer{text-align:center;margin-top:24px;padding:24px 16px;border-top:1px solid #dce8dc;font-size:12px;color:#8aaa8a;}
.footer b{color:#4a6a4a;}
</style>
</head>
<body>
<div class="app">
  <div class="hero">
    <div class="badge"><span class="dot"></span>🔥 <span id="live">276</span> orang sedang mengikuti kelas ini</div>
    <h1>Kelas Formula <br><span class="grad">YouTube Monet</span></h1>
    <p class="sub"><strong>Bawa channel YouTube-mu ke monetisasi dalam 30 hari</strong> — tanpa modal besar, tanpa wajah tampil, tanpa ribet editing.</p>
    <div class="highlight">
      <b>🎯 Peserta yang bergabung akan dibimbing sampai monet & berhasil</b>
      <span>Kami dampingi langkah demi langkah — dari nol sampai channel kamu <b>monetisasi</b> dan menghasilkan uang.</span>
    </div>
    <div class="price-box">
      <div class="price-label">💰 {{ fase_nama }}</div>
      <div class="price-final">
        {{ coret_html|safe }}
        Rp {{ harga_display }}
        <small>/ akses seumur hidup</small>
      </div>
      <div class="price-note">
        {% if sisa_slot > 0 %}⚡ <b>Harga naik setelah {{ sisa_slot }} pendaftar berikutnya!</b><br>{% endif %}
        ✅ Termasuk semua modul, tools AI, bonus eksklusif, dan garansi monet 1 bulan
      </div>
    </div>
    <a href="#memberArea" class="btn">🚀 Ambil Kelas Sekarang →</a>
  </div>

  <div class="card">
    <h2>📘 Apa Saja Yang Akan Kita Pelajari?</h2>
    <div class="item"><span class="icon">📺</span><span><b>Membuat Channel YouTube & Setting Dasar</b> — panduan lengkap dari membuat akun, setting privasi, hingga verifikasi.</span></div>
    <div class="item"><span class="icon">🔥</span><span><b>Teknik percepat 1.000 subscriber & 4.000 jam tayang</b> — memanfaatkan algoritma YouTube.</span></div>
    <div class="item"><span class="icon">✓</span><span><b>Syarat dan cara agar pengajuan monetisasi diterima</b> — checklist lengkap.</span></div>
    <div class="item"><span class="icon">🎯</span><span><b>Menentukan niche channel yang menguntungkan</b> — riset pasar untuk konten viral.</span></div>
    <div class="item"><span class="icon">🤖</span><span><b>Cara buat video tanpa editing manual</b> — tools AI gratis & premium.</span></div>
    <div class="item"><span class="icon">🎬</span><span><b>Buat video ASMR menggunakan AI</b> — teknik live 30 hari tanpa putus.</span></div>
  </div>

  <div id="memberArea" class="member-card">
    <h3>🔐 Akses Member Area</h3>
    <p class="member-sub">Daftar untuk mengakses semua modul, video, tools AI, dan bonus eksklusif.</p>

    <div class="tabs">
      <button class="tab active" data-tab="register" type="button">Daftar</button>
      <button class="tab" data-tab="login" type="button">Login</button>
    </div>

    <div class="form active" id="formRegister">
      {% if error %}<div class="alert alert-error" style="display:block;">❌ {{ error }}</div>{% endif %}
      {% if success %}<div class="alert alert-success" style="display:block;">{{ success|safe }}</div>{% endif %}
      <form method="POST" action="/daftar">
        <label>Nama Lengkap</label>
        <input type="text" name="nama" placeholder="Contoh: Andi Perkasa" required>
        <label>Email</label>
        <input type="email" name="email" placeholder="email@example.com" required>
        <label>Nomor WhatsApp</label>
        <input type="tel" name="whatsapp" placeholder="08123456789" required>
        <label>Password</label>
        <input type="password" name="password" placeholder="Minimal 6 karakter" required>
        <button type="submit" class="btn btn-blue" style="margin-top:16px;">📝 Daftar & Bayar Sekarang</button>
      </form>
      <p class="switch-link">Sudah punya akun? <a onclick="switchTab('login')">Silakan Login</a></p>
    </div>

    <div class="form" id="formLogin">
      {% if login_error %}<div class="alert alert-error" style="display:block;">❌ {{ login_error }}</div>{% endif %}
      <form method="POST" action="/masuk">
        <label>Nama Lengkap</label>
        <input type="text" name="nama" placeholder="Nama kamu" required>
        <label>Password</label>
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit" class="btn" style="margin-top:16px;">🚀 Masuk ke Kelas</button>
      </form>
      <p class="switch-link">Belum punya akun? <a onclick="switchTab('register')">Silakan Daftar</a></p>
    </div>
  </div>

  <div class="footer">
    © 2026 <b>Kelas Formula YouTube Monet</b> — All Rights Reserved<br>
    Powered by <b>Kreatorpedia</b>
  </div>
</div>

<script>
function switchTab(t){
  document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('active', x.dataset.tab===t));
  document.getElementById('formRegister').classList.toggle('active', t==='register');
  document.getElementById('formLogin').classList.toggle('active', t==='login');
}
document.querySelectorAll('.tab').forEach(t=>t.addEventListener('click',()=>switchTab(t.dataset.tab)));
{% if login_error %}switchTab('login');{% endif %}
{% if error or success %}switchTab('register');{% endif %}
</script>
</body>
</html>
'''

ADMIN_PAGE = '''
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Admin</title>
<style>
body{font-family:Arial;background:#f3f4f6;padding:20px;margin:0;}
.card{background:white;border-radius:20px;padding:30px;max-width:1400px;margin:auto;box-shadow:0 4px 12px rgba(0,0,0,.05);}
h2{color:#1f2937;margin-top:0;}h3{color:#374151;margin-top:24px;border-bottom:2px solid #e5e7eb;padding-bottom:8px;}
table{width:100%;border-collapse:collapse;margin-top:16px;font-size:12px;}
th{background:#16a34a;color:white;padding:10px;text-align:left;}
td{padding:8px;border-bottom:1px solid #eee;}
.logout{color:#dc2626;text-decoration:none;float:right;}
.stat{display:inline-block;background:#f0fdf4;border-radius:12px;padding:14px 22px;margin-right:10px;margin-bottom:10px;text-align:center;}
.stat b{color:#16a34a;font-size:24px;display:block;}.stat span{font-size:12px;color:#666;}
</style></head><body>
<div class="card">
<a class="logout" href="/admin-logout">🚪 Logout</a>
<h2>⚙️ Admin Panel — {{ store }}</h2>

<div>
<div class="stat"><b>{{ total_paid }}</b><span>✅ Terbayar</span></div>
<div class="stat"><b>{{ total_pending }}</b><span>⏳ Pending</span></div>
<div class="stat"><b>Rp {{ harga_display }}</b><span>💰 Harga</span></div>
<div class="stat"><b>{{ fase_nama }}</b><span>🏷️ Fase</span></div>
</div>

<h3>👥 Daftar Member ({{ total_users }})</h3>
<table>
<tr><th>Invoice</th><th>Nama</th><th>Email</th><th>WA</th><th>Password</th><th>Bayar</th><th>Fase</th><th>Status</th><th>Aksi</th></tr>
{{ rows|safe }}
</table>
</div></body></html>
'''

LOGIN_ADMIN = '''
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Admin Login</title>
<style>
body{font-family:Arial;background:linear-gradient(135deg,#16a34a,#15803d);min-height:100vh;display:flex;align-items:center;justify-content:center;margin:0;padding:20px;}
.card{background:white;border-radius:20px;padding:40px;max-width:400px;width:100%;box-shadow:0 20px 60px rgba(0,0,0,.3);text-align:center;}
h2{color:#1f2937;margin:0 0 20px;}
input{width:100%;padding:14px;border:2px solid #e5e7eb;border-radius:12px;font-size:15px;box-sizing:border-box;margin-bottom:16px;}
button{width:100%;padding:14px;background:#16a34a;color:white;border:none;border-radius:12px;font-weight:bold;font-size:15px;cursor:pointer;}
.error{color:#c0392b;margin-bottom:12px;}
</style></head><body>
<div class="card"><h2>🔐 Admin Login</h2>
{% if error %}<div class="error">{{ error }}</div>{% endif %}
<form method="POST"><input type="password" name="password" placeholder="Password" required>
<button type="submit">Login</button></form></div></body></html>
'''

# ========================== ROUTES ==========================
@app.route('/')
def home():
    h = get_harga()
    coret = ''
    if h['is_discount']:
        coret = f'<span class="price-coret">Rp {h["harga_coret_display"]}</span>'
    return render_template_string(LANDING,
        fase_nama=h['fase_nama'],
        harga_display=h['harga_display'],
        sisa_slot=h['sisa_slot'],
        coret_html=coret,
        error=request.args.get('error'),
        success=request.args.get('success'),
        login_error=request.args.get('login_error')
    )

@app.route('/daftar', methods=['POST'])
def daftar():
    try:
        nama = (request.form.get('nama') or '').strip()
        email = (request.form.get('email') or '').strip()
        whatsapp = (request.form.get('whatsapp') or '').strip()
        password = request.form.get('password') or ''

        if len(nama) < 3:
            return redirect('/?error=' + 'Nama minimal 3 karakter#memberArea')
        if '@' not in email or '.' not in email:
            return redirect('/?error=' + 'Email tidak valid#memberArea')
        wa_clean = ''.join(filter(str.isdigit, whatsapp))
        if wa_clean.startswith('0'): wa_clean = '62' + wa_clean[1:]
        if not wa_clean.startswith('62'): wa_clean = '62' + wa_clean
        if len(wa_clean) < 10:
            return redirect('/?error=' + 'Nomor WhatsApp tidak valid#memberArea')
        if len(password) < 6:
            return redirect('/?error=' + 'Password minimal 6 karakter#memberArea')

        users = load_users()
        if any(u['email'].lower() == email.lower() for u in users):
            return redirect('/?error=' + 'Email sudah terdaftar#memberArea')

        h = get_harga()
        invoice = gen_invoice()

        users.append({
            'nama': nama, 'email': email, 'whatsapp': wa_clean, 'password': password,
            'invoice': invoice, 'harga': h['harga'], 'harga_display': h['harga_display'],
            'fase_nama': h['fase_nama'], 'fase_number': h['fase_number'],
            'status': 'pending_payment', 'registered_at': datetime.now().isoformat()
        })
        save_users(users)

        try:
            send_email(email, f"🧾 Invoice {invoice} - {STORE_NAME}",
                       invoice_email(nama, email, wa_clean, invoice, h))
            send_email(EMAIL_SENDER, f"🔔 Pendaftaran Baru - {nama}",
                       f"<p>User baru: <b>{nama}</b><br>Email: {email}<br>WA: {wa_clean}<br>Invoice: {invoice}</p>")
        except Exception as e:
            print(f"Email err: {e}")

        success_msg = f"✅ <b>Pendaftaran berhasil!</b><br>📧 Invoice <b>{invoice}</b> sudah dikirim ke <b>{email}</b>.<br>💰 Total: <b>Rp {h['harga_display']}</b> ({h['fase_nama']})<br><br><a href='https://wa.me/{WHATSAPP_ADMIN}?text=Halo%20admin%2C%20saya%20sudah%20daftar.%20Invoice%3A%20{invoice}' target='_blank' style='background:#1B8A3F;color:white;padding:8px 16px;border-radius:8px;text-decoration:none;font-weight:700;'>📱 Konfirmasi via WhatsApp</a>"
        return redirect('/?success=' + success_msg + '#memberArea')
    except Exception as e:
        return redirect('/?error=' + f'Server error: {str(e)}#memberArea')

@app.route('/masuk', methods=['POST'])
def masuk():
    try:
        nama = (request.form.get('nama') or '').strip()
        password = request.form.get('password') or ''

        users = load_users()
        found = next((u for u in users if u['nama'].lower() == nama.lower() and u['password'] == password), None)

        if not found:
            return redirect('/?login_error=' + 'Nama atau password salah!#memberArea')
        if found.get('status') != 'paid':
            return redirect('/?login_error=' + 'Akun belum aktif. Selesaikan pembayaran dulu.#memberArea')

        return redirect(f"https://memberarea.kelasyoutube.my.id/?user={found['nama']}&pass={password}")
    except Exception as e:
        return redirect('/?login_error=' + f'Server error: {str(e)}#memberArea')

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['password'] == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect('/admin')
        return render_template_string(LOGIN_ADMIN, error='Password salah!')
    return render_template_string(LOGIN_ADMIN, error=None)

@app.route('/admin-logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect('/admin-login')

@app.route('/admin')
@login_required
def admin():
    users = load_users()
    h = get_harga()

    rows = ''
    for u in users:
        status = u.get('status', 'pending_payment')
        if status == 'paid':
            badge = "<span style='background:#16a34a;color:white;padding:4px 10px;border-radius:10px;font-size:11px;'>✅ PAID</span>"
            aksi = "<span style='color:#999;'>—</span>"
        else:
            badge = "<span style='background:#f59e0b;color:white;padding:4px 10px;border-radius:10px;font-size:11px;'>⏳ PENDING</span>"
            aksi = f"<a href='/admin/confirm/{u.get('invoice')}' style='background:#16a34a;color:white;padding:4px 10px;border-radius:8px;text-decoration:none;font-size:11px;' onclick=\"return confirm('Konfirmasi {u.get('nama')}?')\">✅ Konfirmasi</a>"

        rows += f"<tr><td style='font-family:monospace;font-size:11px;'>{u.get('invoice','-')}</td><td>{u['nama']}</td><td style='font-size:11px;'>{u['email']}</td><td>{u.get('whatsapp','-')}</td><td style='font-family:monospace;color:#c0392b;font-weight:bold;'>{u.get('password','-')}</td><td><b>Rp {u.get('harga_display','-')}</b></td><td style='font-size:11px;'>{u.get('fase_nama','-')}</td><td>{badge}</td><td>{aksi}</td></tr>"

    if not rows:
        rows = '<tr><td colspan="9" style="text-align:center;padding:40px;color:#999;">Belum ada user</td></tr>'

    return render_template_string(ADMIN_PAGE,
        store=STORE_NAME, rows=rows,
        total_paid=h['total_paid'], total_pending=h['total_pending'],
        harga_display=h['harga_display'], fase_nama=h['fase_nama'],
        total_users=len(users)
    )

@app.route('/admin/confirm/<invoice>')
@login_required
def admin_confirm(invoice):
    users = load_users()
    found = None
    for u in users:
        if u.get('invoice') == invoice:
            u['status'] = 'paid'
            u['paid_at'] = datetime.now().isoformat()
            found = u
            break
    if not found:
        return f"Invoice tidak ditemukan. <a href='/admin'>Kembali</a>"
    save_users(users)
    try:
        send_email(found['email'], f"🎉 Akun Aktif - {STORE_NAME}",
                   aktivasi_email(found['nama'], found['password']))
    except: pass
    return redirect('/admin')

@app.route('/test-email')
def test_email():
    r = send_email(EMAIL_SENDER, "✅ Test",
                   "<h2>✅ EMAIL BERFUNGSI!</h2><p>App password benar.</p>")
    return "✅ EMAIL OK" if r else "❌ EMAIL GAGAL"

@app.route('/api/reset-users')
def api_reset():
    save_users([])
    return "✅ Semua user dihapus. <a href='/admin'>Admin</a>"

@app.route('/api/harga')
def api_harga():
    from flask import jsonify
    return jsonify(get_harga())

# Vercel handler
app = app
handler = app

if __name__ == '__main__':
    app.run()
