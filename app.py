import requests
import re
import os
from flask import Flask, Response, request, redirect, render_template_string
from urllib.parse import quote

app = Flask(__name__)

# Configurações de Agente
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

def extrair_m3u8(url, referer):
    """ Tenta capturar o link .m3u8 no código fonte """
    try:
        headers = {"User-Agent": UA, "Referer": referer}
        res = requests.get(url, headers=headers, timeout=5)
        # Procura por link m3u8
        match = re.search(r'["\'](https?://[^\s"\']+?\.m3u8[^\s"\']*)["\']', res.text)
        if match:
            return match.group(1).replace("\\/", "/")
        # Procura por iframe
        iframe = re.search(r'<iframe.*?src=["\'](https?://.*?)["\']', res.text)
        if iframe and "google" not in iframe.group(1):
            return extrair_m3u8(iframe.group(1), url)
    except: pass
    return None

@app.route('/')
def home():
    return f"Playlist IPTV: {request.host_url}playlist.m3u"

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
                link = f"{host}/canal/s1/{cid}"
                m3u.append(f'#EXTINF:-1 tvg-logo="{c.get("image")}" group-title="S1", [S1] {c.get("name")}\n{link}')
    except: pass

    # S2 - Minha Tela
    try:
        headers_s2 = {"Referer": "https://minhatela.xyz/", "User-Agent": UA}
        r2 = requests.get("https://myapiplay.top/api/guiadejogos/epg.php", headers=headers_s2, timeout=10).json()
        for c in r2:
            cid = c.get('channelLogo')
            if cid:
                link = f"{host}/canal/s2/{cid}"
                m3u.append(f'#EXTINF:-1 tvg-logo="{c.get("logo")}" group-title="S2", [S2] {c.get("name")}\n{link}')
    except: pass

    return Response("\n".join(m3u), mimetype='text/plain')

@app.route('/canal/<source>/<cid>')
def play(source, cid):
    """ Tenta capturar o sinal real, mas tem links de reserva caso falhe """
    stream_url = None
    ref = ""

    if source == 's1':
        # Tenta varrer o player oficial do Sinal Público
        player_url = f"https://sinalpublicoetv.vercel.app/?id={cid}"
        stream_url = extrair_m3u8(player_url, "https://sinalpublic.vercel.app/")
        ref = "https://sinaldvd.github.io/"
        
        # --- SE FALHAR, USA O RESERVA (FALLBACK) ---
        if not stream_url:
            # Esses domínios mudam, mas o padrão é mantido
            stream_url = f"https://t5r4e3w2q1y0-cloudflare-net.vercel.app/{cid}.m3u8"
    
    elif source == 's2':
        # Tenta varrer o player do Minha Tela
        player_url = f"https://meuplayeronlinehd.com/myplay/watch.html?id={cid}"
        stream_url = extrair_m3u8(player_url, "https://minhatela.xyz/")
        ref = "https://minhatela.xyz/"
        
        # --- SE FALHAR, USA O RESERVA (FALLBACK) ---
        if not stream_url:
            stream_url = f"https://meuplayeronlinehd.com/hls/{cid}.m3u8"

    # Se mesmo com fallback não temos link, tenta o player direto
    final_url = stream_url if stream_url else player_url
    
    # Adiciona os cabeçalhos que os players (TiviMate/VLC) precisam
    final_with_headers = f"{final_url}|User-Agent={quote(UA)}&Referer={quote(ref)}&Origin={quote(ref)}"
    
    return redirect(final_with_headers)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
