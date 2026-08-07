import requests
import re
import os
from flask import Flask, Response, request, redirect, render_template_string
from urllib.parse import quote

app = Flask(__name__)

# User-Agent oficial para evitar bloqueios do Cloudflare/Vercel
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

def buscar_sinal_real(url, referer):
    """ Entra no player e 'caça' o link .m3u8 real """
    try:
        headers = {"User-Agent": UA, "Referer": referer}
        res = requests.get(url, headers=headers, timeout=8)
        # Procura por links .m3u8 no código
        match = re.search(r'["\'](https?://[^\s"\']+?\.m3u8[^\s"\']*)["\']', res.text)
        if match:
            return match.group(1).replace("\\/", "/")
        # Se houver iframe, entra nele
        iframe = re.search(r'<iframe.*?src=["\'](https?://.*?)["\']', res.text)
        if iframe and "google" not in iframe.group(1):
            return buscar_sinal_real(iframe.group(1), url)
    except: pass
    return None

@app.route('/')
def home():
    return f"Servidor IPTV Ativo: {request.host_url}playlist.m3u"

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
                link = f"{host}/resolve/s1/{cid}"
                m3u.append(f'#EXTINF:-1 tvg-logo="{c.get("image")}" group-title="S1", [S1] {c.get("name")}\n{link}')
    except: pass

    # S2 - Minha Tela
    try:
        headers_s2 = {"Referer": "https://minhatela.xyz/", "User-Agent": UA}
        r2 = requests.get("https://myapiplay.top/api/guiadejogos/epg.php", headers=headers_s2, timeout=10).json()
        for c in r2:
            cid = c.get('channelLogo')
            if cid:
                link = f"{host}/resolve/s2/{cid}"
                m3u.append(f'#EXTINF:-1 tvg-logo="{c.get("logo")}" group-title="S2", [S2] {c.get("name")}\n{link}')
    except: pass

    return Response("\n".join(m3u), mimetype='text/plain')

@app.route('/resolve/<source>/<cid>')
def resolve(source, cid):
    """ Busca o link do momento e redireciona com headers """
    stream_url = ""
    ref = ""

    if source == 's1':
        # S1 - Tenta encontrar o link na página que abre 'na própria página'
        player_page = f"https://sinalpublicoetv.vercel.app/?id={cid}"
        stream_url = buscar_sinal_real(player_page, "https://sinalpublic.vercel.app/")
        ref = "https://sinaldvd.github.io/"
        # Fallback se não encontrar dinamicamente
        if not stream_url:
            stream_url = f"https://t5r4e3w2q1y0-cloudflare-net.vercel.app/{cid}.m3u8"
    else:
        # S2 - Minha Tela (abre em nova página)
        player_page = f"https://meuplayeronlinehd.com/myplay/watch.html?id={cid}"
        stream_url = buscar_sinal_real(player_page, "https://minhatela.xyz/")
        ref = "https://minhatela.xyz/"
        if not stream_url:
            stream_url = f"https://meuplayeronlinehd.com/hls/{cid}.m3u8"

    if stream_url:
        # Formato que o TiviMate e VLC usam para passar os headers de segurança
        final_url = f"{stream_url}|User-Agent={quote(UA)}&Referer={quote(ref)}&Origin={quote(ref)}"
        return redirect(final_url)
    
    return "Não foi possível capturar o sinal", 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
