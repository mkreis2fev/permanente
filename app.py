import requests
import re
import os
from flask import Flask, Response, request, render_template_string

app = Flask(__name__)

# Configurações de Navegação
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def extrair_link_m3u8(url_player, referer_site):
    """ Entra no player e captura o sinal real .m3u8 """
    try:
        headers = {"User-Agent": UA, "Referer": referer_site}
        # 1. Pega o HTML do player
        res = requests.get(url_player, headers=headers, timeout=10)
        html = res.text
        
        # 2. Busca link .m3u8 (HLS) no código
        match = re.search(r'["\'](https?://[^\s"\']+?\.m3u8[^\s"\']*)["\']', html)
        if match:
            return match.group(1).replace("\\/", "/")
        
        # 3. Busca em iframes se não achar na principal
        iframe = re.search(r'iframe.*?src=["\'](https?://.*?)["\']', html)
        if iframe:
            return extrair_link_m3u8(iframe.group(1), url_player)
    except:
        pass
    return None

@app.route('/')
def home():
    return f"<h1>Servidor S1 & S2 Ativo</h1><p>Link M3U: {request.host_url}playlist.m3u</p>"

@app.route('/playlist.m3u')
def playlist():
    """ Gera a playlist M3U apontando para o nosso resolvedor """
    channels = ["#EXTM3U"]
    base_url = request.host_url.rstrip('/')

    # --- S1 (Sinal Público) ---
    try:
        r = requests.get("https://apisinalpublico.vercel.app/canais.json", timeout=10)
        for c in r.json():
            name, logo, target = c.get('name'), c.get('image'), c.get('url')
            # Mudamos o link para passar pelo nosso servidor
            link = f"{base_url}/get_stream?s=S1&id={target}"
            channels.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="S1", [S1] {name}\n{link}')
    except: pass

    # --- S2 (Minha Tela) ---
    try:
        h = {"Referer": "https://minhatela.xyz/", "User-Agent": UA}
        r = requests.get("https://myapiplay.top/api/guiadejogos/epg.php", headers=h, timeout=10)
        for c in r.json():
            if c.get('channelLogo'):
                name, logo = c.get('name'), c.get('logo')
                target = f"https://meuplayeronlinehd.com/myplay/watch.html?id={c.get('channelLogo')}"
                link = f"{base_url}/get_stream?s=S2&id={target}"
                channels.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="S2", [S2] {name}\n{link}')
    except: pass

    return Response("\n".join(channels), mimetype='text/plain')

@app.route('/get_stream')
def get_stream():
    """ 
    Esta rota converte a página do site em um link de vídeo que o IPTV entende.
    Usamos o sufixo |Referer= para que players modernos como Smarters/OTT aceitem.
    """
    source = request.args.get('s')
    target = request.args.get('id')
    
    ref = "https://sinalpublic.vercel.app/" if source == "S1" else "https://minhatela.xyz/"
    
    # 1. Tenta achar o .m3u8 real
    real_video_url = extrair_link_m3u8(target, ref)
    
    if real_video_url:
        # 2. Adiciona os headers necessários no final da URL (padrão IPTV)
        # Isso faz o player enviar o Referer correto para o servidor do vídeo
        final_url = f"{real_video_url}|Referer={ref}&User-Agent={UA}"
        return Response("", status=302, headers={"Location": final_url})
    
    return "Stream não encontrada", 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
