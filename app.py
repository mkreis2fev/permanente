import os
import requests
from flask import Flask, Response, render_template_string

app = Flask(__name__)

# --- CONFIGURAÇÕES DO VELOPLAY ---

# Servidores Oficiais Extraídos do App
VELO_SERVERS = [
    "http://fastcdn.bond:8080", 
    "http://vodcast.sbs:8080",
    "http://fastcdn.bond"
]

# Sua credencial exata (vWRJvKkPDX)
CREDENTIAL = "vWRJvKkPDX"

# Fontes de Backup (Canais que nunca caem: Globo, SBT, etc.)
BACKUP_SOURCES = [
    "https://raw.githubusercontent.com/Fmacedo87/m3u/main/Canais.m3u",
    "https://iptv-org.github.io/iptv/countries/br.m3u"
]

# --- LÓGICA DE CAPTURA ---

def get_full_list():
    """
    Tenta capturar a grade premium do Velo Play. 
    Se falhar, une com fontes de backup para garantir canais ativos.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; TV Box Build/QP1A.190711.020)',
        'Accept': '*/*',
        'Connection': 'Keep-Alive'
    }
    
    # 1. TENTA CAPTURAR DO SERVIDOR PRIVADO (Canais HBO, Discovery, etc.)
    for base in VELO_SERVERS:
        # Tenta o formato padrão Xtream Codes
        url = f"{base}/get.php?username={CREDENTIAL}&password={CREDENTIAL}&type=m3u_plus&output=ts"
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200 and "#EXTM3U" in response.text:
                content = response.text
                
                # Injeta o link do EPG automaticamente no topo
                domain = os.environ.get("RAILWAY_STATIC_URL", "veloplay-api.up.railway.app")
                if content.startswith("#EXTM3U"):
                    content = content.replace("#EXTM3U", f'#EXTM3U x-tvg-url="https://{domain}/epg.xml"', 1)
                return content
        except:
            continue

    # 2. SE O PRIVADO FALHAR, MONTA UMA LISTA COM AS FONTES DE BACKUP
    combined_m3u = "#EXTM3U\n# MODO BACKUP ATIVO: Servidor VeloPlay instavel\n"
    for url in BACKUP_SOURCES:
        try:
            r = requests.get(url, headers=headers, timeout=8)
            if r.status_code == 200:
                lines = r.text.splitlines()
                for line in lines:
                    if not line.startswith("#EXTM3U"):
                        combined_m3u += line + "\n"
        except:
            continue
            
    return combined_m3u

# --- ROTAS DO SERVIDOR ---

@app.route('/')
def home():
    return render_template_string("""
        <body style="background:#0a0a0a;color:#fff;text-align:center;padding:50px;font-family:sans-serif">
            <h1 style="color:#ffaa00;font-size:3em">VeloPlay Cloud Engine</h1>
            <p style="color:#888;font-size:1.2em">Sincronizado com o código: <code style="color:#fff">vWRJvKkPDX</code></p>
            <hr style="border:0;height:1px;background:#333;margin:30px">
            
            <div style="background:#111;padding:40px;border-radius:20px;display:inline-block;border:1px solid #222">
                <p style="margin-bottom:25px;color:#0f0">Status: Servidor de Canais Ativo</p>
                <a href="/playlist.m3u" style="display:block;background:#ffaa00;color:#000;padding:20px 50px;text-decoration:none;font-weight:bold;border-radius:8px;margin-bottom:15px;font-size:1.1em">ABRIR LISTA M3U</a>
                <a href="/epg.xml" style="color:#ffaa00;text-decoration:none;font-size:1em">Guia de Programação (EPG XML)</a>
            </div>
            
            <p style="margin-top:50px;font-size:11px;color:#444">Railway Deployment v6.0 - Unlimited Mode Active</p>
        </body>
    """)

@app.route('/playlist.m3u')
def playlist():
    return Response(get_full_list(), mimetype='text/plain')

@app.route('/epg.xml')
def epg():
    # Tenta puxar o EPG original do VeloPlay ou usa um backup público
    epg_url = f"{VELO_SERVERS[0]}/xmltv.php?username={CREDENTIAL}&password={CREDENTIAL}"
    try:
        r = requests.get(epg_url, timeout=15)
        if r.status_code == 200:
            return Response(r.text, mimetype='application/xml')
        # Backup do EPG
        r_backup = requests.get("https://iptv-org.github.io/epg/guides/br/mi.tv.epg.xml", timeout=10)
        return Response(r_backup.text, mimetype='application/xml')
    except:
        return '<?xml version="1.0" encoding="UTF-8"?><tv></tv>'

if __name__ == '__main__':
    # O Railway usa a variável de ambiente PORT para rodar o serviço
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
