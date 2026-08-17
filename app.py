import os
import re
import requests
from flask import Flask, Response, redirect, request

app = Flask(__name__)

# Configurações do Scraper
# O player real fica hospedado no github.io
PLAYER_URL = "https://sinaldvd.github.io/tv/player.html?id="

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'Referer': 'https://sinaldvd.github.io/',
    'Origin': 'https://sinaldvd.github.io'
}

def get_stream_url(channel_id):
    """
    Tenta extrair a URL do stream (.m3u8) da página do player.
    """
    url = f"{PLAYER_URL}{channel_id}"
    try:
        session = requests.Session()
        response = session.get(url, headers=HEADERS, timeout=10)
        content = response.text

        # 1. Tenta encontrar URL direta de .m3u8
        match = re.search(r'["\'](http[^"\']+\.m3u8[^"\']*)["\']', content)
        if match:
            return match.group(1).replace('\\/', '/')

        # 2. Tenta encontrar links em base64 (comum nesses players)
        b64_matches = re.findall(r'atob\(["\']([^"\']+)["\']\)', content)
        for b64 in b64_matches:
            try:
                import base64
                decoded = base64.b64decode(b64).decode('utf-8')
                if '.m3u8' in decoded:
                    return decoded
            except:
                continue

    except Exception as e:
        print(f"Erro ao capturar canal {channel_id}: {e}")

    return None

@app.route('/')
def home():
    return "Servidor IPTV Proxy Ativo. Use /playlist.m3u no seu leitor."

@app.route('/playlist.m3u')
def playlist():
    host = request.host
    scheme = request.scheme
    
    # Lista de canais comuns que costumam funcionar nesse sistema
    channels = [
        {"id": "globonews", "name": "Globo News", "logo": "https://logodownload.org/wp-content/uploads/2020/03/globo-news-logo.png"},
        {"id": "globorj", "name": "Globo RJ", "logo": "https://logodownload.org/wp-content/uploads/2020/03/rede-globo-logo.png"},
        {"id": "cnn", "name": "CNN Brasil", "logo": "https://logodownload.org/wp-content/uploads/2020/03/cnn-brasil-logo.png"},
        {"id": "sportv", "name": "SporTV", "logo": "https://logodownload.org/wp-content/uploads/2020/03/sportv-logo.png"},
    ]
    
    m3u = "#EXTM3U\n"
    for ch in channels:
        m3u += f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-name="{ch["name"]}" tvg-logo="{ch["logo"]}" group-title="TV",{ch["name"]}\n'
        m3u += f'{scheme}://{host}/stream/{ch["id"]}\n'
    
    return Response(m3u, mimetype='audio/x-mpegurl')

@app.route('/stream/<channel_id>')
def stream(channel_id):
    stream_url = get_stream_url(channel_id)
    if stream_url:
        # Alguns players exigem que o referer seja mantido
        return redirect(stream_url)
    return "Canal não encontrado ou link expirado.", 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
