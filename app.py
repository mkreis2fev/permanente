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
    """ Busca o link .m3u8 real na página fonte """
    url = f"{PLAYER_URL}{channel_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        content = response.text

        # 1. Procura links em base64 (atob) - Padrão de proteção do site
        b64_matches = re.findall(r'atob\(["\']([^"\']+)["\']\)', content)
        for b64_str in b64_matches:
            try:
                decoded = base64.b64decode(b64_str).decode('utf-8')
                m3u8_match = re.search(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', decoded)
                if m3u8_match:
                    return m3u8_match.group(1).replace('\\/', '/')
            except: continue

        # 2. Busca direta no HTML caso não esteja oculto
        match = re.search(r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']', content)
        if match:
            return match.group(1).replace('\\/', '/')

        # 3. Busca por qualquer string que contenha .m3u8
        match = re.search(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', content)
        if match:
            return match.group(1).replace('\\/', '/')

    except: pass
    return None

@app.route('/')
def home():
    return "Servidor Proxy IPTV Online. Adicione /playlist.m3u ao seu app."

@app.route('/playlist.m3u')
def playlist():
    """ Retorna a playlist como texto puro para evitar o player automático do navegador """
    host = request.host
    scheme = request.scheme

    channels = [
        {"id": "globonews", "name": "Globo News", "logo": "https://logodownload.org/wp-content/uploads/2020/03/globo-news-logo.png"},
        {"id": "globorj", "name": "Globo RJ", "logo": "https://logodownload.org/wp-content/uploads/2020/03/rede-globo-logo.png"},
        {"id": "g1", "name": "G1", "logo": "https://logodownload.org/wp-content/uploads/2020/03/g1-logo.png"},
    ]

    m3u = "#EXTM3U\n"
    for ch in channels:
        m3u += f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-logo="{ch["logo"]}" group-title="Canais",{ch["name"]}\n'
        # Rota de stream que passa pelo nosso servidor proxy
        m3u += f'{scheme}://{host}/stream/{ch["id"]}\n'

    # mimetype text/plain garante que o navegador mostre o texto em vez de tentar tocar
    return Response(m3u, mimetype='text/plain')

@app.route('/stream/<channel_id>')
def stream(channel_id):
    """ Atua como proxy para o arquivo m3u8, corrigindo links internos """
    stream_url = get_stream_url(channel_id)
    if not stream_url:
        return "Canal Offline", 404

    try:
        # O servidor Railway faz o download do manifesto para contornar bloqueios de Referer
        r = requests.get(stream_url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return redirect(stream_url + f"|Referer={REFERER}")

        content = r.text
        # Define a base para transformar links relativos em absolutos
        base_url = stream_url.split('?')[0].rsplit('/', 1)[0] + '/'

        new_lines = []
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # Reescreve o link para ser completo
                new_lines.append(urljoin(base_url, line))
            else:
                new_lines.append(line)

        return Response('\n'.join(new_lines), mimetype='application/vnd.apple.mpegurl')

    except:
        # Em caso de erro, tenta o redirecionamento com o parâmetro de Referer
        return redirect(stream_url + f"|Referer={REFERER}")

if __name__ == '__main__':
    # Railway define a variável PORT
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
