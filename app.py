import os
import requests
from flask import Flask, Response, render_template_string

app = Flask(__name__)

# CONFIGURAÇÕES DE CONEXÃO
# Testando diferentes portas e protocolos do VeloPlay
SERVERS = [
    "http://fastcdn.bond:8080",
    "http://fastcdn.bond:80",
    "http://vodcast.sbs:8080",
    "http://172.67.173.189:8080" # IP direto do fastcdn (se o DNS estiver bloqueado)
]

CREDENTIAL = "vWRJvKkPDX"

def get_veloplay_channels():
    # Headers EXATOS que o app VeloPlay/UniTV usa
    headers = {
        'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 10; TV Box Build/QP1A.190711.020)',
        'X-Requested-With': 'com.global.veloplaytv',
        'Accept-Encoding': 'gzip',
        'Connection': 'Keep-Alive'
    }
    
    # 1. TENTA O MÉTODO XTREAM CODES PADRÃO (Em várias portas)
    for base in SERVERS:
        # Tentativa A: Lista M3U Plus
        url_a = f"{base}/get.php?username={CREDENTIAL}&password={CREDENTIAL}&type=m3u_plus&output=ts"
        # Tentativa B: player_api (JSON convertido para M3U)
        url_b = f"{base}/player_api.php?username={CREDENTIAL}&password={CREDENTIAL}"
        
        for url in [url_a, url_b]:
            try:
                response = requests.get(url, headers=headers, timeout=6, verify=False)
                if response.status_code == 200 and "#EXTM3U" in response.text:
                    return response.text
            except:
                continue

    return None

def get_backup_list():
    # Fontes de backup para nao ficar sem nada
    url = "https://raw.githubusercontent.com/Fmacedo87/m3u/main/Canais.m3u"
    try:
        r = requests.get(url, timeout=10)
        return r.text
    except:
        return "#EXTM3U\n#ERRO: Servidores Offline"

@app.route('/playlist.m3u')
def playlist():
    # Tenta o VeloPlay primeiro
    content = get_veloplay_channels()
    
    if content:
        # Se funcionou, injeta o EPG e retorna
        domain = os.environ.get("RAILWAY_STATIC_URL", "veloplay-api.up.railway.app")
        if content.startswith("#EXTM3U"):
            content = content.replace("#EXTM3U", f'#EXTM3U x-tvg-url="https://{domain}/epg.xml"', 1)
        return Response(content, mimetype='text/plain')
    else:
        # Se falhou, retorna o backup mas avisa no topo
        backup = get_backup_list()
        return Response(f"#EXTM3U\n# AVISO: VeloPlay Bloqueou o Railway. Usando Backup.\n{backup}", mimetype='text/plain')

@app.route('/')
def home():
    return render_template_string("""
        <body style="background:#000;color:#fff;text-align:center;padding:50px;font-family:sans-serif">
            <h1 style="color:#ffaa00">VeloPlay Multi-Port API</h1>
            <p>Testando portas 80, 8080 e IPs diretos...</p>
            <div style="margin-top:30px">
                <a href="/playlist.m3u" style="background:#ffaa00;color:#000;padding:15px 30px;text-decoration:none;font-weight:bold;border-radius:5px">ABRIR LISTA M3U</a>
            </div>
        </body>
    """)

@app.route('/epg.xml')
def epg():
    # Tenta o EPG do VeloPlay, senao usa o publico
    try:
        r = requests.get(f"{SERVERS[0]}/xmltv.php?username={CREDENTIAL}&password={CREDENTIAL}", timeout=10)
        if r.status_code == 200: return Response(r.text, mimetype='application/xml')
    except: pass
    r = requests.get("https://iptv-org.github.io/epg/guides/br/mi.tv.epg.xml", timeout=10)
    return Response(r.text, mimetype='application/xml')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
