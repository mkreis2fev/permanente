from flask import Flask, jsonify, request, Response
import requests
import os
from urllib.parse import urlparse
import hashlib

app = Flask(__name__)

# TESTE COM APENAS 3 CANAIS PARA VER SE LIGA
CHANNELS_DATA = [
    {"name":"Globo News","id":"globonews","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globonews.png"},
    {"name":"Globo SP","id":"globosp","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name":"ESPN","id":"espn","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/espn.png"}
]

@app.route('/')
def index():
    return "Servidor TV Online ATIVO!"

@app.route('/lista.m3u')
def get_m3u():
    m3u = "#EXTM3U\n"
    # Pega o link do seu site automaticamente
    base = request.host_url.rstrip('/')
    for ch in CHANNELS_DATA:
        ch_hash = hashlib.md5(ch["id"].encode()).hexdigest()
        video_url = f"https://t5r4e3w2q1y0.s21-cloudfront-net.lat/test/{ch_hash}/file.txt"
        link_proxy = f"{base}/play.m3u8?u={video_url}"
        m3u += f'#EXTINF:-1 tvg-logo="{ch["logo"]}", {ch["name"]}\n{link_proxy}\n'
    return Response(m3u, mimetype='text/plain')

@app.route('/play.m3u8')
def proxy_handler():
    target_url = request.args.get('u')
    if not target_url: return "URL ausente", 400

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Referer': 'https://t5r4e3w2q1y0-cloudflare-net.vercel.app/',
        'Origin': 'https://t5r4e3w2q1y0-cloudflare-net.vercel.app'
    }

    try:
        # Tenta carregar o vídeo
        resp = requests.get(target_url, headers=headers, timeout=10)

        # Se falhar, tenta sem o /test/
        if resp.status_code != 200:
             target_url = target_url.replace("/test/", "/")
             resp = requests.get(target_url, headers=headers, timeout=10)

        domain_base = f"{urlparse(target_url).scheme}://{urlparse(target_url).netloc}"

        lines = resp.text.splitlines()
        new_lines = []
        for line in lines:
            line = line.strip()
            if not line: continue
            if line.startswith("/") and not line.startswith("//"):
                new_lines.append(domain_base + line)
            elif line and not line.startswith("#") and not line.startswith("http"):
                path_base = target_url.rsplit('/', 1)[0]
                new_lines.append(path_base + "/" + line)
            else:
                new_lines.append(line)

        return Response("\n".join(new_lines), mimetype='application/vnd.apple.mpegurl')
    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
