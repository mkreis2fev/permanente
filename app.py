import os
import re
import requests
import base64
from flask import Flask, Response, request, redirect, jsonify
from urllib.parse import urljoin

app = Flask(__name__)

# Configurações do Scraper
PLAYER_URL = "https://sinaldvd.github.io/tv/player.html?id="
REFERER = "https://sinaldvd.github.io/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Referer': REFERER,
    'Origin': 'https://sinaldvd.github.io'
}

def get_stream_url(channel_id):
    """ Busca o link .m3u8 real na página fonte """
    url = f"{PLAYER_URL}{channel_id}"
    try:
        session = requests.Session()
        # Aumentamos o timeout e permitimos redirecionamentos
        response = session.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        content = response.text

        # 1. Procura links em base64 (atob)
        b64_matches = re.findall(r'atob\(["\']([^"\']+)["\']\)', content)
        for b64_str in b64_matches:
            try:
                decoded = base64.b64decode(b64_str).decode('utf-8')
                m3u8_match = re.search(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', decoded)
                if m3u8_match:
                    return m3u8_match.group(1).replace('\\/', '/')
            except: continue

        # 2. Busca direta no HTML por .m3u8
        match = re.search(r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']', content)
        if match:
            return match.group(1).replace('\\/', '/')

        # 3. Busca por strings que pareçam URLs .m3u8 ocultas
        match = re.search(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', content)
        if match:
            return match.group(1).replace('\\/', '/')

    except Exception as e:
        print(f"Erro ao buscar canal {channel_id}: {e}")
    return None

@app.route('/')
def home():
    return "Servidor IPTV Proxy Rodando. Use o link /playlist.m3u no seu App."

@app.route('/playlist.m3u')
def playlist():
    """ Retorna a playlist M3U """
    host = request.host
    scheme = request.scheme
    
    channels = [
        {"id": "globonews", "name": "Globo News", "logo": "https://logodownload.org/wp-content/uploads/2020/03/globo-news-logo.png"},
        {"id": "globorj", "name": "Globo RJ", "logo": "https://logodownload.org/wp-content/uploads/2020/03/rede-globo-logo.png"},
        {"id": "g1", "name": "G1", "logo": "https://logodownload.org/wp-content/uploads/2020/03/g1-logo.png"},
        # Canal de teste direto para verificar se o app IPTV está funcionando
        {"id": "test", "name": "[TESTE] Big Buck Bunny", "logo": "https://upload.wikimedia.org/wikipedia/commons/c/c5/Big_Buck_Bunny_Logo.png"}
    ]

    m3u = "#EXTM3U\n"
    for ch in channels:
        m3u += f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-logo="{ch["logo"]}" group-title="Canais",{ch["name"]}\n'
        m3u += f'{scheme}://{host}/stream/{ch["id"]}\n'

    return Response(m3u, mimetype='application/x-mpegurl', headers={"Content-Disposition": "attachment; filename=playlist.m3u"})

@app.route('/stream/<channel_id>')
def stream(channel_id):
    # Canal de teste direto
    if channel_id == "test":
        return redirect("http://sample.vodobox.net/skate_phantom_flex_4k/skate_phantom_flex_4k.m3u8")

    stream_url = get_stream_url(channel_id)
    if not stream_url:
        return "Canal Offline ou não encontrado.", 404

    # Redireciona para o stream com o Referer anexado
    # Muitos apps IPTV interpretam o "|" como separador de headers
    final_url = stream_url
    if "|" not in final_url:
        final_url += f"|Referer={REFERER}&User-Agent={HEADERS['User-Agent']}"
    
    return redirect(final_url)

# Rota para testar no navegador o que o scraper está capturando
@app.route('/debug/<channel_id>')
def debug(channel_id):
    url = get_stream_url(channel_id)
    return jsonify({
        "channel": channel_id,
        "captured_url": url,
        "status": "success" if url else "failed"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
