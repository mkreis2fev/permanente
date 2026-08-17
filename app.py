import os
import re
import requests
import base64
from flask import Flask, Response, redirect, request

app = Flask(__name__)

# Configurações do Scraper
PLAYER_URL = "https://sinaldvd.github.io/tv/player.html?id="
# Referer que o servidor de vídeo espera para autorizar o sinal
REFERER = "https://sinaldvd.github.io/"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Referer': REFERER,
    'Accept': '*/*',
}

def get_stream_url(channel_id):
    """
    Extrai a URL do stream tentando decodificar scripts e base64 da página fonte
    """
    url = f"{PLAYER_URL}{channel_id}"
    try:
        session = requests.Session()
        response = session.get(url, headers=HEADERS, timeout=15)
        content = response.text

        # 1. Tenta encontrar links em Base64 (estratégia comum do site fonte)
        b64_matches = re.findall(r'atob\(["\']([^"\']+)["\']\)', content)
        for b64_str in b64_matches:
            try:
                decoded = base64.b64decode(b64_str).decode('utf-8')
                # Procura o link .m3u8 dentro do conteúdo decodificado
                m3u8_match = re.search(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', decoded)
                if m3u8_match:
                    return m3u8_match.group(1).replace('\\/', '/')
            except:
                continue

        # 2. Busca direta por .m3u8 no HTML caso não esteja em Base64
        match = re.search(r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']', content)
        if match:
            return match.group(1).replace('\\/', '/')

    except Exception as e:
        print(f"Erro no Scraper para {channel_id}: {e}")

    return None

@app.route('/')
def home():
    return "Servidor Proxy IPTV Online. Use /playlist.m3u no seu leitor."

@app.route('/playlist.m3u')
def playlist():
    """
    Gera a playlist M3U dinâmica para ser usada no app IPTV
    """
    host = request.host
    scheme = request.scheme

    # Você pode adicionar mais IDs de canais aqui conforme descobrir
    channels = [
        {"id": "globonews", "name": "Globo News", "logo": "https://logodownload.org/wp-content/uploads/2020/03/globo-news-logo.png"},
        {"id": "globorj", "name": "Globo RJ", "logo": "https://logodownload.org/wp-content/uploads/2020/03/rede-globo-logo.png"},
        {"id": "g1", "name": "G1", "logo": "https://logodownload.org/wp-content/uploads/2020/03/g1-logo.png"},
    ]

    m3u = "#EXTM3U\n"
    for ch in channels:
        # AQUI ESTÁ O SEGREDO: Definimos a rota de stream deste servidor
        m3u += f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-logo="{ch["logo"]}" group-title="Canais",{ch["name"]}\n'
        m3u += f'{scheme}://{host}/stream/{ch["id"]}\n'

    return Response(m3u, mimetype='audio/x-mpegurl')

@app.route('/stream/<channel_id>')
def stream(channel_id):
    """
    Captura o link real e redireciona o player com os cabeçalhos necessários
    """
    stream_url = get_stream_url(channel_id)
    if stream_url:
        # Anexamos o Referer ao link final. 
        # Formato |Referer=... é reconhecido por VLC, TiviMate e outros.
        if "|" not in stream_url:
            stream_url += f"|Referer={REFERER}"
        return redirect(stream_url)

    return "Canal indisponível.", 404

if __name__ == '__main__':
    # O Railway define a porta automaticamente na variável de ambiente PORT
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
