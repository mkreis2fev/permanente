import requests
import re
import os
import base64
from flask import Flask, Response, request, render_template_string
from urllib.parse import urljoin

app = Flask(__name__)

# Configurações de Agente
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

def get_headers(source):
    if source == 's1':
        return {
            "User-Agent": UA,
            "Referer": "https://sinaldvd.github.io/",
            "Origin": "https://sinaldvd.github.io",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site"
        }
    else:
        return {
            "User-Agent": UA,
            "Referer": "https://minhatela.xyz/",
            "Origin": "https://minhatela.xyz"
        }

@app.route('/')
def home():
    return f"Servidor IPTV Ativo: {request.host_url}playlist.m3u"

@app.route('/playlist.m3u')
def playlist():
    host = request.host_url.rstrip('/')
    lines = ["#EXTM3U"]
    
    # S1 - Sinal Público
    try:
        r = requests.get("https://apisinalpublico.vercel.app/canais.json", timeout=10).json()
        for c in r:
            cid = c.get('url').split('=')[-1]
            # O link agora aponta para o nosso proxy com .m3u8 no final para compatibilidade
            link = f"{host}/proxy/s1/{cid}/stream.m3u8"
            lines.append(f'#EXTINF:-1 tvg-logo="{c.get("image")}" group-title="S1", [S1] {c.get("name")}\n{link}')
    except: pass

    # S2 - Minha Tela
    try:
        headers = {"Referer": "https://minhatela.xyz/", "User-Agent": UA}
        r = requests.get("https://myapiplay.top/api/guiadejogos/epg.php", headers=headers, timeout=10).json()
        for c in r:
            if c.get('channelLogo'):
                cid = c.get('channelLogo')
                link = f"{host}/proxy/s2/{cid}/stream.m3u8"
                lines.append(f'#EXTINF:-1 tvg-logo="{c.get("logo")}" group-title="S2", [S2] {c.get("name")}\n{link}')
    except: pass

    return Response("\n".join(lines), mimetype='text/plain')

@app.route('/proxy/<source>/<cid>/stream.m3u8')
def proxy_m3u8(source, cid):
    """ Baixa o m3u8 original e reescreve os links para passarem pelo nosso servidor """
    if source == 's1':
        # S1 costuma usar esse formato
        target = f"https://t5r4e3w2q1y0-cloudflare-net.vercel.app/{cid}.m3u8"
    else:
        # Padrão S2 simplificado
        target = f"https://meuplayeronlinehd.com/hls/{cid}.m3u8"

    try:
        headers = get_headers(source)
        res = requests.get(target, headers=headers, timeout=10)
        
        if res.status_code != 200:
            # Segunda tentativa para S1 com domínio alternativo
            if source == 's1':
                target = f"https://a9b8c7d6e5f4-cloudflare-net.vercel.app/{cid}.m3u8"
                res = requests.get(target, headers=headers, timeout=10)

        # Reescreve o conteúdo do M3U8
        lines = res.text.splitlines()
        new_lines = []
        base_url = res.url.rsplit('/', 1)[0] + '/'
        
        for line in lines:
            if line.startswith('#') or not line.strip():
                new_lines.append(line)
            else:
                # Transforma cada segmento .ts ou sub-playlist em um link do nosso proxy
                full_url = urljoin(base_url, line.strip())
                encoded_url = base64.urlsafe_b64encode(full_url.encode()).decode()
                new_lines.append(f"{request.host_url.rstrip('/')}/ts?u={encoded_url}&s={source}")
        
        return Response("\n".join(new_lines), mimetype='application/vnd.apple.mpegurl')
    except:
        return "Erro ao processar sinal", 404

@app.route('/ts')
def proxy_ts():
    """ O túnel real para os dados do vídeo """
    url = base64.urlsafe_b64decode(request.args.get('u')).decode()
    source = request.args.get('s')
    
    try:
        res = requests.get(url, headers=get_headers(source), stream=True, timeout=15)
        return Response(res.iter_content(chunk_size=1024*64), content_type=res.headers.get('Content-Type'))
    except:
        return "", 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
