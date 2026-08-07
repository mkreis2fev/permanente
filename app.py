import requests
from flask import Flask, jsonify, render_template_string, Response

app = Flask(__name__)

SOURCES = {
    "minhatela": {
        "url": "https://myapiplay.top/api/guiadejogos/epg.php",
        "referer": "https://minhatela.xyz/",
        "player_base": "https://meuplayeronlinehd.com/myplay/watch.html?id="
    },
    "sinalpublic": {
        "url": "https://apisinalpublico.vercel.app/canais.json",
        "referer": "https://sinalpublic.vercel.app/"
    }
}

def fetch_all_channels():
    all_channels = []
    
    # Minha Tela
    try:
        h1 = {"Referer": SOURCES["minhatela"]["referer"], "User-Agent": "Mozilla/5.0"}
        r1 = requests.get(SOURCES["minhatela"]["url"], headers=h1, timeout=10)
        if r1.status_code == 200:
            for item in r1.json():
                if item.get("channelLogo"):
                    all_channels.append({
                        "name": item.get("name"),
                        "url": f"{SOURCES['minhatela']['player_base']}{item.get('channelLogo')}",
                        "logo": item.get("logo"),
                        "group": "Minha Tela"
                    })
    except: pass

    # Sinal Público
    try:
        h2 = {"Referer": SOURCES["sinalpublic"]["referer"], "User-Agent": "Mozilla/5.0"}
        r2 = requests.get(SOURCES["sinalpublic"]["url"], headers=h2, timeout=10)
        if r2.status_code == 200:
            for item in r2.json():
                all_channels.append({
                    "name": item.get("name"),
                    "url": item.get("url"),
                    "logo": item.get("image"),
                    "group": "Sinal Público"
                })
    except: pass
    
    return all_channels

@app.route('/')
def index():
    return "<h1>Servidor IPTV Ativo</h1><p>Link da Playlist: <b>/playlist.m3u</b></p>"

@app.route('/api/channels')
def get_channels():
    return jsonify(fetch_all_channels())

@app.route('/playlist.m3u')
def generate_m3u():
    """Gera a lista no formato M3U para aplicativos de IPTV"""
    channels = fetch_all_channels()
    m3u_content = "#EXTM3U\n"
    
    for c in channels:
        m3u_content += f'#EXTINF:-1 tvg-logo="{c["logo"]}" group-title="{c["group"]}",{c["name"]}\n'
        m3u_content += f'{c["url"]}\n'
    
    return Response(m3u_content, mimetype='text/plain')

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
