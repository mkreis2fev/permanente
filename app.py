import os
import requests
import re
from flask import Flask, Response, render_template_string

app = Flask(__name__)

# URL de exemplo para capturar canais e EPG (Fontes do IPTV-ORG)
SOURCE_URL = "https://iptv-org.github.io/iptv/countries/br.m3u"
EPG_URL = "https://iptv-org.github.io/epg/guides/br/mi.tv.epg.xml"

def get_channels():
    """
    Busca os canais e insere a tag x-tvg-url para o player encontrar o EPG.
    """
    try:
        response = requests.get(SOURCE_URL, timeout=10)
        if response.status_code == 200:
            content = response.text
            # Usamos a variável de ambiente do Railway para gerar o link dinâmico do EPG
            domain = os.environ.get("RAILWAY_STATIC_URL", "seu-link.up.railway.app")
            if content.startswith("#EXTM3U"):
                content = content.replace("#EXTM3U", f'#EXTM3U x-tvg-url="https://{domain}/epg.xml"', 1)
            return content
        return "#EXTM3U\n#ERRO: Lista indisponível"
    except Exception as e:
        return f"#EXTM3U\n#ERRO: {str(e)}"

def fetch_epg():
    """
    Busca o conteúdo XML do guia de programação.
    """
    try:
        response = requests.get(EPG_URL, timeout=15)
        if response.status_code == 200:
            return response.text
        return '<?xml version="1.0" encoding="UTF-8"?><tv></tv>'
    except:
        return '<?xml version="1.0" encoding="UTF-8"?><tv></tv>'

@app.route('/')
def index():
    return render_template_string("""
        <body style="background:#121212;color:white;text-align:center;padding:50px;font-family:sans-serif">
            <h1>Veloplay TV - Gerador de M3U & EPG</h1>
            <p>Servidor rodando no Railway!</p>
            <br>
            <a href="/playlist.m3u" style="display:inline-block;background:#ffaa00;color:black;padding:15px;text-decoration:none;border-radius:5px;font-weight:bold;margin:10px">LINK DA LISTA M3U</a>
            <a href="/epg.xml" style="display:inline-block;background:#ffaa00;color:black;padding:15px;text-decoration:none;border-radius:5px;font-weight:bold;margin:10px">LINK DO EPG XML</a>
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
