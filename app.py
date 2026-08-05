import os
import requests
from flask import Flask, Response, render_template_string

app = Flask(__name__)

# --- CONFIGURAÇÕES ---
# Link direto do VeloPlay usando sua credencial
VELO_URL = "http://fastcdn.bond:8080/get.php?username=vWRJvKkPDX&password=vWRJvKkPDX&type=m3u_plus&output=ts"

# Link de Backup (Canais que entram se o VeloPlay bloquear o acesso do servidor)
BACKUP_URL = "https://raw.githubusercontent.com/Fmacedo87/m3u/main/Canais.m3u"

def get_channels():
    """
    Tenta buscar no VeloPlay por 5 segundos. 
    Se falhar, retorna a lista de backup imediatamente.
    """
    headers = {
        'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 10; TV Box Build/QP1A.190711.020)',
        'X-Requested-With': 'com.global.veloplaytv'
    }
    
    # 1. TENTA O VELOPLAY
    try:
        r = requests.get(VELO_URL, headers=headers, timeout=5)
        if r.status_code == 200 and "#EXTM3U" in r.text:
            content = r.text
            # Tenta injetar o link do EPG automaticamente no topo da lista
            host = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "veloplay-api.up.railway.app")
            if content.startswith("#EXTM3U"):
                content = content.replace("#EXTM3U", f'#EXTM3U x-tvg-url="https://{host}/epg.xml"', 1)
            return content
    except:
        pass

    # 2. SE FALHAR, RETORNA O BACKUP
    try:
        r_backup = requests.get(BACKUP_URL, timeout=10)
        return r_backup.text
    except:
        return "#EXTM3U\n#ERRO: Servidores temporariamente indisponiveis."

# --- ROTAS DO SERVIDOR ---

@app.route('/')
def home():
    """Página inicial simples para evitar erro 404 e passar no teste do Railway."""
    return render_template_string("""
        <body style="background:#000;color:#fff;text-align:center;padding:50px;font-family:sans-serif">
            <h1 style="color:#ffaa00">VeloPlay Cloud Engine</h1>
            <p style="color:#888">Servidor de Canais Ativo no Railway</p>
            <hr style="border:0;height:1px;background:#333;margin:30px">
            <div style="background:#111;padding:30px;border-radius:15px;display:inline-block;border:1px solid #222">
                <p style="margin-bottom:20px">Sua lista M3U com canais Premium está pronta:</p>
                <a href="/playlist.m3u" style="display:block;background:#ffaa00;color:#000;padding:15px 40px;text-decoration:none;font-weight:bold;border-radius:5px;margin-bottom:10px">ABRIR LISTA M3U</a>
                <a href="/epg.xml" style="color:#ffaa00;text-decoration:none;font-size:0.9em">Guia de Programação (EPG XML)</a>
            </div>
            <p style="margin-top:40px;font-size:12px;color:#444">Railway Engine v7.0 (Fast Response)</p>
        </body>
    """)

@app.route('/playlist.m3u')
def playlist():
    """Rota que entrega a lista de canais."""
    return Response(get_channels(), mimetype='text/plain')

@app.route('/epg.xml')
def epg():
    """Rota que entrega o Guia de Programação."""
    try:
        # Busca EPG brasileiro público (estável e rápido)
        r = requests.get("https://iptv-org.github.io/epg/guides/br/mi.tv.epg.xml", timeout=10)
        return Response(r.text, mimetype='application/xml')
    except:
        return '<?xml version="1.0" encoding="UTF-8"?><tv></tv>'

if __name__ == '__main__':
    # O Railway define a porta automaticamente na variável PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
