from flask import Flask, Blueprint, request, redirect, session, render_template_string
import uuid, json, os, time

app = Flask(__name__)
app.secret_key = "secure123"

BASE = "/vless-panel"
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.json")
XRAY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xray.json")

USERNAME = "admin"
PASSWORD = "admin"

DOMAIN = "anugerah-ternak-sejagad.xyz"

bp = Blueprint("panel", __name__, url_prefix=BASE)

def load():
    if not os.path.exists(DB):
        return []
    with open(DB, "r") as f:
        return json.load(f)

def save(data):
    with open(DB, "w") as f:
        json.dump(data, f, indent=2)

def generate_link(user):
    path = user.get("path", f"/{user['id'][:6]}")
    return f"vless://{user['id']}@{DOMAIN}:443?type=ws&path={path}&security=tls"

def sync_xray(users):
    inbounds = []
    port = 10001
    now = time.time()

    for u in users:
        path = f"/{u['id'][:6]}"
        u["path"] = path

        if u["expired"] >= now:
            u["link"] = generate_link(u)
            inbounds.append({
                "port": port,
                "protocol": "vless",
                "settings": {"clients": [{"id": u["id"]}]},
                "streamSettings": {
                    "network": "ws",
                    "wsSettings": {
                        "path": path,
                        "headers": {"Host": DOMAIN}
                    }
                }
            })
            port += 1
        else:
            u["link"] = u.get("link", generate_link(u))

    config = {
        "log": {"loglevel": "warning"},
        "inbounds": inbounds,
        "outbounds": [{"protocol": "freedom"}],
        "dns": {"servers": ["1.1.1.1", "1.0.0.1", "8.8.8.8"]}
    }

    with open(XRAY, "w") as f:
        json.dump(config, f, indent=2)

    os.system("pkill -f 'xray run' 2>/dev/null; sleep 1; xray run -c " + XRAY + " &>/dev/null &")

@bp.route("/", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        if request.form.get("user") == USERNAME and request.form.get("pw") == PASSWORD:
            session["login"] = True
            return redirect(BASE + "/panel")
        error = "<p style='color:red'>❌ Username atau password salah!</p>"

    return f"""<!DOCTYPE html>
    <html>
    <head><title>VLESS Panel Login</title></head>
    <body style='background:black;color:#0ff;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh;margin:0'>
    <div style='border:1px solid #0ff;padding:30px;min-width:300px'>
    <h2 style='text-align:center'>🔐 VLESS PANEL</h2>
    {error}
    <form method=post>
    <p>Username:<br><input name=user style='background:#111;color:#0ff;border:1px solid #0ff;padding:5px;width:100%;box-sizing:border-box'></p>
    <p>Password:<br><input name=pw type=password style='background:#111;color:#0ff;border:1px solid #0ff;padding:5px;width:100%;box-sizing:border-box'></p>
    <button style='width:100%;background:#0ff;color:black;padding:8px;border:none;cursor:pointer;font-weight:bold;font-family:monospace'>LOGIN</button>
    </form>
    </div>
    </body>
    </html>"""

@bp.route("/panel")
def panel():
    if not session.get("login"):
        return redirect(BASE + "/")

    users = load()
    now = time.time()

    for u in users:
        u["expired_str"] = time.strftime("%Y-%m-%d %H:%M", time.localtime(u["expired"]))
        u.setdefault("link", generate_link(u))

    html = """<!DOCTYPE html>
    <html>
    <head><title>VLESS Panel</title></head>
    <body style='background:black;color:#0ff;font-family:monospace;padding:20px'>
    <div style='display:flex;justify-content:space-between;align-items:center'>
      <h2>💰 VLESS PANEL</h2>
      <a href='{{ base }}/logout' style='color:red;text-decoration:none'>🚪 Logout</a>
    </div>

    <h3>➕ Tambah User Baru</h3>
    <form method=post action='{{ base }}/create' style='margin-bottom:20px'>
    Nama: <input name=nama required style='background:#111;color:#0ff;border:1px solid #0ff;padding:4px'>
    &nbsp;
    Durasi (hari): <input name=days value=1 type=number min=1 style='background:#111;color:#0ff;border:1px solid #0ff;padding:4px;width:60px'>
    &nbsp;
    <button style='background:#0ff;color:black;padding:5px 15px;border:none;cursor:pointer;font-weight:bold;font-family:monospace'>+ CREATE</button>
    </form>

    <h3>📋 Daftar User ({{ users|length }} total)</h3>
    <table border=1 style='border-collapse:collapse;width:100%;border-color:#0ff'>
    <tr style='background:#003333'>
      <th style='padding:8px'>Nama</th>
      <th style='padding:8px'>Status</th>
      <th style='padding:8px'>Expired</th>
      <th style='padding:8px'>Link VLESS</th>
      <th style='padding:8px'>Hapus</th>
    </tr>

    {% for u in users %}
    <tr>
      <td style='padding:6px'>{{ u.nama }}</td>
      <td style='padding:6px;color:{% if u.expired > now %}lime{% else %}red{% endif %}'>
        {% if u.expired > now %}✅ AKTIF{% else %}❌ EXPIRED{% endif %}
      </td>
      <td style='padding:6px'>{{ u.expired_str }}</td>
      <td style='padding:6px;font-size:11px;max-width:400px;word-break:break-all'>
        {{ u.link if u.link else '-' }}
      </td>
      <td style='padding:6px;text-align:center'>
        <a href='{{ base }}/delete/{{ u.id }}' style='color:red;text-decoration:none'
           onclick="return confirm('Hapus user {{ u.nama }}?')">❌</a>
      </td>
    </tr>
    {% endfor %}

    {% if not users %}
    <tr><td colspan=5 style='text-align:center;padding:20px;color:#555'>Belum ada user. Tambah user baru di atas.</td></tr>
    {% endif %}

    </table>
    </body>
    </html>"""

    return render_template_string(html, users=users, now=now, base=BASE)

@bp.route("/create", methods=["POST"])
def create():
    if not session.get("login"):
        return redirect(BASE + "/")

    nama = request.form.get("nama", "").strip()
    if not nama:
        return redirect(BASE + "/panel")

    days = max(1, int(request.form.get("days", 1)))
    uid = str(uuid.uuid4())
    expired = int(time.time()) + (days * 86400)

    users = load()
    users.append({
        "id": uid,
        "nama": nama,
        "expired": expired,
        "path": f"/{uid[:6]}",
        "link": ""
    })

    sync_xray(users)
    save(users)

    return redirect(BASE + "/panel")

@bp.route("/delete/<uid>")
def delete(uid):
    if not session.get("login"):
        return redirect(BASE + "/")

    users = load()
    users = [u for u in users if u["id"] != uid]

    sync_xray(users)
    save(users)

    return redirect(BASE + "/panel")

@bp.route("/logout")
def logout():
    session.clear()
    return redirect(BASE + "/")

app.register_blueprint(bp)

@app.route("/")
def root_redirect():
    return redirect(BASE + "/")

if __name__ == "__main__":
    if not os.path.exists(DB):
        save([])
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
