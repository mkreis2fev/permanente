from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import requests
import os
from urllib.parse import urlparse
import hashlib

app = Flask(__name__)
CORS(app)

# Lista de canais extraída do seu código JSON
CHANNELS_DATA = [
    {"name":"Globo News","id":"globonews","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globonews.png"},
    {"name":"Globo RJ","id":"globorj","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name":"Globo MG","id":"globomg","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name":"Globo SP","id":"globosp","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name":"Globo PE","id":"globope","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name":"Globo PB","id":"globopb","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name":"Globo RS","id":"globors","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name":"Globo ES","id":"globoes","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name":"Globo AM","id":"globoam","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name":"Globo CE","id":"globoce","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name":"SportyNet","id":"sportynet","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportynet.png"},
    {"name":"SportyNet+ 1","id":"sportynetplus1","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportynet.png"},
    {"name":"SportyNet+ 2","id":"sportynetplus2","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportynet.png"},
    {"name":"SportyNet+ 3","id":"sportynetplus3","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportynet.png"},
    {"name":"Paramount+ 1","id":"paramountplus1","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/paramountplus.png"},
    {"name":"Paramount+ 2","id":"paramountplus2","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/paramountplus.png"},
    {"name":"Paramount+ 3","id":"paramountplus3","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/paramountplus.png"},
    {"name":"MAX 1","id":"max1","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/max.png"},
    {"name":"MAX 2","id":"max2","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/max.png"},
    {"name":"MAX 3","id":"max3","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/max.png"},
    {"name":"Cazé TV 1","id":"caze1","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/cazetv.png"},
    {"name":"Cazé TV 2","id":"caze2","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/cazetv.png"},
    {"name":"Cazé TV 3","id":"caze3","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/cazetv.png"},
    {"name":"Disney+ 1","id":"disneyplus1","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/disneyplus.png"},
    {"name":"Disney+ 2","id":"disneyplus2","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/disneyplus.png"},
    {"name":"Disney+ 3","id":"disneyplus3","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/disneyplus.png"},
    {"name":"Prime Video 1","id":"primevideo","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/prime-video.png"},
    {"name":"Prime Video 2","id":"primevideo2","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/prime-video.png"},
    {"name":"Prime Video 3","id":"primevideo3","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/prime-video.png"},
    {"name":"Prime Video 4","id":"primevideo4","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/prime-video.png"},
    {"name":"ESPN","id":"espn","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/espn.png"},
    {"name":"ESPN 2","id":"espn2","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/espn-2.png"},
    {"name":"ESPN 3","id":"espn3","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/espn-3.png"},
    {"name":"ESPN 4","id":"espn4","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/espn-4.png"},
    {"name":"ESPN 5","id":"espn5","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/espn-5.png"},
    {"name":"ESPN 6","id":"espn6","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/espn-6.png"},
    {"name":"Ge TV","id":"getv","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/ge-tv.png"},
    {"name":"Band Sports","id":"bandsports","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/band-sports.png"},
    {"name":"Combate","id":"combate","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/combate.png"},
    {"name":"Premiere Clubes","id":"premiere","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere.png"},
    {"name":"Premiere 2","id":"premiere2","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-2.png"},
    {"name":"Premiere 3","id":"premiere3","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-3.png"},
    {"name":"Premiere 4","id":"premiere4","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-4.png"},
    {"name":"Premiere 5","id":"premiere5","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-5.png"},
    {"name":"Premiere 6","id":"premiere6","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-6.png"},
    {"name":"Premiere 7","id":"premiere7","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-7.png"},
    {"name":"Premiere 8","id":"premiere8","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-8.png"},
    {"name":"SporTV","id":"sportv","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportv.png"},
    {"name":"SporTV 2","id":"sportv2","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportv-2.png"},
    {"name":"SporTV 3","id":"sportv3","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportv-3.png"},
    {"name":"SporTV 4","id":"sportv4","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportv-4.png"},
    {"name":"Sporttv 1","id":"pt_sportv1","logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Logo_SportTV.svg/960px-Logo_SportTV.svg.png"},
    {"name":"Sporttv 2","id":"pt_sportv2","logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Logo_SportTV.svg/960px-Logo_SportTV.svg.png"},
    {"name":"Sporttv 3","id":"pt_sportv3","logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Logo_SportTV.svg/960px-Logo_SportTV.svg.png"},
    {"name":"Sporttv 4","id":"pt_sportv4","logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Logo_SportTV.svg/960px-Logo_SportTV.svg.png"},
    {"name":"Sporttv 5","id":"pt_sportv5","logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Logo_SportTV.svg/960px-Logo_SportTV.svg.png"},
    {"name":"Sporttv 6","id":"pt_sportv6","logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Logo_SportTV.svg/960px-Logo_SportTV.svg.png"},
    {"name":"Sporttv 7","id":"pt_sportv7","logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Logo_SportTV.svg/960px-Logo_SportTV.svg.png"},
    {"name":"ELEVEN 1","id":"pt_eleven1","logo":"https://upload.wikimedia.org/wikipedia/commons/d/d6/Logo_Eleven_Sports_2020.png"},
    {"name":"ELEVEN 2","id":"pt_eleven2","logo":"https://upload.wikimedia.org/wikipedia/commons/d/d6/Logo_Eleven_Sports_2020.png"},
    {"name":"ELEVEN 3","id":"pt_eleven3","logo":"https://upload.wikimedia.org/wikipedia/commons/d/d6/Logo_Eleven_Sports_2020.png"},
    {"name":"Benfica TV","id":"pt_benficatv","logo":"https://upload.wikimedia.org/wikipedia/commons/d/d2/Logo_Benfica_TV.png"},
    {"name":"A Bola","id":"pt_abola","logo":"https://ringiersportsmediagroup.com/wp-content/uploads/2023/07/abola.png"},
    {"name":"Canal 11","id":"pt_canal11","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/play-tv.png"},
    {"name":"UFC Fight Pass","id":"ufcfightpass","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/ufc.png"},
    {"name":"XSports","id":"xsports","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/xsports.png"},
    {"name":"A&E","id":"aie","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/aee.png"},
    {"name":"Adult Swim","id":"adultswim","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/adult-swim.png"},
    {"name":"AMC","id":"amc","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/amc.png"},
    {"name":"Animal Planet","id":"animalplanet","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/animal-planet.png"},
    {"name":"Megapix","id":"megapix","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/megapix.png"},
    {"name":"Arte 1","id":"arte1","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/arte1.png"},
    {"name":"AXN","id":"axn","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/axn.png"},
    {"name":"Band","id":"band","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/band.png"},
    {"name":"Band SP","id":"bandsp","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/band.png"},
    {"name":"Band RJ","id":"bandrj","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/band.png"},
    {"name":"Band News","id":"bandnews","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/band-news.png"},
    {"name":"BIS","id":"bis","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/bis.png"},
    {"name":"Cultura","id":"cultura","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/cultura.png"},
    {"name":"Cartoon Network","id":"cartoonnetwork","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/cartoon-network.png"},
    {"name":"Cartoonito","id":"cartoonito","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/cartoonito.png"},
    {"name":"Discovery Kids","id":"discoverykids","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/discovery-kids.png"},
    {"name":"Gloob","id":"gloob","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/gloob.png"},
    {"name":"Cinemax","id":"cinemax","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/cinemax.png"},
    {"name":"CNN Brasil","id":"cnnbrasil","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/cnn.png"},
    {"name":"Curta!","id":"curta","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/curta.png"},
    {"name":"Discovery Channel","id":"discoverychannel","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/discovery.png"},
    {"name":"Discovery Home & Health","id":"discoveryhh","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/discovery-home-and-health.png"},
    {"name":"Discovery Science","id":"discoveryscience","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/discovery-science.png"},
    {"name":"Discovery Theater","id":"discoverytheather","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/discovery-theater.png"},
    {"name":"Discovery Turbo","id":"discoveryturbo","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/discovery-turbo.png"},
    {"name":"Discovery World","id":"discoveryworld","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/discovery-world.png"},
    {"name":"Fish TV","id":"fishtv","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/fish-tv.png"},
    {"name":"Food Network","id":"foodnetwork","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/food-network.png"},
    {"name":"GNT","id":"gnt","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/gnt.png"},
    {"name":"HBO","id":"hbo","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/hbo.png"},
    {"name":"HBO 2","id":"hbo2","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/hbo2.png"},
    {"name":"HBO Family","id":"hbofamily","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/hbofamily.png"},
    {"name":"HBO Mundi","id":"hbomundi","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/hbomundi.png"},
    {"name":"HBO Plus","id":"hboplus","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/hboplus.png"},
    {"name":"HBO Pop","id":"hbopop","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/hbopop.png"},
    {"name":"HBO Xtreme","id":"hboxtreme","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/hboxtreme.png"},
    {"name":"HBO Signature","id":"hbosignathure","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/hbosignature.png"},
    {"name":"HGTV","id":"hgtv","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/hgtv.png"},
    {"name":"History 1","id":"history","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/history-channel.png"},
    {"name":"History 2","id":"history2","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/history-2.png"},
    {"name":"Lifetime","id":"lifetime","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/lifetime.png"},
    {"name":"Modo Viagem","id":"modoviagem","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/modo-viagem.png"},
    {"name":"Multishow","id":"multishow","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/multishow.png"},
    {"name":"Off","id":"off","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/canal-off.png"},
    {"name":"Record News","id":"recordnews","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/record-tv.png"},
    {"name":"Record TV","id":"record","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/record-tv.png"},
    {"name":"Record SP","id":"recordsp","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/record-tv.png"},
    {"name":"Record MG","id":"recordmg","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/record-tv.png"},
    {"name":"Record RJ","id":"recordrj","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/record-tv.png"},
    {"name":"Rede TV","id":"redetv","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/redetv.png"},
    {"name":"SBT","id":"sbt","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sbt.png"},
    {"name":"SBT SP","id":"sbtsp","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sbt.png"},
    {"name":"SBT RJ","id":"sbtrj","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sbtrj.png"},
    {"name":"SBT News","id":"sbtnews","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sbt.png"},
    {"name":"Sony Channel","id":"sony","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sony.png"},
    {"name":"Space","id":"space","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/space.png"},
    {"name":"Studio Universal","id":"studiouniversal","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/studio-universal.png"},
    {"name":"Telecine Action","id":"telecineaction","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/tc-action.png"},
    {"name":"Telecine Cult","id":"telecinecult","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/tc-cult.png"},
    {"name":"Telecine Fun","id":"telecinefun","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/tc-fun.png"},
    {"name":"Telecine Pipoca","id":"telecinepipoca","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/tc-pipoca.png"},
    {"name":"Telecine Premium","id":"telecinepremium","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/tc-premium.png"},
    {"name":"Telecine Touch","id":"telecinetouch","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/tc-touch.png"},
    {"name":"TLC","id":"tlc","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/tlc.png"},
    {"name":"TNT","id":"tnt","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/tnt.png"},
    {"name":"TNT Novelas","id":"tntnovelas","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/tnt-novelas.png"},
    {"name":"TNT Series","id":"tntseries","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/tnt-series.png"},
    {"name":"Universal TV","id":"universaltv","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/universal.png"},
    {"name":"Warner TV","id":"warnerchannel","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/warner-channel.png"},
    {"name":"24H PlayBoy","id":"playboy","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/24h.png"},
    {"name":"24H SexyHot","id":"sexyhot","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/24h.png"},
    {"name":"24H Naruto","id":"24h_naruto","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/24h.png"},
    {"name":"24H Dragonball","id":"24h_dragonball","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/24h.png"},
    {"name":"24H Os Simpsons","id":"24h_simpsons","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/24h.png"},
    {"name":"24H Chaves","id":"24h_chaves","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/24h.png"},
    {"name":"24H Todo Mundo Odeia o Cris","id":"24h_odeiachris","logo":"https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/24h.png"}
]

