import os
import re
import requests
import base64
from flask import Flask, Response, request, redirect
from urllib.parse import urljoin

app = Flask(__name__)

# Configurações do Scraper
PLAYER_URL = "https://sinaldvd.github.io/tv/player.html?id="
REFERER = "https://sinaldvd.github.io/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Referer': REFERER
}

def get_stream_url(channel_id):
    """ Busca o link .m3u8 real na página fonte do sinaldvd """
    url = f"{PLAYER_URL}{channel_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        content = response.text

        # 1. Procura em base64 (padrão de proteção do site)
        b64_matches = re.findall(r'atob\(["\']([^"\']+)["\']\)', content)
        for b64_str in b64_matches:
            try:
                decoded = base64.b64decode(b64_str).decode('utf-8')
                m3u8_match = re.search(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', decoded)
                if m3u8_match:
                    return m3u8_match.group(1).replace('\\/', '/')
            except: 
                continue

        # 2. Busca direta no HTML caso não esteja oculto
        match = re.search(r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']', content)
        if match:
            return match.group(1).replace('\\/', '/')
    except: 
        pass
    return None

@app.route('/')
def home():
    return "Servidor Proxy IPTV Online. Adicione /playlist.m3u ao seu app."

@app.route('/playlist.m3u')
def playlist():
    """ Gera a playlist M3U que você vai colocar no seu App IPTV """
    host = request.host
    scheme = request.scheme

    # Canais disponíveis - Você pode adicionar novos IDs aqui
    channels = [
        {"id": "globonews", "name": "Globo News", "logo": "https://logodownload.org/wp-content/uploads/2020/03/globo-news-logo.png"},
        {"id": "globorj", "name": "Globo RJ", "logo": "https://logodownload.org/wp-content/uploads/2020/03/rede-globo-logo.png"},
        {"id": "g1", "name": "G1", "logo": "https://logodownload.org/wp-content/uploads/2020/03/g1-logo.png"},
    ]

    m3u = "#EXTM3U\n"
    for ch in channels:
        m3u += f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-logo="{ch["logo"]}" group-title="Canais",{ch["name"]}\n'
        m3u += f'{scheme}://{host}/stream/{ch["id"]}\n'

    return Response(m3u, mimetype='audio/x-mpegurl')

@app.route('/stream/<channel_id>')
def stream(channel_id):
    """ Atua como um túnel (proxy) para o arquivo de vídeo (.m3u8) """
    stream_url = get_stream_url(channel_id)
    if not stream_url:
        return "Canal Offline", 404

    try:
        # O Railway baixa o conteúdo do arquivo para contornar o bloqueio de Referer
        r = requests.get(stream_url, headers=HEADERS, timeout=10)
        content = r.text

        # Corrige os links de vídeo dentro do arquivo para que o player os encontre
        base_url = stream_url.split('?')[0].rsplit('/', 1)[0] + '/'

        new_lines = []
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # Transforma links relativos em links completos (absolutos)
                if not line.startswith('http'):
                    new_lines.append(urljoin(base_url, line))
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        proxy_content = '\n'.join(new_lines)
        return Response(proxy_content, mimetype='application/vnd.apple.mpegurl')

    except Exception as e:
        # Se o processamento falhar, tenta apenas o redirecionamento direto
        return redirect(stream_url + f"|Referer={REFERER}")

if __name__ == '__main__':
    # Configuração de porta para Railway
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
