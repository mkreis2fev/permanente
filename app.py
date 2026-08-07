import requests
import re
import os
import base64
from flask import Flask, Response, request, render_template_string

app = Flask(__name__)

# Configurações de Identidade
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

def buscar_sinal_direto(url_player, referer_original):
    """ 
    Entra na página do player, pula os anúncios e pega o link .m3u8 real.
    """
    try:
        session = requests.Session()
        headers = {"User-Agent": UA, "Referer": referer_original}
        
        # 1. Acessa a página que contém o player
        res = session.get(url_player, headers=headers, timeout=10)
        html = res.text
        
        # 2. Procura o link do vídeo (.m3u8) no código Javascript
        # Esses sites costumam usar: source: 'link', file: 'link' ou o link puro
        match = re.search(r'["\'](https?://[^\s"\']+?\.m3u8[^\s"\']*)["\']', html)
        
        if match:
            stream_url = match.group(1).replace("\\/", "/")
            # Retorna o link formatado com o "Cadeado" de Referer que o IPTV Smarters/OTT Navigator entende
            return f"{stream_url}|User-Agent={UA}&Referer={url_player}"
            
        # 3. Se estiver em um IFRAME, tenta entrar nele
        iframe = re.search(r'<iframe.*?src=["\'](https?://.*?)["\']', html)
        if iframe:
            return buscar_sinal_direto(iframe.group(1), url_player)

    except Exception as e:
        print(f"Erro ao tunelar canal: {e}")
    return None

@app.route('/')
def home():
    return f"<h1>Servidor S1 & S2 Ativo</h1><p>Link M3U: {request.host_url}playlist.m3u</p>"

@app.route('/playlist.m3u')
def playlist():
    """ Gera a playlist M3U que o seu aplicativo vai ler """
    m3u_lines = ["#EXTM3U"]
    base_url = request.host_url.rstrip('/')

    # --- EXTRAÇÃO S1 (Sinal Público) ---
    try:
        r1 = requests.get("https://apisinalpublico.vercel.app/canais.json", timeout=10)
        for c in r1.json():
            # O link aponta para nossa rota /play para ser processado em tempo real
            link_iptv = f"{base_url}/play?s=S1&id={c.get('url')}"
            m3u_lines.append(f'#EXTINF:-1 tvg-logo="{c.get("image")}" group-title="S1", [S1] {c.get("name")}\n{link_iptv}')
    except: pass

    # --- EXTRAÇÃO S2 (Minha Tela) ---
    try:
        h2 = {"Referer": "https://minhatela.xyz/", "User-Agent": UA}
        r2 = requests.get("https://myapiplay.top/api/guiadejogos/epg.php", headers=h2, timeout=10)
        for c in r2.json():
            if c.get('channelLogo'):
                target = f"https://meuplayeronlinehd.com/myplay/watch.html?id={c.get('channelLogo')}"
                link_iptv = f"{base_url}/play?s=S2&id={target}"
                m3u_lines.append(f'#EXTINF:-1 tvg-logo="{c.get("logo")}" group-title="S2", [S2] {c.get("name")}\n{link_iptv}')
    except: pass

    return Response("\n".join(m3u_lines), mimetype='text/plain')

@app.route('/play')
def play():
    """ 
    A parte mais importante: Quando você clica no canal, 
    o servidor Python descobre o link real e redireciona o seu app de IPTV.
    """
    source = request.args.get('s')
    target_id = request.args.get('id')
    
    # Define de qual site estamos fingindo vir
    referer = "https://sinalpublic.vercel.app/" if source == "S1" else "https://minhatela.xyz/"
    
    # Tenta descobrir o sinal real (.m3u8)
    real_stream = buscar_sinal_direto(target_id, referer)
    
    if real_stream:
        # Manda o seu app de IPTV direto para o vídeo real decodificado
        return Response("", status=302, headers={"Location": real_stream})
    
    # Se falhar, tenta o link original como última opção
    return Response("", status=302, headers={"Location": target_id})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
