import requests
import re
import os
import base64
from flask import Flask, Response, request, render_template_string
from urllib.parse import urljoin

app = Flask(__name__)

# Configurações de Navegação
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

def get_headers(source):
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

def buscar_m3u8(url, ref):
    """ Varredor de links m3u8 dentro de players HTML """
    try:
        res = requests.get(url, headers={"User-Agent": UA, "Referer": ref}, timeout=7)
        # 1. Tenta achar link direto
        match = re.search(r'["\'](https?://[^\s"\']+?\.m3u8[^\s"\']*)["\']', res.text)
        if match:
            return match.group(1).replace("\\/", "/")
        # 2. Tenta entrar em iframes
        iframe = re.search(r'<iframe.*?src=["\'](https?://.*?)["\']', res.text)
        if iframe and "google" not in iframe.group(1):
            return buscar_m3u8(iframe.group(1), url)
    except: pass
    return None

@app.route('/')
def home():
    return f"Playlist para TiviMate: {request.host_url}playlist.m3u"

@app.route('/playlist.m3u')
def playlist():
    host = request.host_url.rstrip('/')
    m3u = ["#EXTM3U"]
    
    # S1 - Sinal Público
    try:
        r1 = requests.get("https://apisinalpublico.vercel.app/canais.json", timeout=10).json()
        for c in r1:
            cid = c.get('url', '').split('=')[-1]
            if cid:
                link = f"{host}/stream/s1/{cid}.m3u8"
                m3u.append(f'#EXTINF:-1 tvg-logo="{c.get("image")}" group-title="S1", [S1] {c.get("name")}\n{link}')
    except: pass

    # S2 - Minha Tela
    try:
        h2 = {"Referer": "https://minhatela.xyz/", "User-Agent": UA}
        r2 = requests.get("https://myapiplay.top/api/guiadejogos/epg.php", headers=h2, timeout=10).json()
        for c in r2:
            cid = c.get('channelLogo')
            if cid:
                link = f"{host}/stream/s2/{cid}.m3u8"
                m3u.append(f'#EXTINF:-1 tvg-logo="{c.get("logo")}" group-title="S2", [S2] {c.get("name")}\n{link}')
    except: pass

    return Response("\n".join(m3u), mimetype='text/plain')

@app.route('/stream/<source>/<cid>.m3u8')
def m3u8_proxy(source, cid):
    """ Proxy para o arquivo de manifesto """
    target = ""
    ref = ""
    
    if source == 's1':
        # Fonte direta S1 (Vercel)
        target = f"https://t5r4e3w2q1y0-cloudflare-net.vercel.app/{cid}.m3u8"
        ref = "https://sinaldvd.github.io/"
    else:
        # Busca dinâmica para S2
        url_p = f"https://meuplayeronlinehd.com/myplay/watch.html?id={cid}"
        target = buscar_m3u8(url_p, "https://minhatela.xyz/")
        ref = "https://minhatela.xyz/"

    if not target:
        return "Canal não encontrado", 404

    try:
        headers = get_headers(source)
        res = requests.get(target, headers=headers, timeout=10, allow_redirects=True)
        
        lines = res.text.splitlines()
        new_lines = []
        # Importante: Base URL para resolver links relativos
        base_url = res.url.rsplit('/', 1)[0] + '/'
        
        for line in lines:
            line = line.strip()
            if not line: continue
            if line.startswith('#'):
                new_lines.append(line)
            else:
                # Resolve URL completa do segmento
                full_url = urljoin(base_url, line)
                # Codifica para o proxy
                b64_url = base64.urlsafe_b64encode(full_url.encode()).decode()
                b64_ref = base64.urlsafe_b64encode(ref.encode()).decode()
                new_lines.append(f"{request.host_url.rstrip('/')}/ts?u={b64_url}&r={b64_ref}&s={source}")
        
        return Response("\n".join(new_lines), mimetype='application/vnd.apple.mpegurl')
    except Exception as e:
        print(f"Erro no Proxy M3U8: {e}")
        return "Erro Interno", 500

@app.route('/ts')
def proxy_ts():
    """ Túnel binário para os dados de vídeo """
    try:
        url = base64.urlsafe_b64decode(request.args.get('u')).decode()
        ref = base64.urlsafe_b64decode(request.args.get('r')).decode()
        source = request.args.get('s')
        
        headers = {"User-Agent": UA, "Referer": ref}
        res = requests.get(url, headers=headers, stream=True, timeout=15)
        
        return Response(res.iter_content(chunk_size=1024*64), content_type=res.headers.get('Content-Type'))
    except:
        return "", 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
