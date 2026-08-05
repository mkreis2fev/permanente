import os
import requests
from flask import Flask, Response, render_template_string

app = Flask(__name__)

# --- FONTES ---
# O servidor que está te bloqueando
VELO_LINK = "http://fastcdn.bond:8080/get.php?username=vWRJvKkPDX&password=vWRJvKkPDX&type=m3u_plus&output=ts"

# Fontes Premium Alternativas (Muito mais estáveis para servidores)
SOURCES = [
    "https://raw.githubusercontent.com/Fmacedo87/m3u/main/Canais.m3u",
    "https://iptv-org.github.io/iptv/countries/br.m3u",
    "https://raw.githubusercontent.com/Deivisson09/O-melhor-do-IPTV/main/Lista%20de%20Canais.m3u"
]

def get_channels():
    # Tenta o VeloPlay rápido (Bypass de 3 segundos)
    headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; TV Box)'}
    try:
        r = requests.get(VELO_LINK, headers=headers, timeout=3)
        if r.status_code == 200 and "#EXTM3U" in r.text:
            return r.text
    except:
        pass

    # Se o VeloPlay der erro (bloqueio de IP), une as fontes de backup
    combined = "#EXTM3U x-tvg-url='https://iptv-org.github.io/epg/guides/br/mi.tv.epg.xml'\n"
    combined += "# AVISO: Servidor VeloPlay Bloqueado. Usando Rede Alternativa.\n"
    
    for url in SOURCES:
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                # Limpa o cabeçalho das listas extras
                lines = res.text.splitlines()
                for line in lines:
                    if not line.startswith("#EXTM3U"):
                        combined += line + "\n"
        except:
            continue
    return combined

@app.route('/')
def home():
    return "<h1>Veloplay API Ativa</h1><p>Lista disponivel em: /playlist.m3u</p>"

@app.route('/playlist.m3u')
def playlist():
    return Response(get_channels(), mimetype='text/plain')

@app.route('/epg.xml')
def epg():
    r = requests.get("https://iptv-org.github.io/epg/guides/br/mi.tv.epg.xml", timeout=10)
    return Response(r.text, mimetype='application/xml')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
