import os
import requests
from flask import Flask, Response, render_template_string

app = Flask(__name__)

# Fontes Massivas (Públicas e de Repositórios Grandes)
SOURCES = [
    "https://iptv-org.github.io/iptv/countries/br.m3u",
    "https://iptv-org.github.io/iptv/countries/pt.m3u",
    "https://raw.githubusercontent.com/Fmacedo87/m3u/main/Canais.m3u", # Exemplo de lista brasileira mantida
    "https://iptv-org.github.io/iptv/categories/movies.m3u",
    "https://iptv-org.github.io/iptv/categories/sports.m3u",
    "https://iptv-org.github.io/iptv/categories/news.m3u",
    # ADICIONE AQUI O SEU LINK PRIVADO (CAPTURADO DO APP) SE TIVER
]

EPG_URL = "https://iptv-org.github.io/epg/guides/br/mi.tv.epg.xml"

def get_channels():
    combined_m3u = "#EXTM3U"
    domain = os.environ.get("RAILWAY_STATIC_URL", "seu-app.up.railway.app")
    combined_m3u += f' x-tvg-url="https://{domain}/epg.xml"\n'

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for url in SOURCES:
        try:
            # Algumas listas exigem verificação SSL desligada para funcionar
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            if response.status_code == 200:
                lines = response.text.splitlines()
                for line in lines:
                    if not line.startswith("#EXTM3U"):
                        combined_m3u += line + "\n"
        except:
            continue

    return combined_m3u

@app.route('/')
def index():
    return render_template_string("""
        <body style="background:#000;color:#fff;text-align:center;padding:50px;font-family:sans-serif">
            <h1 style="color:#ffaa00">VeloPlay Cloud - API Ativa</h1>
            <p>Sincronizando canais e EPG em tempo real...</p>
            <div style="margin:30px">
                <a href="/playlist.m3u" style="background:#ffaa00;color:#000;padding:15px;text-decoration:none;font-weight:bold;border-radius:5px">LISTA M3U COMPLETA</a>
            </div>
            <p style="font-size:12px;color:#666">Railway Deployment v2.0</p>
        </body>
    """)

@app.route('/playlist.m3u')
def playlist():
    return Response(get_channels(), mimetype='text/plain')

@app.route('/epg.xml')
def epg():
    try:
        r = requests.get(EPG_URL, timeout=20)
        return Response(r.text, mimetype='application/xml')
    except:
        return '<?xml version="1.0" encoding="UTF-8"?><tv></tv>'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
