import os
import requests
import re
from flask import Flask, Response, render_template_string

app = Flask(__name__)

# Lista de fontes para capturar o máximo de canais possível
SOURCES = [
    "https://iptv-org.github.io/iptv/countries/br.m3u",          # Brasil (Geral)
    "https://iptv-org.github.io/iptv/categories/movies.m3u",    # Filmes
    "https://iptv-org.github.io/iptv/categories/sports.m3u",    # Esportes
    "https://iptv-org.github.io/iptv/categories/animation.m3u"  # Desenhos/Kids
]

EPG_URL = "https://iptv-org.github.io/epg/guides/br/mi.tv.epg.xml"

def get_channels():
    combined_m3u = "#EXTM3U"
    # Adiciona o link do EPG no cabeçalho
    domain = os.environ.get("RAILWAY_STATIC_URL", "localhost:5000")
    combined_m3u += f' x-tvg-url="https://{domain}/epg.xml"\n'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for url in SOURCES:
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                # Remove o cabeçalho #EXTM3U de cada lista para não repetir
                lines = response.text.splitlines()
                for line in lines:
                    if not line.startswith("#EXTM3U"):
                        combined_m3u += line + "\n"
        except Exception as e:
            print(f"Erro ao capturar {url}: {e}")

    return combined_m3u

def fetch_epg():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(EPG_URL, headers=headers, timeout=20)
        return response.text if response.status_code == 200 else '<?xml version="1.0" encoding="UTF-8"?><tv></tv>'
    except:
        return '<?xml version="1.0" encoding="UTF-8"?><tv></tv>'

@app.route('/')
def index():
    return render_template_string("""
        <body style="background:#121212;color:white;text-align:center;padding:50px;font-family:sans-serif">
            <h1 style="color:#ffaa00">Veloplay TV - Super Scraper</h1>
            <p>Capturando de múltiplas fontes...</p>
            <hr style="border:0;height:1px;background:#333;margin:30px">
            <a href="/playlist.m3u" style="display:inline-block;background:#ffaa00;color:black;padding:15px;text-decoration:none;border-radius:5px;font-weight:bold;margin:10px">LINK DA LISTA COMPLETA</a>
            <a href="/epg.xml" style="display:inline-block;background:#444;color:white;padding:15px;text-decoration:none;border-radius:5px;font-weight:bold;margin:10px">LINK DO EPG XML</a>
        </body>
    """)

@app.route('/playlist.m3u')
def playlist():
    return Response(get_channels(), mimetype='text/plain')

@app.route('/epg.xml')
def epg():
    return Response(fetch_epg(), mimetype='application/xml')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
