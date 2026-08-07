import requests
import re
from flask import Flask, jsonify, Response, render_template_string
import os

app = Flask(__name__)

# Configurações das fontes
SOURCES = {
    "S1": {
        "url": "https://apisinalpublico.vercel.app/canais.json",
        "referer": "https://sinalpublic.vercel.app/"
    },
    "S2": {
        "url": "https://myapiplay.top/api/guiadejogos/epg.php",
        "referer": "https://minhatela.xyz/",
        "player_base": "https://meuplayeronlinehd.com/myplay/watch.html?id="
    }
}

def get_direct_stream(url, referer):
    """
    Tenta extrair o link .m3u8 real de uma página de player.
    """
    try:
        headers = {
            "Referer": referer,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        # 1. Acessa a página do player
        response = requests.get(url, headers=headers, timeout=5)
        html = response.text
        
        # 2. Procura por links .m3u8 no código fonte
        stream_match = re.search(r'["\'](https?://.*?\.m3u8.*?)["\']', html)
        if stream_match:
            return stream_match.group(1)
            
        # 3. Se não achar m3u8, tenta achar um iframe que possa conter o vídeo
        iframe_match = re.search(r'iframe.*?src=["\'](.*?)["\']', html)
        if iframe_match:
            # Recursão simples para tentar achar dentro do iframe
            return get_direct_stream(iframe_match.group(1), url)
            
    except:
        pass
    return url # Retorna a URL original se falhar

def fetch_channels():
    all_channels = []
    headers = {"User-Agent": "Mozilla/5.0"}

    # --- S1: Sinal Público ---
    try:
        r1 = requests.get(SOURCES["S1"]["url"], headers={"Referer": SOURCES["S1"]["referer"]}, timeout=5)
        if r1.status_code == 200:
            for item in r1.json():
                all_channels.append({
                    "name": f"[S1] {item.get('name')}",
                    "url": item.get("url"),
                    "logo": item.get("image"),
                    "group": "S1"
                })
    except: pass

    # --- S2: Minha Tela ---
    try:
        r2 = requests.get(SOURCES["S2"]["url"], headers={"Referer": SOURCES["S2"]["referer"]}, timeout=5)
        if r2.status_code == 200:
            for item in r2.json():
                if item.get("channelLogo"):
                    all_channels.append({
                        "name": f"[S2] {item.get('name')}",
                        "url": f"{SOURCES['S2']['player_base']}{item.get('channelLogo')}",
                        "logo": item.get("logo"),
                        "group": "S2"
                    })
    except: pass

    return all_channels

@app.route('/')
def home():
    return "<h1>Servidor IPTV S1 & S2 Ativo</h1><p>M3U: /playlist.m3u</p>"

@app.route('/playlist.m3u')
def playlist():
    channels = fetch_channels()
    # Adicionamos tags extras para ajudar o player a entender que é um vídeo HLS
    m3u = "#EXTM3U\n"
    for c in channels:
        # Nota: Alguns players precisam de User-Agent específico para abrir os canais
        m3u += f'#EXTINF:-1 tvg-logo="{c["logo"]}" group-title="{c["group"]}",{c["name"]}\n'
        m3u += f'#EXTVLCOPT:http-user-agent=Mozilla/5.0\n'
        m3u += f'{c["url"]}\n'
    return Response(m3u, mimetype='text/plain')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
