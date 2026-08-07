import requests
import re
import os
import base64
from flask import Flask, Response, request, render_template_string
from urllib.parse import urljoin

app = Flask(__name__)

# Cabeçalhos de Navegador Real
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

def get_headers(source):
    if source == 's1':
        return {"User-Agent": UA, "Referer": "https://sinaldvd.github.io/", "Origin": "https://sinaldvd.github.io"}
    else:
        return {"User-Agent": UA, "Referer": "https://minhatela.xyz/", "Origin": "https://minhatela.xyz"}

def buscar_m3u8(url, ref):
    """ Tenta encontrar o link .m3u8 dentro do HTML do player """
    try:
        res = requests.get(url, headers={"User-Agent": UA, "Referer": ref}, timeout=5)
        # Busca link .m3u8
        match = re.search(r'["\'](https?://[^\s"\']+?\.m3u8[^\s"\']*)["\']', res.text)
        if match:
            return match.group(1).replace("\\/", "/")
        # Busca em iframe
        iframe = re.search(r'<iframe.*?src=["\'](https?://.*?)["\']', res.text)
        if iframe:
            return buscar_m3u8(iframe.group(1), url)
    except: pass
    return None

@app.route('/')
def home():
    return f"Playlist: {request.host_url}playlist.m3u"

@app.route('/playlist.m3u')
def playlist():
    host = request.host_url.rstrip('/')
    m3u = ["#EXTM3U"]
    
    # S1 - Captura Sinal Público
    try:
        r = requests.get("https://apisinalpublico.vercel.app/canais.json", timeout=10).json()
        for c in r:
            cid = c.get('url').split('=')[-1]
            m3u.append(f'#EXTINF:-1 tvg-logo="{c.get("image")}" group-title="S1", [S1] {c.get("name")}')
            m3u.append(f'{host}/stream/s1/{cid}.m3u8')
    except: pass

    # S2 - Captura Minha Tela
    try:
        h2 = {"Referer": "https://minhatela.xyz/", "User-Agent": UA}
        r = requests.get("https://myapiplay.top/api/guiadejogos/epg.php", headers=h2, timeout=10).json()
        for c in r:
            if c.get('channelLogo'):
                m3u.append(f'#EXTINF:-1 tvg-logo="{c.get("logo")}" group-title="S2", [S2] {c.get("name")}')
                m3u.append(f'{host}/stream/s2/{c.get("channelLogo")}.m3u8')
    except: pass

    return Response("\n".join(m3u), mimetype='text/plain')

@app.route('/stream/<source>/<cid>.m3u8')
def m3u8_proxy(source, cid):
    """ Baixa o m3u8 original e altera os links para passarem pelo nosso proxy """
    target = ""
    ref = ""
    
    if source == 's1':
        # Tenta o servidor padrão do S1
        target = f"https://t5r4e3w2q1y0-cloudflare-net.vercel.app/{cid}.m3u8"
        ref = "https://sinaldvd.github.io/"
    else:
        # Varre o player do S2 para achar o sinal
        url_p = f"https://meuplayeronlinehd.com/myplay/watch.html?id={cid}"
        target = buscar_m3u8(url_p, "https://minhatela.xyz/")
        ref = "https://minhatela.xyz/"

    if not target: return "Erro ao localizar sinal", 404

    try:
        res = requests.get(target, headers=get_headers(source), timeout=10)
        content = res.text
        base_url = res.url.rsplit('/', 1)[0] + '/'
        
        # Reescreve o M3U8 para que cada pedaço de vídeo (.ts) passe pelo nosso servidor
        new_lines = []
        for line in content.splitlines():
            if line.startswith('#') or not line.strip():
                new_lines.append(line)
            else:
                full_url = urljoin(base_path, line.strip())
                b64_url = base64.urlsafe_b64encode(full_url.encode()).decode()
                new_lines.append(f"{request.host_url.rstrip('/')}/chunk.ts?u={b64_url}&s={source}")
        
        return Response("\n".join(new_lines), mimetype='application/vnd.apple.mpegurl')
    except:
        return "Erro no Proxy", 500

@app.route('/chunk.ts')
def proxy_ts():
    """ Baixa o pedaço do vídeo e entrega ao VLC com os headers certos """
    url = base64.urlsafe_b64decode(request.args.get('u')).decode()
    source = request.args.get('s')
    try:
        res = requests.get(url, headers=get_headers(source), stream=True, timeout=15)
        return Response(res.iter_content(chunk_size=1024*10), content_type=res.headers.get('Content-Type'))
    except:
        return "", 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
