import requests
import re
import os
import base64
from flask import Flask, Response, request, redirect, render_template_string
from urllib.parse import urljoin, quote

app = Flask(__name__)

# User-Agent robusto para evitar bloqueios
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

def extrair_m3u8_real(url_player, referer):
    """ Tenta encontrar o link .m3u8 real dentro do player """
    try:
        headers = {"User-Agent": UA, "Referer": referer, "Origin": referer}
        response = requests.get(url_player, headers=headers, timeout=5)
        html = response.text
        
        # 1. Procura por links .m3u8 no código
        links = re.findall(r'["\'](https?://[^\s"\']+?\.m3u8[^\s"\']*)["\']', html)
        if links:
            return links[0].replace("\\/", "/")
            
        # 2. Procura em iframes (recursivo)
        iframe = re.search(r'<iframe.*?src=["\'](https?://.*?)["\']', html)
        if iframe:
            return extrair_m3u8_real(iframe.group(1), url_player)
    except:
        pass
    return None

@app.route('/')
def index():
    return render_template_string("""
        <body style="font-family:sans-serif; background:#000; color:#fff; text-align:center; padding:100px;">
            <h1 style="color:#00c8ff;">S1 & S2 IPTV PROXY</h1>
            <p>Copie este link no seu App (OTT Navigator / Televizo / VLC):</p>
            <input type="text" value="{{ host }}playlist.m3u" style="width:80%; padding:10px; background:#222; color:#0f0; border:1px solid #444; text-align:center;">
        </body>
    """, host=request.host_url)

@app.route('/playlist.m3u')
def playlist():
    host = request.host_url.rstrip('/')
    m3u = ["#EXTM3U"]
    
    # S1 - Sinal Público
    try:
        r = requests.get("https://apisinalpublico.vercel.app/canais.json", timeout=5)
        for c in r.json():
            cid = c.get('url').split('=')[-1]
            m3u.append(f'#EXTINF:-1 tvg-logo="{c.get("image")}" group-title="S1", [S1] {c.get("name")}')
            m3u.append(f'{host}/play?s=s1&id={cid}')
    except: pass

    # S2 - Minha Tela
    try:
        headers = {"Referer": "https://minhatela.xyz/", "User-Agent": UA}
        r = requests.get("https://myapiplay.top/api/guiadejogos/epg.php", headers=headers, timeout=5)
        for c in r.json():
            if c.get('channelLogo'):
                m3u.append(f'#EXTINF:-1 tvg-logo="{c.get("logo")}" group-title="S2", [S2] {c.get("name")}')
                m3u.append(f'{host}/play?s=s2&id={c.get("channelLogo")}')
    except: pass

    return Response("\n".join(m3u), mimetype='text/plain')

@app.route('/play')
def play():
    source = request.args.get('s')
    cid = request.args.get('id')
    
    if source == 's1':
        # Fonte do Sinal Público costuma usar esses domínios dinâmicos
        # Tentamos o resolvedor mas deixamos o link direto como fallback
        player_url = f"https://sinaldvd.github.io/tv/player.html?id={cid}"
        m3u8 = extrair_m3u8_real(player_url, "https://sinalpublicoetv.vercel.app/")
        if not m3u8:
            m3u8 = f"https://t5r4e3w2q1y0-cloudflare-net.vercel.app/{cid}.m3u8"
        
        return redirect(f"{m3u8}|Referer=https://sinaldvd.github.io/&User-Agent={UA}")

    elif source == 's2':
        # Fonte do Minha Tela
        player_url = f"https://meuplayeronlinehd.com/myplay/watch.html?id={cid}"
        m3u8 = extrair_m3u8_real(player_url, "https://minhatela.xyz/")
        if not m3u8:
            return redirect(player_url) # Se falhar, manda pro player original
            
        return redirect(f"{m3u8}|Referer={player_url}&User-Agent={UA}")

    return "Erro", 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
