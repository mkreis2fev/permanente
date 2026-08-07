import requests
import re
import os
import base64
from flask import Flask, Response, request, render_template_string
from urllib.parse import urljoin

app = Flask(__name__)

# Configurações de Navegação para burlar bloqueios
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

def get_headers(source):
    """ Retorna os cabeçalhos exatos que cada site exige """
    if source == 's1':
        return {
            "User-Agent": UA,
            "Referer": "https://sinaldvd.github.io/",
            "Origin": "https://sinaldvd.github.io"
        }
    else:
        return {
            "User-Agent": UA,
            "Referer": "https://minhatela.xyz/",
            "Origin": "https://minhatela.xyz"
        }

def buscar_link_m3u8(url, referer):
    """ Entra na página e varre o código fonte atrás do sinal .m3u8 """
    try:
        res = requests.get(url, headers={"User-Agent": UA, "Referer": referer}, timeout=8)
        # Procura link de vídeo no HTML ou JavaScript
        match = re.search(r'["\'](https?://[^\s"\']+?\.m3u8[^\s"\']*)["\']', res.text)
        if match:
            return match.group(1).replace("\\/", "/")
        # Se houver iframe, entra nele (Recursivo)
        iframe = re.search(r'<iframe.*?src=["\'](https?://.*?)["\']', res.text)
        if iframe and "google" not in iframe.group(1):
            return buscar_link_m3u8(iframe.group(1), url)
    except: pass
    return None

@app.route('/')
def home():
    return f"Playlist Ativa: {request.host_url}playlist.m3u"

@app.route('/playlist.m3u')
def playlist():
    host = request.host_url.rstrip('/')
    m3u = ["#EXTM3U"]
    # S1 - Sinal Público
    try:
        r1 = requests.get("https://apisinalpublico.vercel.app/canais.json", timeout=10).json()
        for c in r1:
            cid = c.get('url', '').split('=')[-1]
            m3u.append(f'#EXTINF:-1 tvg-logo="{c.get("image")}" group-title="S1", [S1] {c.get("name")}\n{host}/m3u8/s1/{cid}.m3u8')
    except: pass
    # S2 - Minha Tela
    try:
        h2 = {"Referer": "https://minhatela.xyz/", "User-Agent": UA}
        r2 = requests.get("https://myapiplay.top/api/guiadejogos/epg.php", headers=h2, timeout=10).json()
        for c in r2:
            cid = c.get('channelLogo')
            if cid:
                m3u.append(f'#EXTINF:-1 tvg-logo="{c.get("logo")}" group-title="S2", [S2] {c.get("name")}\n{host}/m3u8/s2/{cid}.m3u8')
    except: pass
    return Response("\n".join(m3u), mimetype='text/plain')

@app.route('/m3u8/<source>/<cid>.m3u8')
def proxy_m3u8(source, cid):
    """ Proxy que lê o conteúdo do vídeo e reescreve os caminhos """
    target = ""
    if source == 's1':
        target = f"https://t5r4e3w2q1y0-cloudflare-net.vercel.app/{cid}.m3u8"
    else:
        url_p = f"https://meuplayeronlinehd.com/myplay/watch.html?id={cid}"
        target = buscar_link_m3u8(url_p, "https://minhatela.xyz/") or f"https://meuplayeronlinehd.com/hls/{cid}.m3u8"

    try:
        headers = get_headers(source)
        res = requests.get(target, headers=headers, timeout=10, allow_redirects=True)
        if res.status_code != 200 and source == 's1': # Tenta servidor reserva do S1
            target = f"https://a9b8c7d6e5f4-cloudflare-net.vercel.app/{cid}.m3u8"
            res = requests.get(target, headers=headers, timeout=10)
        
        # Reescreve as URLs internas para passarem pelo nosso proxy
        lines = res.text.splitlines()
        new_lines = []
        base_path = res.url.rsplit('/', 1)[0] + '/'
        
        for line in lines:
            if not line.strip() or line.startswith('#'):
                new_lines.append(line)
            else:
                full_url = urljoin(base_path, line.strip())
                b64_url = base64.urlsafe_b64encode(full_url.encode()).decode()
                new_lines.append(f"{request.host_url.rstrip('/')}/ts?u={b64_url}&s={source}")
        
        return Response("\n".join(new_lines), mimetype='application/vnd.apple.mpegurl')
    except:
        return "Erro ao carregar stream", 404

@app.route('/ts')
def proxy_ts():
    """ O 'Túnel' de vídeo real que engana as proteções """
    try:
        url = base64.urlsafe_b64decode(request.args.get('u')).decode()
        source = request.args.get('s')
        res = requests.get(url, headers=get_headers(source), stream=True, timeout=15)
        return Response(res.iter_content(chunk_size=1024*64), content_type=res.headers.get('Content-Type'))
    except:
        return "", 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
