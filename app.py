import requests
from flask import Flask, jsonify, render_template_string, Response
import os

app = Flask(__name__)

# Configurações das fontes
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
    
    # Extração Minha Tela (Identificado como S2)
    try:
        headers_s2 = {
            "Referer": SOURCES["minhatela"]["referer"],
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        r1 = requests.get(SOURCES["minhatela"]["url"], headers=headers_s2, timeout=10)
        if r1.status_code == 200:
            for item in r1.json():
                if item.get("channelLogo"):
                    all_channels.append({
                        "name": item.get("name"),
                        "url": f"{SOURCES['minhatela']['player_base']}{item.get('channelLogo')}",
                        "logo": item.get("logo"),
                        "group": "S2"  # <--- Identificação solicitada
                    })
    except Exception as e:
        print(f"Erro S2 (Minha Tela): {e}")

    # Extração Sinal Público
    try:
        headers_sp = {
            "Referer": SOURCES["sinalpublic"]["referer"],
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        r2 = requests.get(SOURCES["sinalpublic"]["url"], headers=headers_sp, timeout=10)
        if r2.status_code == 200:
            for item in r2.json():
                all_channels.append({
                    "name": item.get("name"),
                    "url": item.get("url"),
                    "logo": item.get("image"),
                    "group": "Sinal Público"
                })
    except Exception as e:
        print(f"Erro Sinal Público: {e}")
    
    return all_channels

@app.route('/')
def index():
    return """
    <html>
        <body style="font-family: sans-serif; text-align: center; padding-top: 50px; background: #121212; color: white;">
            <h1>🚀 Servidor IPTV Ativo</h1>
            <p>Sua lista de canais está pronta!</p>
            <div style="background: #1e1e1e; padding: 20px; display: inline-block; border-radius: 10px; border: 1px solid #007bff;">
                Link para o seu App IPTV:<br>
                <code style="color: #007bff; font-size: 1.2em;">/playlist.m3u</code>
            </div>
            <p><a href="/api/channels" style="color: gray;">Ver API JSON</a></p>
        </body>
    </html>
    """

@app.route('/api/channels')
def get_channels():
    return jsonify(fetch_all_channels())

@app.route('/playlist.m3u')
def generate_m3u():
    """Gera a lista M3U para o reprodutor IPTV"""
    channels = fetch_all_channels()
    m3u_content = "#EXTM3U\n"
    
    for c in channels:
        # Formatação padrão IPTV com logo, grupo e nome
        m3u_content += f'#EXTINF:-1 tvg-logo="{c["logo"]}" group-title="{c["group"]}",{c["name"]}\n'
        m3u_content += f'{c["url"]}\n'
    
    return Response(m3u_content, mimetype='text/plain')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
