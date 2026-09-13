from flask import Flask, request, render_template_string, redirect, session, jsonify
from datetime import datetime
import os, json, requests, smtplib
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

products = {
    'name': 'Cuan Digital Academy',
    'price': 10000,
    'description': 'Paket Marketing Komplit',
    'payment_instructions': 'Bank Jago\n106371536422\na.n. Deny Prasetyo',
    'product_image': 'https://i.imgur.com/bOaZtCP.png'
}

QRIS_IMAGE_URL = "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjdEuaeTQp9-oYTbkTybyGb4hV23Gbdi12E9p9x3SJNlzJCfweazzWg2Tr6iSXHFXlSxi845dqwVbRZQ8CPnI63_mtQ9wNltEb_gDtJtP5GiI_YeIZLWnBVw_AZ1Glo_0RfuHBupJFra28Gf1M3idWT6l9G_edl1DNSjZ5P9DLhT5CFzwCIkG7pWGHLYSk/w398-h400/photo_2026-05-14_06-29-01.jpg"

# ========================== STORAGE ====================
USERS_FILE = '/tmp/users.json'
ORDERS_FILE = '/tmp/orders.json'

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

# ========================== ADMIN DECORATOR ====================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect('/admin-login')
        return f(*args, **kwargs)
    return wrapper

