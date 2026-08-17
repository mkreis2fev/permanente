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
    'Origin': 'https://sinaldvd.github.io',
    'Accept': '*/*',
}

def get_stream_url(channel_id):
    """ Busca o link .m3u8 real na página fonte usando padrões conhecidos """
    url = f"{PLAYER_URL}{channel_id}"
    try:
        session = requests.Session()
        # O Referer deve ser o site da Vercel para passar em alguns checks de segurança
        headers = HEADERS.copy()
        headers['Referer'] = 'https://sinalpublicoetv.vercel.app/'
        
        response = session.get(url, headers=headers, timeout=15)
        content = response.text

        # 1. Tenta extrair domínios dinâmicos das fontes encontradas no código
        # Exemplo: https://t5r4e3w2q1y0-cloudflare-net.vercel.app/${canalId}.m3u8
        source_matches = re.findall(r'https?://[a-z0-9-]+-cloudflare-net\.vercel\.app', content)
        if source_matches:
            # Retorna o primeiro link construído com o ID do canal
            return f"{source_matches[0]}/{channel_id}.m3u8"

        # 2. Fallback para domínios conhecidos caso o regex falhe
        known_domains = [
            "t5r4e3w2q1y0-cloudflare-net.vercel.app",
            "a9b8c7d6e5f4-cloudflare-net.vercel.app"
        ]
        # Verificamos se esses domínios aparecem no texto da página
        for domain in known_domains:
            if domain in content:
                return f"https://{domain}/{channel_id}.m3u8"

        # 3. Busca padrão base64 (atob)
        b64_matches = re.findall(r'atob\(["\']([^"\']+)["\']\)', content)
        for b64_str in b64_matches:
            try:
                decoded = base64.b64decode(b64_str).decode('utf-8')
                m3u8_match = re.search(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', decoded)
                if m3u8_match:
                    return m3u8_match.group(1).replace('\\/', '/')
            except: continue

    except Exception as e:
        print(f"Erro ao buscar canal {channel_id}: {e}")
    
    # Se tudo falhar, retorna o link provável baseado na estrutura descoberta
    return f"https://t5r4e3w2q1y0-cloudflare-net.vercel.app/{channel_id}.m3u8"

@app.route('/')
def home():
    return "Servidor IPTV Proxy Rodando. Use /playlist.m3u"

@app.route('/playlist.m3u')
def playlist():
    host = request.host
    scheme = request.scheme

    channels = [
        {"id": "globonews", "name": "Globo News", "logo": "https://logodownload.org/wp-content/uploads/2020/03/globo-news-logo.png"},
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
    
    # O Referer precisa ser o player original para o servidor autorizar o stream
    suffix = f"|Referer=https://sinaldvd.github.io/&Origin=https://sinaldvd.github.io/&User-Agent={HEADERS['User-Agent']}"
    
    return redirect(stream_url + suffix)

@app.route('/debug/<channel_id>')
def debug(channel_id):
    url = get_stream_url(channel_id)
    return jsonify({"channel": channel_id, "url": url, "status": "ok" if url else "fail"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
