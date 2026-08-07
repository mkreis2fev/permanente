import requests
import re
import os
from flask import Flask, Response, request, render_template_string, redirect

app = Flask(__name__)

# Configurações de Navegação
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

def extrair_m3u8(url, referer):
    """ Entra na página do player e caça o link .m3u8 real """
    try:
        headers = {"User-Agent": UA, "Referer": referer}
        response = requests.get(url, headers=headers, timeout=10)
        html = response.text
        
        # Procura por links .m3u8 no código-fonte
        # Padrão para capturar links de vídeo HLS
        matches = re.findall(r'["\'](https?://[^\s"\']+?\.m3u8[^\s"\']*)["\']', html)
        
        if matches:
            link = matches[0].replace("\\/", "/")
            # Retorna o link com o comando de Referer que Apps IPTV (OTT/Smarters) entendem
            return f"{link}|Referer={url}&User-Agent={UA}"
            
        # Busca recursiva em iframes
        iframe = re.search(r'<iframe.*?src=["\'](https?://.*?)["\']', html)
        if iframe:
            iframe_url = iframe.group(1)
            if "google" not in iframe_url:
                return extrair_m3u8(iframe_url, url)
    except:
        pass
    return None

@app.route('/')
def home():
    host = request.host_url
    return render_template_string("""
        <body style="font-family:sans-serif; background:#0f172a; color:white; text-align:center; padding:50px;">
            <h1 style="color:#3b82f6;">Agregador IPTV S1 & S2</h1>
            <div style="background:#1e293b; padding:20px; border-radius:10px; border:1px solid #334155; display:inline-block;">
                <p>Link da sua Playlist M3U:</p>
                <code style="color:#10b981; font-size:1.2em;">{{ host }}playlist.m3u</code>
            </div>
            <p style="margin-top:20px; color:#64748b;">S1: Sinal Público | S2: Minha Tela</p>
        </body>
    """, host=host)

@app.route('/playlist.m3u')
def playlist():
    """ Gera a playlist unificada para o App IPTV """
    channels = ["#EXTM3U"]
    base_url = request.host_url.rstrip('/')

    # --- S1: Sinal Público ---
    try:
        r1 = requests.get("https://apisinalpublico.vercel.app/canais.json", timeout=10)
        if r1.status_code == 200:
            for c in r1.json():
                # O id aqui é o slug do canal (ex: globorj)
                cid = c.get('url').split('=')[-1]
                link = f"{base_url}/play?s=s1&id={cid}"
                channels.append(f'#EXTINF:-1 tvg-logo="{c.get("image")}" group-title="S1", [S1] {c.get("name")}\n{link}')
    except: pass

    # --- S2: Minha Tela ---
    try:
        h2 = {"Referer": "https://minhatela.xyz/", "User-Agent": UA}
        r2 = requests.get("https://myapiplay.top/api/guiadejogos/epg.php", headers=h2, timeout=10)
        if r2.status_code == 200:
            for c in r2.json():
                if c.get('channelLogo'):
                    link = f"{base_url}/play?s=s2&id={c.get('channelLogo')}"
                    channels.append(f'#EXTINF:-1 tvg-logo="{c.get("logo")}" group-title="S2", [S2] {c.get("name")}\n{link}')
    except: pass

    return Response("\n".join(channels), mimetype='text/plain')

@app.route('/play')
def play():
    """ Resolve o link e redireciona o reprodutor """
    source = request.args.get('s')
    channel_id = request.args.get('id')

    if source == 's1':
        # Para o S1, o player real costuma ser o sinaldvd
        player_url = f"https://sinaldvd.github.io/tv/player.html?id={channel_id}"
        ref = "https://sinalpublicoetv.vercel.app/"
        # Tenta pegar o .m3u8 direto
        stream = extrair_m3u8(player_url, ref)
        if not stream:
            # Fallback para o redirector do vercel que eles usam
            stream = f"https://t5r4e3w2q1y0-cloudflare-net.vercel.app/{channel_id}.m3u8|Referer=https://sinaldvd.github.io/&User-Agent={UA}"
        return redirect(stream)

    elif source == 's2':
        player_url = f"https://meuplayeronlinehd.com/myplay/watch.html?id={channel_id}"
        ref = "https://minhatela.xyz/"
        stream = extrair_m3u8(player_url, ref)
        if stream:
            return redirect(stream)
        return redirect(player_url)

    return "Caminho inválido", 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
