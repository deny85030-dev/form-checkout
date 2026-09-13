from flask import Flask, request, jsonify, session, redirect
from datetime import datetime
import os, json, requests, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import wraps
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = 'morahshop-secret-key-2026'

# CORS — supaya www.kelasyoutube.my.id bisa akses Vercel
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# ========================== KONFIGURASI ====================
STORE_NAME = 'Formula YouTube Monet'
WHATSAPP_ADMIN = '6285138718594'
EMAIL_SENDER = 'morahshop@gmail.com'
EMAIL_PASSWORD = 'ewsv nupx pvem olmq'
FONNTE_API_KEY = 'aM5d4QEx2uEV2bjtt3ta3'
ADMIN_PASSWORD = 'admin123'

USERS_FILE = '/tmp/users.json'

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

@app.route('/')
def home():
    return "Server aktif. Notif pendaftaran dari www.kelasyoutube.my.id"

# ========================== API REGISTER ====================
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
            </div>
        </div>
        """
        send_email(email, f"Selamat Datang di {STORE_NAME}", welcome_html)

        return jsonify({'success': True, 'message': 'Pendaftaran berhasil! Silakan login.'})

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
    users_rows = ''.join(f"<tr><td>{u['nama']}</td><td>{u['email']}</td><td>{u.get('registered_at','-')[:10]}</td></tr>" for u in users) if users else '<tr><td colspan="3" style="text-align:center;padding:40px;color:#999;">Belum ada user</td></tr>'
    return f"""
    <!DOCTYPE html><html><head><title>Admin Panel</title>
    <style>
        body {{ font-family:Arial;background:#f3f4f6;padding:40px 20px; }}
        .card {{ background:white;border-radius:20px;padding:30px;max-width:900px;margin:auto; }}
        h2 {{ color:#1f2937; }}
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
    </div></body></html>
    """

@app.route('/test-wa')
def test_wa():
    result = send_whatsapp(WHATSAPP_ADMIN, "🧪 Test: WA dari Vercel OK!")
    return f"{'✅ WA OK' if result else '❌ WA GAGAL'}"

if __name__ == '__main__':
    app.run(debug=True)
