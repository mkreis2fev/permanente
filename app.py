import os
import requests
from flask import Flask, Response, render_template_string

app = Flask(__name__)

# --- CONFIGURAÇÕES ---

# Link direto do VeloPlay usando sua credencial
VELO_URL = "http://fastcdn.bond:8080/get.php?username=vWRJvKkPDX&password=vWRJvKkPDX&type=m3u_plus&output=ts"

# Link de Backup (Canais que nunca caem se o VeloPlay bloquear o Railway)
BACKUP_URL = "https://raw.githubusercontent.com/Fmacedo87/m3u/main/Canais.m3u"

def get_channels_logic():
    """
    Função ultra-rápida: tenta VeloPlay em 4 segundos, se não der, pula para o Backup.
    """
    headers = {
        'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 10; TV Box Build/QP1A.190711.020)',
        'X-Requested-With': 'com.global.veloplaytv'
    }

    # TENTA VELOPLAY (TIMEOUT CURTO DE 4 SEGUNDOS)
    try:
        r = requests.get(VELO_URL, headers=headers, timeout=4)
        if r.status_code == 200 and "#EXTM3U" in r.text:
            content = r.text
            # Tenta injetar o link do EPG automaticamente
            domain = os.environ.get("RAILWAY_STATIC_URL", "veloplay-api.up.railway.app")
            if content.startswith("#EXTM3U"):
                content = content.replace("#EXTM3U", f'#EXTM3U x-tvg-url="https://{domain}/epg.xml"', 1)
            return content
    except:
        pass

    # SE FALHAR, ENTREGA O BACKUP IMEDIATAMENTE
    try:
        r_backup = requests.get(BACKUP_URL, timeout=5)
        return r_backup.text
    except:
        return "#EXTM3U\n#ERRO: Servidores temporariamente indisponiveis."

# --- ROTAS ---

@app.route('/')
def home():
    return render_template_string("""
        <body style="background:#000;color:#fff;text-align:center;padding:50px;font-family:sans-serif">
            <h1 style="color:#ffaa00">VeloPlay Cloud Engine</h1>
            <p style="color:#888">Sincronizando Canais e EPG...</p>
            <div style="margin-top:30px">
                <a href="/playlist.m3u" style="background:#ffaa00;color:#000;padding:15px 30px;text-decoration:none;font-weight:bold;border-radius:5px">ABRIR LISTA M3U</a>
            </div>
            <p style="margin-top:20px;font-size:12px;color:#444">Railway Engine v7.0 (Fast Response)</p>
        </body>
    """)

@app.route('/playlist.m3u')
def playlist():
    return Response(get_channels_logic(), mimetype='text/plain')

@app.route('/epg.xml')
def epg():
    # EPG público para carregar mais rápido no player
    try:
        r = requests.get("https://iptv-org.github.io/epg/guides/br/mi.tv.epg.xml", timeout=5)
        return Response(r.text, mimetype='application/xml')
    except:
        return '<?xml version="1.0" encoding="UTF-8"?><tv></tv>'

if __name__ == '__main__':
    # Railway configura a porta automaticamente
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
