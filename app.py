from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import requests
import re
import os
from urllib.parse import urlparse
import hashlib
import base64

app = Flask(__name__)
CORS(app)

# Sessão persistente para capturar cookies e manter o sinal ativo
session = requests.Session()

# Cabeçalhos de segurança para liberar o vídeo no Cloudfront (Bypass 403)
HEADERS_BYPASS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://t5r4e3w2q1y0-cloudflare-net.vercel.app/',
    'Origin': 'https://t5r4e3w2q1y0-cloudflare-net.vercel.app',
    'X-Forwarded-For': '177.100.100.100' # Simula IP Brasileiro
}

# Lista completa de canais
LINKS = [
    {"name": "Globo News", "url": "https://sinalpublicoetv.vercel.app/?id=globonews", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globonews.png"},
    {"name": "Globo RJ", "url": "https://sinalpublicoetv.vercel.app/?id=globorj", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name": "Globo MG", "url": "https://sinalpublicoetv.vercel.app/?id=globomg", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name": "Globo SP", "url": "https://sinalpublicoetv.vercel.app/?id=globosp", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name": "Globo PE", "url": "https://sinalpublicoetv.vercel.app/?id=globope", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name": "Globo PB", "url": "https://sinalpublicoetv.vercel.app/?id=globopb", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name": "Globo RS", "url": "https://sinalpublicoetv.vercel.app/?id=globors", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name": "Globo ES", "url": "https://sinalpublicoetv.vercel.app/?id=globoes", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name": "Globo AM", "url": "https://sinalpublicoetv.vercel.app/?id=globoam", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name": "Globo CE", "url": "https://sinalpublicoetv.vercel.app/?id=globoce", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name": "SportyNet", "url": "https://sinalpublicoetv.vercel.app/?id=sportynet", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportynet.png"},
    {"name": "SportyNet+ 1", "url": "https://sinalpublicoetv.vercel.app/?id=sportynetplus1", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportynet.png"},
    {"name": "SportyNet+ 2", "url": "https://sinalpublicoetv.vercel.app/?id=sportynetplus2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportynet.png"},
    {"name": "SportyNet+ 3", "url": "https://sinalpublicoetv.vercel.app/?id=sportynetplus3", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportynet.png"},
    {"name": "Paramount+ 1", "url": "https://sinalpublicoetv.vercel.app/?id=paramountplus1", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/paramountplus.png"},
    {"name": "Paramount+ 2", "url": "https://sinalpublicoetv.vercel.app/?id=paramountplus2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/paramountplus.png"},
    {"name": "Paramount+ 3", "url": "https://sinalpublicoetv.vercel.app/?id=paramountplus3", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/paramountplus.png"},
    {"name": "MAX 1", "url": "https://sinalpublicoetv.vercel.app/?id=max1", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/max.png"},
    {"name": "MAX 2", "url": "https://sinalpublicoetv.vercel.app/?id=max2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/max.png"},
    {"name": "MAX 3", "url": "https://sinalpublicoetv.vercel.app/?id=max3", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/max.png"},
    {"name": "Cazé TV 1", "url": "https://sinalpublicoetv.vercel.app/?id=caze1", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/cazetv.png"},
    {"name": "Cazé TV 2", "url": "https://sinalpublicoetv.vercel.app/?id=caze2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/cazetv.png"},
    {"name": "Cazé TV 3", "url": "https://sinalpublicoetv.vercel.app/?id=caze3", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/cazetv.png"},
    {"name": "Disney+ 1", "url": "https://sinalpublicoetv.vercel.app/?id=disneyplus1", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/disneyplus.png"},
    {"name": "Disney+ 2", "url": "https://sinalpublicoetv.vercel.app/?id=disneyplus2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/disneyplus.png"},
    {"name": "Disney+ 3", "url": "https://sinalpublicoetv.vercel.app/?id=disneyplus3", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/disneyplus.png"},
    {"name": "Prime Video 1", "url": "https://sinalpublicoetv.vercel.app/?id=primevideo", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/prime-video.png"},
    {"name": "Prime Video 2", "url": "https://sinalpublicoetv.vercel.app/?id=primevideo2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/prime-video.png"},
    {"name": "Prime Video 3", "url": "https://sinalpublicoetv.vercel.app/?id=primevideo3", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/prime-video.png"},
    {"name": "Prime Video 4", "url": "https://sinalpublicoetv.vercel.app/?id=primevideo4", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/prime-video.png"},
    {"name": "ESPN", "url": "https://sinalpublicoetv.vercel.app/?id=espn", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/espn.png"},
    {"name": "ESPN 2", "url": "https://sinalpublicoetv.vercel.app/?id=espn2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/espn-2.png"},
    {"name": "ESPN 3", "url": "https://sinalpublicoetv.vercel.app/?id=espn3", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/espn-3.png"},
    {"name": "ESPN 4", "url": "https://sinalpublicoetv.vercel.app/?id=espn4", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/espn-4.png"},
    {"name": "ESPN 5", "url": "https://sinalpublicoetv.vercel.app/?id=espn5", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/espn-5.png"},
    {"name": "ESPN 6", "url": "https://sinalpublicoetv.vercel.app/?id=espn6", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/espn-6.png"},
    {"name": "Ge TV", "url": "https://sinalpublicoetv.vercel.app/?id=getv", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/ge-tv.png"},
    {"name": "Band Sports", "url": "https://sinalpublicoetv.vercel.app/?id=bandsports", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/band-sports.png"},
    {"name": "Combate", "url": "https://sinalpublicoetv.vercel.app/?id=combate", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/combate.png"},
    {"name": "Premiere Clubes", "url": "https://sinalpublicoetv.vercel.app/?id=premiere", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere.png"},
    {"name": "Premiere 2", "url": "https://sinalpublicoetv.vercel.app/?id=premiere2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-2.png"},
    {"name": "Premiere 3", "url": "https://sinalpublicoetv.vercel.app/?id=premiere3", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-3.png"},
    {"name": "Premiere 4", "url": "https://sinalpublicoetv.vercel.app/?id=premiere4", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-4.png"},
    {"name": "Premiere 5", "url": "https://sinalpublicoetv.vercel.app/?id=premiere5", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-5.png"},
    {"name": "Premiere 6", "url": "https://sinalpublicoetv.vercel.app/?id=premiere6", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-6.png"},
    {"name": "Premiere 7", "url": "https://sinalpublicoetv.vercel.app/?id=premiere7", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-7.png"},
    {"name": "Premiere 8", "url": "https://sinalpublicoetv.vercel.app/?id=premiere8", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-8.png"},
    {"name": "SporTV", "url": "https://sinalpublicoetv.vercel.app/?id=sportv", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportv.png"},
    {"name": "SporTV 2", "url": "https://sinalpublicoetv.vercel.app/?id=sportv2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportv-2.png"},
    {"name": "SporTV 3", "url": "https://sinalpublicoetv.vercel.app/?id=sportv3", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportv-3.png"},
    {"name": "SporTV 4", "url": "https://sinalpublicoetv.vercel.app/?id=sportv4", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportv-4.png"},
    {"name": "Sony Channel", "url": "https://sinalpublicoetv.vercel.app/?id=sony", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sony.png"},
    {"name": "Space", "url": "https://sinalpublicoetv.vercel.app/?id=space", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/space.png"},
    {"name": "Universal TV", "url": "https://sinalpublicoetv.vercel.app/?id=universaltv", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/universal.png"},
    {"name": "Warner TV", "url": "https://sinalpublicoetv.vercel.app/?id=warnerchannel", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/warner-channel.png"},
    {"name": "SBT", "url": "https://sinalpublicoetv.vercel.app/?id=sbt", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sbt.png"},
    {"name": "Record TV", "url": "https://sinalpublicoetv.vercel.app/?id=record", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/record-tv.png"}
]

def sniff_media_url(vercel_url):
    """
    Simula o comportamento da extensão MAX Video Downloader:
    Captura o link de vídeo real (m3u8/txt) dentro da página da Vercel.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://sinalpublicoetv.vercel.app/'
    }
    try:
        # Acessa a página para gerar a sessão e capturar o HTML
        resp_page = session.get(vercel_url, headers=headers, timeout=10)
        html = resp_page.text
        
        # 1. Procura por links diretos .m3u8 ou .txt da cloudfront
        match = re.search(r'(https://[^\s\'"]+cloudfront[^\s\'"]+\.(?:txt|m3u8)[^\s\'"]*)', html)
        if match: return match.group(1)
            
        # 2. Procura links escondidos em base64 (atob)
        base64_matches = re.findall(r'atob\([\'"]([a-zA-Z0-9+/=]+)[\'"]\)', html)
        for b in base64_matches:
            try:
                decoded = base64.b64decode(b).decode('utf-8')
                if 'http' in decoded and ('cloudfront' in decoded or '.m3u8' in decoded):
                    return decoded
            except: continue

        # 3. Fallback: Gera via lógica MD5
        channel_id = vercel_url.split('id=')[-1].split('&')[0]
        ch_hash = hashlib.md5(channel_id.encode()).hexdigest()
        return f"https://t5r4e3w2q1y0.s21-cloudfront-net.lat/test/{ch_hash}/file.txt"
    except: return None

@app.route('/')
def index():
    return "Farejador IPTV Ativo!"

@app.route('/lista.m3u')
def get_m3u():
    m3u = "#EXTM3U\n"
    host = request.host_url.rstrip('/')
    for ch in LINKS:
        # Link do nosso proxy farejador
        link_proxy = f"{host}/play.m3u8?u={ch['url']}"
        m3u += f'#EXTINF:-1 tvg-logo="{ch["logo"]}", {ch["name"]}\n{link_proxy}\n'
    return Response(m3u, mimetype='text/plain')

@app.route('/play.m3u8')
def proxy_handler():
    vercel_url = request.args.get('u')
    if not vercel_url: return "URL ausente", 400

    # FAREJA O LINK REAL NO MOMENTO DO ACESSO
    target_url = sniff_media_url(vercel_url)
    if not target_url: return "Link de vídeo não encontrado", 404

    try:
        # Puxa o manifesto do vídeo (file.txt / m3u8)
        resp = session.get(target_url, headers=HEADERS_BYPASS, timeout=15)
        
        # Tenta sem o /test/ se der erro
        if resp.status_code != 200 and "/test/" in target_url:
            target_url = target_url.replace("/test/", "/")
            resp = session.get(target_url, headers=HEADERS_BYPASS, timeout=15)

        if resp.status_code != 200: return f"Erro 403 no Cloudfront", 403

        # REESCREVE OS SEGMENTOS PARA PASSAR PELO PROXY
        parsed_uri = urlparse(target_url)
        domain_base = f"{parsed_uri.scheme}://{parsed_uri.netloc}"
        path_base = target_url.rsplit('/', 1)[0]
        host = request.host_url.rstrip('/')
        
        lines = resp.text.splitlines()
        new_lines = []
        for line in lines:
            line = line.strip()
            if not line: continue
            if not line.startswith("#"):
                # Corrige links relativos para absolutos
                if line.startswith("http"): full_url = line
                elif line.startswith("/"): full_url = domain_base + line
                else: full_url = path_base + "/" + line
                # Faz o pedaço passar pelo proxy de segmento para injetar os headers
                new_lines.append(f"{host}/segment?u={full_url}")
            else:
                new_lines.append(line)
        
        return Response("\n".join(new_lines), mimetype='application/vnd.apple.mpegurl')
    except Exception as e:
        return str(e), 500

@app.route('/segment')
def proxy_segment():
    target_url = request.args.get('u')
    try:
        # Repassa o pedaço do vídeo com cabeçalhos de segurança (libera o play)
        resp = session.get(target_url, headers=HEADERS_BYPASS, stream=True, timeout=15)
        return Response(resp.content, content_type=resp.headers.get('Content-Type', 'video/mp2t'))
    except:
        return "Erro no segmento", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