# ========================== HALAMAN UTAMA (LOGIN + DAFTAR) ========
HOME_TEMPLATE = '''
<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Akses Member Area</title>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:'Plus Jakarta Sans',sans-serif; background:#f0f4f0; padding:20px; min-height:100vh; }
.app { max-width:480px; margin:40px auto; }
.card { background:white; border-radius:24px; padding:32px; box-shadow:0 4px 12px rgba(6,40,15,0.06); }
.member-header { display:flex; align-items:center; gap:14px; margin-bottom:16px; }
.lock-badge { background:linear-gradient(135deg,#052e16,#16a34a); color:white; width:48px; height:48px; border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:20px; }
.member-header h3 { font-size:20px; font-weight:800; }
.subtitle { color:#3d523d; margin-bottom:24px; font-size:14px; }
.auth-tabs { display:flex; margin-bottom:24px; border-radius:14px; border:2px solid #dbe7db; background:#f8faf8; padding:5px; gap:5px; }
.auth-tab { flex:1; padding:13px; font-weight:800; cursor:pointer; background:transparent; color:#7a8f7a; border:none; border-radius:10px; font-family:inherit; font-size:14px; transition:0.2s; }
.auth-tab.active { background:linear-gradient(135deg,#052e16,#16a34a); color:white; }
.auth-form { display:none; }
.auth-form.active { display:block; }
.input-group { margin-bottom:18px; }
.input-group label { display:block; font-weight:800; font-size:13px; margin-bottom:8px; color:#0a1a0f; }
.input-group input { width:100%; padding:14px 18px; border:2px solid #dbe7db; border-radius:12px; font-size:15px; font-family:inherit; background:#f8faf8; transition:0.2s; }
.input-group input:focus { outline:none; border-color:#16a34a; background:white; }
.btn-login, .btn-register { width:100%; padding:16px; border-radius:14px; font-weight:800; font-size:15px; cursor:pointer; border:none; color:white; font-family:inherit; transition:0.2s; }
.btn-login { background:linear-gradient(135deg,#052e16,#16a34a); }
.btn-register { background:linear-gradient(135deg,#1e3a8a,#2563eb); }
.btn-login:hover, .btn-register:hover { transform:translateY(-2px); box-shadow:0 8px 20px rgba(6,40,15,0.15); }
.btn-login:disabled, .btn-register:disabled { opacity:0.6; cursor:not-allowed; transform:none; }
.auth-error { color:#dc2626; text-align:center; margin-top:14px; font-weight:700; font-size:13px; display:none; padding:14px; background:#fef2f2; border-radius:12px; border:1.5px solid #fca5a5; }
.auth-error.show { display:block; }
.auth-success { color:#15803d; text-align:center; margin-top:14px; font-weight:700; font-size:13px; display:none; padding:14px; background:#ecfdf3; border-radius:12px; border:1.5px solid #a7f3c4; }
.auth-success.show { display:block; }
.footer { text-align:center; font-size:12px; color:#7a8f7a; padding:24px; }
.admin-link { display:block; text-align:center; margin-top:16px; font-size:12px; color:#9ca3af; text-decoration:none; }
.admin-link:hover { color:#16a34a; }
</style>
</head>
<body>
<div class="app">
    <div class="card">
        <div class="member-header">
            <div class="lock-badge">🔐</div>
            <h3>Akses Member Area</h3>
        </div>
        <p class="subtitle">Login atau daftar untuk mengakses semua modul.</p>

        <div class="auth-tabs">
            <button class="auth-tab active" data-tab="login">Login</button>
            <button class="auth-tab" data-tab="register">Daftar</button>
        </div>

        <div class="auth-form active" id="formLogin">
            <div class="input-group">
                <label>Email</label>
                <input type="email" id="loginEmail" placeholder="email@example.com">
            </div>
            <div class="input-group">
                <label>Password</label>
                <input type="password" id="loginPass" placeholder="Masukkan password">
            </div>
            <button id="btnLoginMember" class="btn-login">Masuk ke Kelas</button>
            <div id="loginError" class="auth-error"></div>
        </div>

        <div class="auth-form" id="formRegister">
            <div class="input-group">
                <label>Nama Lengkap</label>
                <input type="text" id="regName" placeholder="Contoh: Andi Perkasa">
            </div>
            <div class="input-group">
                <label>Email</label>
                <input type="email" id="regEmail" placeholder="email@example.com">
            </div>
            <div class="input-group">
                <label>Password</label>
                <input type="password" id="regPass" placeholder="Minimal 6 karakter">
            </div>
            <div class="input-group">
                <label>Konfirmasi Password</label>
                <input type="password" id="regConfirm" placeholder="Ulangi password">
            </div>
            <button id="btnRegisterMember" class="btn-register">Daftar Sekarang</button>
            <div id="registerError" class="auth-error"></div>
            <div id="registerSuccess" class="auth-success"></div>
        </div>

        <a href="/admin-login" class="admin-link">🔧 Admin Login</a>
    </div>
    <div class="footer">© 2026 {{ store }}</div>
</div>

<script>
const tabs = document.querySelectorAll('.auth-tab');
const formLogin = document.getElementById('formLogin');
const formRegister = document.getElementById('formRegister');
tabs.forEach(tab => {
    tab.addEventListener('click', function() {
        tabs.forEach(t => t.classList.remove('active'));
        this.classList.add('active');
        const target = this.dataset.tab;
        formLogin.classList.toggle('active', target === 'login');
        formRegister.classList.toggle('active', target === 'register');
    });
});

document.getElementById('btnLoginMember').addEventListener('click', function() {
    const email = document.getElementById('loginEmail').value.trim();
    const pass = document.getElementById('loginPass').value.trim();
    const errBox = document.getElementById('loginError');
    errBox.classList.remove('show');
    if (!email || !pass) {
        errBox.textContent = 'Email dan password harus diisi.';
        errBox.classList.add('show');
        return;
    }
    const btn = this;
    btn.textContent = 'Memproses...';
    btn.disabled = true;
    fetch('/api/login', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({email:email, password:pass})
    })
    .then(r => r.json())
    .then(data => {
        btn.textContent = 'Masuk ke Kelas';
        btn.disabled = false;
        if (data.success) {
            window.location.href = data.redirect;
        } else {
            errBox.textContent = data.message;
            errBox.classList.add('show');
        }
    })
    .catch(err => {
        btn.textContent = 'Masuk ke Kelas';
        btn.disabled = false;
        errBox.textContent = 'Server error: ' + err.message;
        errBox.classList.add('show');
    });
});

document.getElementById('btnRegisterMember').addEventListener('click', function() {
    const nama = document.getElementById('regName').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const pass = document.getElementById('regPass').value;
    const confirm = document.getElementById('regConfirm').value;
    const errBox = document.getElementById('registerError');
    const okBox = document.getElementById('registerSuccess');
    errBox.classList.remove('show');
    okBox.classList.remove('show');

    if (!nama || nama.length < 3) { errBox.textContent='Nama minimal 3 karakter.'; errBox.classList.add('show'); return; }
    if (!email || !email.includes('@')) { errBox.textContent='Email tidak valid.'; errBox.classList.add('show'); return; }
    if (pass.length < 6) { errBox.textContent='Password minimal 6 karakter.'; errBox.classList.add('show'); return; }
    if (pass !== confirm) { errBox.textContent='Password tidak cocok.'; errBox.classList.add('show'); return; }

    const btn = this;
    btn.textContent = 'Mendaftar...';
    btn.disabled = true;
    fetch('/api/register', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({nama:nama, email:email, password:pass})
    })
    .then(r => r.json())
    .then(data => {
        btn.textContent = 'Daftar Sekarang';
        btn.disabled = false;
        if (data.success) {
            okBox.textContent = '✅ ' + data.message;
            okBox.classList.add('show');
            document.getElementById('regName').value = '';
            document.getElementById('regEmail').value = '';
            document.getElementById('regPass').value = '';
            document.getElementById('regConfirm').value = '';
            setTimeout(() => {
                document.querySelector('.auth-tab[data-tab="login"]').click();
                document.getElementById('loginEmail').value = email;
            }, 2000);
        } else {
            errBox.textContent = data.message;
            errBox.classList.add('show');
        }
    })
    .catch(err => {
        btn.textContent = 'Daftar Sekarang';
        btn.disabled = false;
        errBox.textContent = 'Server error: ' + err.message;
        errBox.classList.add('show');
    });
});
</script>
</body>
</html>
'''