BASE_VIDEO_URL = "https://t5r4e3w2q1y0.s21-cloudfront-net.lat"

@app.route('/')
def index():
    return "Servidor TV Online ativo!"

@app.route('/lista.m3u')
def get_m3u():
    m3u = "#EXTM3U\n"
    for ch in CHANNELS_DATA:
        # Geramos o MD5 do ID para cada canal
        ch_id = ch["id"]
        ch_hash = hashlib.md5(ch_id.encode()).hexdigest()
        
        # Montamos a URL final que o Cloudfront usa
        video_url = f"{BASE_VIDEO_URL}/test/{ch_hash}/file.txt"
        
        # Link que passa pelo nosso tradutor de cabeçalhos
        link_proxy = f"{request.url_root}play.m3u8?u={video_url}"
        
        m3u += f'#EXTINF:-1 tvg-logo="{ch["logo"]}", {ch["name"]}\n{link_proxy}\n'
    return Response(m3u, mimetype='text/plain')

@app.route('/play.m3u8')
def proxy_handler():
    target_url = request.args.get('u')
    if not target_url: return "URL ausente", 400

    # Headers cruciais para que o Cloudfront aceite a requisição
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Referer': 'https://t5r4e3w2q1y0-cloudflare-net.vercel.app/',
        'Origin': 'https://t5r4e3w2q1y0-cloudflare-net.vercel.app'
    }
    
    try:
        resp = requests.get(target_url, headers=headers, timeout=10)
        
        # Se falhar com /test/, tenta sem (fallback)
        if resp.status_code != 200:
             alt_url = target_url.replace("/test/", "/")
             resp = requests.get(alt_url, headers=headers, timeout=10)
             if resp.status_code == 200:
                 target_url = alt_url

        parsed_uri = urlparse(target_url)
        domain_base = f"{parsed_uri.scheme}://{parsed_uri.netloc}"
        
        lines = resp.text.splitlines()
        new_lines = []
        for line in lines:
            line = line.strip()
            if line.startswith("/") and not line.startswith("//"):
                new_lines.append(domain_base + line)
            elif line and not line.startswith("#") and not line.startswith("http"):
                path_base = target_url.rsplit('/', 1)[0]
                new_lines.append(path_base + "/" + line)
            else:
                new_lines.append(line)
        
        return Response("\n".join(new_lines), mimetype='application/vnd.apple.mpegurl')
    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
}


Aqui está o código completo do `app.py`, contendo toda a lista de canais e a lógica de processamento de vídeo HLS:
