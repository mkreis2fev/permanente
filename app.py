import requests
from flask import Flask, jsonify, Response, render_template_string
import os

app = Flask(__name__)

# Configurações das fontes de dados
SOURCES = {
    "s1_sinalpublic": {
        "url": "https://apisinalpublico.vercel.app/canais.json",
        "referer": "https://sinalpublic.vercel.app/",
        "label": "S1"
    },
    "s2_minhatela": {
        "url": "https://myapiplay.top/api/guiadejogos/epg.php",
        "referer": "https://minhatela.xyz/",
        "player_base": "https://meuplayeronlinehd.com/myplay/watch.html?id=",
        "label": "S2"
    }
}

def fetch_channels():
    all_channels = []
    headers_base = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # 1. Extração S1 (Sinal Público)
    try:
        s1_cfg = SOURCES["s1_sinalpublic"]
        headers = headers_base.copy()
        headers["Referer"] = s1_cfg["referer"]
        
        response = requests.get(s1_cfg["url"], headers=headers, timeout=10)
        if response.status_code == 200:
            for item in response.json():
                all_channels.append({
                    "name": f"[{s1_cfg['label']}] {item.get('name')}",
                    "url": item.get("url"),
                    "logo": item.get("image"),
                    "group": s1_cfg["label"]
                })
    except Exception as e:
        print(f"Erro ao buscar S1: {e}")

    # 2. Extração S2 (Minha Tela)
    try:
        s2_cfg = SOURCES["s2_minhatela"]
        headers = headers_base.copy()
        headers["Referer"] = s2_cfg["referer"]
        
        response = requests.get(s2_cfg["url"], headers=headers, timeout=10)
        if response.status_code == 200:
            for item in response.json():
                if item.get("channelLogo"):
                    all_channels.append({
                        "name": f"[{s2_cfg['label']}] {item.get('name')}",
                        "url": f"{s2_cfg['player_base']}{item.get('channelLogo')}",
                        "logo": item.get("logo"),
                        "group": s2_cfg["label"]
                    })
    except Exception as e:
        print(f"Erro ao buscar S2: {e}")

    return all_channels

@app.route('/')
def home():
    return render_template_string("""
        <html>
            <head><title>IPTV Agregador S1 & S2</title></head>
            <body style="font-family:sans-serif; background:#121212; color:white; text-align:center; padding:50px;">
                <h1 style="color:#007bff;">📡 Servidor IPTV Online</h1>
                <p>Canais S1 (Sinal Público) e S2 (Minha Tela) unificados.</p>
                <div style="margin:20px; padding:20px; border:1px solid #333; display:inline-block; border-radius:10px;">
                    Link da Playlist M3U:<br>
                    <input type="text" value="{{ url }}/playlist.m3u" style="width:400px; padding:10px; margin-top:10px; background:#000; color:#0f0; border:1px solid #555;" readonly>
                </div>
                <p><small>Copie o link acima e cole no seu reprodutor IPTV (VLC, Smarters, etc)</small></p>
            </body>
        </html>
    """, url=os.environ.get('RAILWAY_STATIC_URL', 'http://localhost:5000'))

@app.route('/playlist.m3u')
def playlist():
    channels = fetch_channels()
    m3u = "#EXTM3U\n"
    for c in channels:
        m3u += f'#EXTINF:-1 tvg-logo="{c["logo"]}" group-title="{c["group"]}",{c["name"]}\n'
        m3u += f'{c["url"]}\n'
    return Response(m3u, mimetype='text/plain')

@app.route('/api/json')
def api():
    return jsonify(fetch_channels())

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
