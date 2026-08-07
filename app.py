import requests
import re
import os
import base64
from flask import Flask, Response, request, render_template_string
from urllib.parse import urljoin

app = Flask(__name__)

# Configurações de Navegação
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

def get_proxied_headers(referer):
    return {
        "User-Agent": UA,
        "Referer": referer,
        "Origin": re.search(r'https?://[^/]+', referer).group(0) if referer else "",
        "Accept": "*/*"
    }

def scrape_m3u8(url, referer):
    try:
        headers = {"User-Agent": UA, "Referer": referer}
        res = requests.get(url, headers=headers, timeout=10)
        matches = re.findall(r'["\'](https?://[^\s"\']+?\.m3u8[^\s"\']*)["\']', res.text)
        if matches:
            return matches[0].replace("\\/", "/")
        iframe = re.search(r'<iframe.*?src=["\'](https?://.*?)["\']', res.text)
        if iframe:
            return scrape_m3u8(iframe.group(1), url)
    except: pass
    return None

@app.route('/')
def home():
    return render_template_string("""
        <body style="font-family:sans-serif; background:#0f172a; color:white; text-align:center; padding:50px;">
            <h1 style="color:#3b82f6;">📡 Servidor IPTV S1 & S2 (Proxy On)</h1>
            <div style="background:#1e293b; padding:20px; border-radius:10px; border:1px solid #334155; display:inline-block;">
                Link da Playlist para o App:<br>
                <code style="color:#10b981; font-size:1.2em;">{{ host }}playlist.m3u</code>
            </div>
        </body>
    """, host=request.host_url)

@app.route('/playlist.m3u')
def playlist():
    host = request.host_url.rstrip('/')
    lines = ["#EXTM3U"]
    # S1 - Sinal Público
    try:
        r1 = requests.get("https://apisinalpublico.vercel.app/canais.json", timeout=10)
        for c in r1.json():
            cid = c.get('url').split('=')[-1]
            link = f"{host}/hls/s1/{cid}.m3u8"
            lines.append(f'#EXTINF:-1 tvg-logo="{c.get("image")}" group-title="S1", [S1] {c.get("name")}\n{link}')
    except: pass
    # S2 - Minha Tela
    try:
        h2 = {"Referer": "https://minhatela.xyz/", "User-Agent": UA}
        r2 = requests.get("https://myapiplay.top/api/guiadejogos/epg.php", headers=h2, timeout=10)
        for c in r2.json():
            if c.get('channelLogo'):
                link = f"{host}/hls/s2/{c.get('channelLogo')}.m3u8"
                lines.append(f'#EXTINF:-1 tvg-logo="{c.get("logo")}" group-title="S2", [S2] {c.get("name")}\n{link}')
    except: pass
    return Response("\n".join(lines), mimetype='text/plain')

@app.route('/hls/<source>/<cid>.m3u8')
def m3u8_proxy(source, cid):
    target_url, ref = None, ""
    if source == 's1':
        target_url = f"https://t5r4e3w2q1y0-cloudflare-net.vercel.app/{cid}.m3u8"
        ref = "https://sinaldvd.github.io/"
    else:
        player_page = f"https://meuplayeronlinehd.com/myplay/watch.html?id={cid}"
        target_url = scrape_m3u8(player_page, "https://minhatela.xyz/")
        ref = player_page

    if not target_url: return "Canal não resolvido", 404

    try:
        res = requests.get(target_url, headers=get_proxied_headers(ref), timeout=10)
        content = res.text
        base_path = res.url.rsplit('/', 1)[0] + '/'
        new_content = []
        for line in content.splitlines():
            if line.startswith('#') or not line.strip():
                new_content.append(line)
            else:
                full_url = urljoin(base_path, line.strip())
                b64_url = base64.urlsafe_b64encode(full_url.encode()).decode()
                b64_ref = base64.urlsafe_b64encode(ref.encode()).decode()
                new_content.append(f"{request.host_url.rstrip('/')}/proxy?u={b64_url}&r={b64_ref}")
        return Response("\n".join(new_content), mimetype='application/vnd.apple.mpegurl')
    except: return "Erro ao processar stream", 500

@app.route('/proxy')
def proxy():
    try:
        url = base64.urlsafe_b64decode(request.args.get('u')).decode()
        ref = base64.urlsafe_b64decode(request.args.get('r')).decode()
        res = requests.get(url, headers=get_proxied_headers(ref), stream=True, timeout=15)
        return Response(res.iter_content(chunk_size=1024*10), content_type=res.headers.get('Content-Type'))
    except: return "Erro no Proxy", 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
