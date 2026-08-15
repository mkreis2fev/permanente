from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import requests
import re
import os
from urllib.parse import urlparse
import hashlib

app = Flask(__name__)
CORS(app)

# CONFIGURAÇÃO DE SEGURANÇA (PARA EVITAR O ERRO 403)
HEADERS_BYPASS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Referer': 'https://t5r4e3w2q1y0-cloudflare-net.vercel.app/',
    'Origin': 'https://t5r4e3w2q1y0-cloudflare-net.vercel.app',
    'Accept': '*/*',
    'Connection': 'keep-alive'
}

# Lista completa de canais
LINKS = [
    {"name": "Globo News", "id": "globonews", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globonews.png"},
    {"name": "Globo RJ", "id": "globorj", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name": "Globo MG", "id": "globomg", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name": "Globo SP", "id": "globosp", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name": "Globo PE", "id": "globope", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name": "Globo PB", "id": "globopb", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name": "Globo RS", "id": "globors", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name": "Globo ES", "id": "globoes", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name": "Globo AM", "id": "globoam", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name": "Globo CE", "id": "globoce", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name": "SportyNet", "id": "sportynet", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportynet.png"},
    {"name": "SportyNet+ 1", "id": "sportynetplus1", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportynet.png"},
    {"name": "SportyNet+ 2", "id": "sportynetplus2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportynet.png"},
    {"name": "SportyNet+ 3", "id": "sportynetplus3", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportynet.png"},
    {"name": "Paramount+ 1", "id": "paramountplus1", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/paramountplus.png"},
    {"name": "Paramount+ 2", "id": "paramountplus2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/paramountplus.png"},
    {"name": "Paramount+ 3", "id": "paramountplus3", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/paramountplus.png"},
    {"name": "MAX 1", "id": "max1", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/max.png"},
    {"name": "MAX 2", "id": "max2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/max.png"},
    {"name": "MAX 3", "id": "max3", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/max.png"},
    {"name": "Cazé TV 1", "id": "caze1", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/cazetv.png"},
    {"name": "Cazé TV 2", "id": "caze2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/cazetv.png"},
    {"name": "Cazé TV 3", "id": "caze3", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/cazetv.png"},
    {"name": "Disney+ 1", "id": "disneyplus1", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/disneyplus.png"},
    {"name": "Disney+ 2", "id": "disneyplus2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/disneyplus.png"},
    {"name": "Disney+ 3", "id": "disneyplus3", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/disneyplus.png"},
    {"name": "Prime Video 1", "id": "primevideo", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/prime-video.png"},
    {"name": "Prime Video 2", "id": "primevideo2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/prime-video.png"},
    {"name": "Prime Video 3", "id": "primevideo3", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/prime-video.png"},
    {"name": "Prime Video 4", "id": "primevideo4", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/prime-video.png"},
    {"name": "ESPN", "id": "espn", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/espn.png"},
    {"name": "ESPN 2", "id": "espn2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/espn-2.png"},
    {"name": "ESPN 3", "id": "espn3", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/espn-3.png"},
    {"name": "ESPN 4", "id": "espn4", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/espn-4.png"},
    {"name": "ESPN 5", "id": "espn5", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/espn-5.png"},
    {"name": "ESPN 6", "id": "espn6", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/espn-6.png"},
    {"name": "Ge TV", "id": "getv", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/ge-tv.png"},
    {"name": "Band Sports", "id": "bandsports", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/band-sports.png"},
    {"name": "Combate", "id": "combate", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/combate.png"},
    {"name": "Premiere Clubes", "id": "premiere", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere.png"},
    {"name": "Premiere 2", "id": "premiere2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-2.png"},
    {"name": "Premiere 3", "id": "premiere3", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-3.png"},
    {"name": "Premiere 4", "id": "premiere4", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-4.png"},
    {"name": "Premiere 5", "id": "premiere5", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-5.png"},
    {"name": "Premiere 6", "id": "premiere6", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-6.png"},
    {"name": "Premiere 7", "id": "premiere7", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-7.png"},
    {"name": "Premiere 8", "id": "premiere8", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-8.png"},
    {"name": "SporTV", "id": "sportv", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportv.png"},
    {"name": "SporTV 2", "id": "sportv2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportv-2.png"},
    {"name": "SporTV 3", "id": "sportv3", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportv-3.png"},
    {"name": "SporTV 4", "id": "sportv4", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportv-4.png"}
]

@app.route('/')
def index():
    return "Servidor IPTV Ativo! Link: /lista.m3u"

@app.route('/lista.m3u')
def get_m3u():
    m3u = "#EXTM3U\n"
    host = request.host_url.rstrip('/')
    for ch in LINKS:
        # Geramos o link de vídeo a partir do ID via MD5
        ch_hash = hashlib.md5(ch["id"].encode()).hexdigest()
        # O link do arquivo de sinal real
        target_file = f"https://t5r4e3w2q1y0.s21-cloudfront-net.lat/test/{ch_hash}/file.txt"
        # Link que passa pelo nosso proxy principal
        link_proxy = f"{host}/play.m3u8?u={target_file}"
        m3u += f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-logo="{ch["logo"]}", {ch["name"]}\n{link_proxy}\n'
    return Response(m3u, mimetype='text/plain')

@app.route('/play.m3u8')
def proxy_main():
    target_url = request.args.get('u')
    if not target_url: return "URL ausente", 400

    try:
        # 1. Busca o conteúdo do file.txt (o manifesto do vídeo)
        resp = requests.get(target_url, headers=HEADERS_BYPASS, timeout=10)
        
        # Fallback se a pasta /test/ não existir
        if resp.status_code != 200 and "/test/" in target_url:
            target_url = target_url.replace("/test/", "/")
            resp = requests.get(target_url, headers=HEADERS_BYPASS, timeout=10)

        if resp.status_code != 200:
            return f"Erro Cloudfront: {resp.status_code}", resp.status_code

        # 2. Corrige os links internos para que também passem pelo proxy
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
                if line.startswith("http"):
                    full_url = line
                elif line.startswith("/"):
                    full_url = domain_base + line
                else:
                    full_url = path_base + "/" + line
                # Redireciona cada pedaço do vídeo para nossa rota /segment para injetar os headers
                new_lines.append(f"{host}/segment?u={full_url}")
            else:
                new_lines.append(line)
        
        return Response("\n".join(new_lines), mimetype='application/vnd.apple.mpegurl')
    except Exception as e:
        return str(e), 500

@app.route('/segment')
def proxy_segment():
    target_url = request.args.get('u')
    if not target_url: return "URL ausente", 400
    
    try:
        # Injeta os cabeçalhos de bypass em cada pedaço (segmento) do vídeo
        resp = requests.get(target_url, headers=HEADERS_BYPASS, stream=True, timeout=15)
        return Response(resp.content, content_type=resp.headers.get('Content-Type', 'video/mp2t'))
    except:
        return "Erro no segmento", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