# ========================== ROUTE: HALAMAN UTAMA ====================
@app.route('/')
def home():
    return render_template_string(HOME_TEMPLATE, store=STORE_NAME)

# ========================== ROUTE: REGISTER API ====================
@app.route('/api/register', methods=['POST', 'OPTIONS'])
def api_register():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        data = request.get_json()
        nama = (data.get('nama') or '').strip()
        email = (data.get('email') or '').strip()
        password = data.get('password') or ''

        if len(nama) < 3:
            return jsonify({'success': False, 'message': 'Nama minimal 3 karakter'}), 400
        if '@' not in email or '.' not in email:
            return jsonify({'success': False, 'message': 'Email tidak valid'}), 400
        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Password minimal 6 karakter'}), 400

        users = load_json(USERS_FILE)
        if any(u['email'].lower() == email.lower() for u in users):
            return jsonify({'success': False, 'message': 'Email sudah terdaftar'}), 400

        new_user = {
            'nama': nama, 'email': email, 'password': password,
            'registered_at': datetime.now().isoformat(), 'status': 'active'
        }
        users.append(new_user)
        save_json(USERS_FILE, users)

        admin_msg = (
            f"🎉 *PENDAFTARAN BARU!*\n\n"
            f"👤 Nama: {nama}\n"
            f"📧 Email: {email}\n"
            f"🕐 Waktu: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
            f"👥 Total user: {len(users)}"
        )
        send_whatsapp(WHATSAPP_ADMIN, admin_msg)

        welcome_html = f"""
        <div style="font-family:Arial;max-width:500px;margin:auto;background:white;border-radius:16px;overflow:hidden;">
            <div style="background:#16a34a;padding:30px;text-align:center;color:white;">
                <h2>🎉 Selamat Datang!</h2>
            </div>
            <div style="padding:30px;">
                <p>Halo <b>{nama}</b>,</p>
                <p>Pendaftaran Anda di <b>{STORE_NAME}</b> berhasil!</p>
                <p>Silakan login untuk mengakses semua modul.</p>
                <p style="font-size:12px;color:#999;">Butuh bantuan? wa.me/{WHATSAPP_ADMIN}</p>
            </div>
        </div>
        """
        send_email(email, f"Selamat Datang di {STORE_NAME}", welcome_html)

        return jsonify({'success': True, 'message': 'Pendaftaran berhasil! Silakan login.'})

    except Exception as e:
        print(f"Register error: {e}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

# ========================== ROUTE: LOGIN API ====================
@app.route('/api/login', methods=['POST', 'OPTIONS'])
def api_login():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        data = request.get_json()
        email = (data.get('email') or '').strip()
        password = data.get('password') or ''

        if not email or not password:
            return jsonify({'success': False, 'message': 'Email dan password harus diisi'}), 400

        users = load_json(USERS_FILE)
        user = next((u for u in users if u['email'].lower() == email.lower() and u['password'] == password), None)

        if not user:
            return jsonify({'success': False, 'message': 'Email atau password salah'}), 401

        member_url = f"https://memberarea.kelasyoutube.my.id/?user={user['nama']}&email={user['email']}"
        return jsonify({'success': True, 'message': 'Login berhasil', 'redirect': member_url})

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

# ========================== ROUTE: ADMIN ====================
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
    orders = load_json(ORDERS_FILE)
    users_rows = ''.join(f"<tr><td>{u['nama']}</td><td>{u['email']}</td><td>{u.get('registered_at','-')[:10]}</td></tr>" for u in users) if users else '<tr><td colspan="3" style="text-align:center;padding:40px;color:#999;">Belum ada user</td></tr>'
    orders_rows = ''.join(f"<tr><td>{o.get('invoice','-')}</td><td>{o.get('customer_name','-')}</td><td>Rp {o.get('price','-')}</td></tr>" for o in orders) if orders else '<tr><td colspan="3" style="text-align:center;padding:40px;color:#999;">Belum ada pesanan</td></tr>'
    return f"""
    <!DOCTYPE html><html><head><title>Admin Panel</title>
    <style>
        body {{ font-family:Arial;background:#f3f4f6;padding:40px 20px; }}
        .card {{ background:white;border-radius:20px;padding:30px;max-width:900px;margin:auto; }}
        h2 {{ color:#1f2937; }}
        h3 {{ color:#374151;margin-top:30px;border-bottom:2px solid #e5e7eb;padding-bottom:10px; }}
        table {{ width:100%;border-collapse:collapse;margin-top:16px; }}
        th {{ background:#16a34a;color:white;padding:12px;text-align:left; }}
        td {{ padding:12px;border-bottom:1px solid #eee; }}
        a.logout {{ color:#dc2626;text-decoration:none;float:right;font-size:14px; }}
    </style></head><body>
    <div class="card">
        <a class="logout" href="/admin-logout">🚪 Logout</a>
        <h2>⚙️ Admin Panel</h2>
        <h3>👥 User Terdaftar ({len(users)})</h3>
        <table><tr><th>Nama</th><th>Email</th><th>Tanggal</th></tr>{users_rows}</table>
        <h3>📋 Pesanan ({len(orders)})</h3>
        <table><tr><th>Invoice</th><th>Customer</th><th>Total</th></tr>{orders_rows}</table>
    </div></body></html>
    """

# ========================== TEST WA ====================
@app.route('/test-wa')
def test_wa():
    result = send_whatsapp(WHATSAPP_ADMIN, "🧪 Test: WA dari Vercel OK!")
    return f"{'✅ WA OK' if result else '❌ WA GAGAL - Cek log Vercel'}"

if __name__ == '__main__':
    app.run(debug=True)
