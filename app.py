import os
import requests
from flask import Flask, Response, render_template_string

app = Flask(__name__)

# FONTES MASSIVAS - Unindo os maiores repositórios mundiais e nacionais
SOURCES = [
    "https://iptv-org.github.io/iptv/countries/br.m3u",          # Brasil Oficial
    "https://iptv-org.github.io/iptv/countries/pt.m3u",          # Portugal
    "https://iptv-org.github.io/iptv/categories/movies.m3u",     # Filmes Mundial
    "https://iptv-org.github.io/iptv/categories/sports.m3u",     # Esportes Mundial
    "https://iptv-org.github.io/iptv/categories/animation.m3u",  # Kids/Desenhos
    "https://iptv-org.github.io/iptv/categories/documentary.m3u",# Documentários
    "https://raw.githubusercontent.com/Fmacedo87/m3u/main/Canais.m3u", # Lista BR Alternativa 1
    "https://raw.githubusercontent.com/Deivisson09/O-melhor-do-IPTV/main/Lista%20de%20Canais.m3u", # Lista BR Alternativa 2
]

EPG_URL = "https://iptv-org.github.io/epg/guides/br/mi.tv.epg.xml"

def get_channels():
    combined_m3u = "#EXTM3U"
    domain = os.environ.get("RAILWAY_STATIC_URL", "seu-app.up.railway.app")
    combined_m3u += f' x-tvg-url="https://{domain}/epg.xml"\n'

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    seen_links = set() # Para evitar canais duplicados

    for url in SOURCES:
        try:
            # verify=False ajuda a carregar listas de sites com SSL vencido
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            if response.status_code == 200:
                lines = response.text.splitlines()
                current_info = ""
                
                for line in lines:
                    line = line.strip()
                    if line.startswith("#EXTINF"):
                        current_info = line
                    elif line.startswith("http"):
                        # Se o link ainda não foi adicionado, coloca na lista
                        if line not in seen_links:
                            combined_m3u += current_info + "\n" + line + "\n"
                            seen_links.add(line)
        except:
            continue

    return combined_m3u

@app.route('/')
def index():
    return render_template_string("""
        <body style="background:#0a0a0a;color:#eee;text-align:center;padding:50px;font-family:sans-serif">
            <h1 style="color:#ffaa00;font-size:3em">Veloplay Ultra API</h1>
            <p style="color:#888">Sincronizando múltiplas redes de transmissão...</p>
            <div style="background:#1a1a1a;padding:30px;border-radius:15px;display:inline-block;margin-top:20px;border:1px solid #333">
                <a href="/playlist.m3u" style="display:block;background:#ffaa00;color:#000;padding:20px 40px;text-decoration:none;font-weight:bold;border-radius:5px;margin-bottom:15px">ACESSAR LISTA M3U COMPLETA</a>
                <a href="/epg.xml" style="color:#ffaa00;text-decoration:none;font-size:0.9em">Guia de Programação (EPG XML)</a>
            </div>
            <p style="margin-top:40px;font-size:0.8em;color:#444">Railway Engine v3.0 - Status: Online</p>
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
    # Railway utiliza a variável PORT
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
