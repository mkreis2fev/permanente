import os
import re
import requests
import base64
from flask import Flask, Response, request, redirect, jsonify
from urllib.parse import urljoin

app = Flask(__name__)

# Canais com Links Diretos (Muito mais estáveis)
STATIC_CHANNELS = {
    "globonews": "http://177.52.24.163/GLOBO-NEWS-HD/index.m3u8",
}

# Configurações do Scraper
PLAYER_URL = "https://sinaldvd.github.io/tv/player.html?id="
REFERER = "https://sinaldvd.github.io/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Referer': REFERER,
    'Origin': 'https://sinaldvd.github.io',
}

def clean_url(url):
    """ Remove vírgulas, espaços e caracteres invisíveis da URL """
    if not url:
        return url
    return url.replace(',', '').replace(' ', '').replace('\n', '').replace('\r', '').strip()

def get_stream_url(channel_id):
    """ Busca o link dinâmico e garante que ele esteja limpo """
    # 1. Tenta o link estático primeiro
    if channel_id in STATIC_CHANNELS:
        return clean_url(STATIC_CHANNELS[channel_id])

    url = f"{PLAYER_URL}{channel_id}"
    try:
        session = requests.Session()
        response = session.get(url, headers=HEADERS, timeout=15)
        content = response.text

        # Tenta extrair domínios dinâmicos da Vercel
        source_matches = re.findall(r'https?://[a-z0-9-]+-cloudflare-net\.vercel\.app', content)
        if source_matches:
            raw_url = f"{source_matches[0]}/{channel_id}.m3u8"
            return clean_url(raw_url)

        # Fallback Base64
        b64_matches = re.findall(r'atob\(["\']([^"\']+)["\']\)', content)
        for b64_str in b64_matches:
            try:
                decoded = base64.b64decode(b64_str).decode('utf-8')
                m3u8_match = re.search(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', decoded)
                if m3u8_match:
                    return clean_url(m3u8_match.group(1).replace('\\/', '/'))
            except: continue
    except: pass

    # Link de emergência caso tudo falhe
    return clean_url(f"https://t5r4e3w2q1y0-cloudflare-net.vercel.app/{channel_id}.m3u8")

@app.route('/')
def home():
    return "Servidor IPTV Proxy Rodando. Playlist em /playlist.m3u"

@app.route('/playlist.m3u')
def playlist():
    host = request.host
    scheme = request.scheme

    channels = [
        {"id": "globonews", "name": "Globo News (HD Direto)", "logo": "https://logodownload.org/wp-content/uploads/2020/03/globo-news-logo.png"},
        {"id": "globorj", "name": "Globo RJ", "logo": "https://logodownload.org/wp-content/uploads/2020/03/rede-globo-logo.png"},
        {"id": "g1", "name": "G1", "logo": "https://logodownload.org/wp-content/uploads/2020/03/g1-logo.png"},
        {"id": "test", "name": "[TESTE] Big Buck Bunny", "logo": "https://upload.wikimedia.org/wikipedia/commons/c/c5/Big_Buck_Bunny_Logo.png"}
    ]

    m3u = "#EXTM3U\n"
    for ch in channels:
        m3u += f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-logo="{ch["logo"]}" group-title="Canais",{ch["name"]}\n'
        m3u += f'{scheme}://{host}/stream/{ch["id"]}\n'

    return Response(m3u, mimetype='application/x-mpegurl')

@app.route('/stream/<channel_id>')
def stream(channel_id):
    if channel_id == "test":
        return redirect("http://sample.vodobox.net/skate_phantom_flex_4k/skate_phantom_flex_4k.m3u8")

    stream_url = get_stream_url(channel_id)

    # Se for link de IP direto, redireciona sem headers extras
    if "177.52.24.163" in stream_url:
        return redirect(stream_url)

    # Para outros, anexa os headers de bypass
    suffix = f"|Referer={REFERER}&User-Agent={HEADERS['User-Agent']}"
    return redirect(stream_url + suffix)

@app.route('/debug/<channel_id>')
def debug(channel_id):
    url = get_stream_url(channel_id)
    return jsonify({"channel": channel_id, "clean_url": url})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
