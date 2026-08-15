from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import requests
import re
import os
from urllib.parse import urlparse
import hashlib
import base64

app = Flask(__name__)
CORS(app)

# Criamos uma sessão para manter os cookies (simulando o "dar play" no navegador)
session = requests.Session()

# Lista completa de canais (Links originais da Vercel)
LINKS = [
    {"name": "Globo News", "url": "https://sinalpublicoetv.vercel.app/?id=globonews", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globonews.png"},
    {"name": "Globo RJ", "url": "https://sinalpublicoetv.vercel.app/?id=globorj", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name": "Globo MG", "url": "https://sinalpublicoetv.vercel.app/?id=globomg", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name": "Globo SP", "url": "https://sinalpublicoetv.vercel.app/?id=globosp", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name": "Globo PE", "url": "https://sinalpublicoetv.vercel.app/?id=globope", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name": "Globo PB", "url": "https://sinalpublicoetv.vercel.app/?id=globopb", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name": "Globo RS", "url": "https://sinalpublicoetv.vercel.app/?id=globors", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name": "Globo ES", "url": "https://sinalpublicoetv.vercel.app/?id=globoes", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name": "Globo AM", "url": "https://sinalpublicoetv.vercel.app/?id=globoam", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name": "Globo CE", "url": "https://sinalpublicoetv.vercel.app/?id=globoce", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/globo.png"},
    {"name": "SportyNet", "url": "https://sinalpublicoetv.vercel.app/?id=sportynet", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportynet.png"},
    {"name": "SportyNet+ 1", "url": "https://sinalpublicoetv.vercel.app/?id=sportynetplus1", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportynet.png"},
    {"name": "SportyNet+ 2", "url": "https://sinalpublicoetv.vercel.app/?id=sportynetplus2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportynet.png"},
    {"name": "SportyNet+ 3", "url": "https://sinalpublicoetv.vercel.app/?id=sportynetplus3", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportynet.png"},
    {"name": "Paramount+ 1", "url": "https://sinalpublicoetv.vercel.app/?id=paramountplus1", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/paramountplus.png"},
    {"name": "Paramount+ 2", "url": "https://sinalpublicoetv.vercel.app/?id=paramountplus2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/paramountplus.png"},
    {"name": "Paramount+ 3", "url": "https://sinalpublicoetv.vercel.app/?id=paramountplus3", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/paramountplus.png"},
    {"name": "MAX 1", "url": "https://sinalpublicoetv.vercel.app/?id=max1", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/max.png"},
    {"name": "MAX 2", "url": "https://sinalpublicoetv.vercel.app/?id=max2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/max.png"},
    {"name": "MAX 3", "url": "https://sinalpublicoetv.vercel.app/?id=max3", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/max.png"},
    {"name": "Cazé TV 1", "url": "https://sinalpublicoetv.vercel.app/?id=caze1", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/cazetv.png"},
    {"name": "Cazé TV 2", "url": "https://sinalpublicoetv.vercel.app/?id=caze2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/cazetv.png"},
    {"name": "Cazé TV 3", "url": "https://sinalpublicoetv.vercel.app/?id=caze3", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/cazetv.png"},
    {"name": "Disney+ 1", "url": "https://sinalpublicoetv.vercel.app/?id=disneyplus1", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/disneyplus.png"},
    {"name": "Disney+ 2", "url": "https://sinalpublicoetv.vercel.app/?id=disneyplus2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/disneyplus.png"},
    {"name": "Disney+ 3", "url": "https://sinalpublicoetv.vercel.app/?id=disneyplus3", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/disneyplus.png"},
    {"name": "Prime Video 1", "url": "https://sinalpublicoetv.vercel.app/?id=primevideo", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/prime-video.png"},
    {"name": "Prime Video 2", "url": "https://sinalpublicoetv.vercel.app/?id=primevideo2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/prime-video.png"},
    {"name": "Prime Video 3", "url": "https://sinalpublicoetv.vercel.app/?id=primevideo3", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/prime-video.png"},
    {"name": "Prime Video 4", "url": "https://sinalpublicoetv.vercel.app/?id=primevideo4", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/prime-video.png"},
    {"name": "ESPN", "url": "https://sinalpublicoetv.vercel.app/?id=espn", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/espn.png"},
    {"name": "ESPN 2", "url": "https://sinalpublicoetv.vercel.app/?id=espn2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/espn-2.png"},
    {"name": "ESPN 3", "url": "https://sinalpublicoetv.vercel.app/?id=espn3", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/espn-3.png"},
    {"name": "ESPN 4", "url": "https://sinalpublicoetv.vercel.app/?id=espn4", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/espn-4.png"},
    {"name": "ESPN 5", "url": "https://sinalpublicoetv.vercel.app/?id=espn5", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/espn-5.png"},
    {"name": "ESPN 6", "url": "https://sinalpublicoetv.vercel.app/?id=espn6", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/espn-6.png"},
    {"name": "Ge TV", "url": "https://sinalpublicoetv.vercel.app/?id=getv", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/ge-tv.png"},
    {"name": "Band Sports", "url": "https://sinalpublicoetv.vercel.app/?id=bandsports", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/band-sports.png"},
    {"name": "Combate", "url": "https://sinalpublicoetv.vercel.app/?id=combate", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/combate.png"},
    {"name": "Premiere Clubes", "url": "https://sinalpublicoetv.vercel.app/?id=premiere", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere.png"},
    {"name": "Premiere 2", "url": "https://sinalpublicoetv.vercel.app/?id=premiere2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-2.png"},
    {"name": "Premiere 3", "url": "https://sinalpublicoetv.vercel.app/?id=premiere3", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-3.png"},
    {"name": "Premiere 4", "url": "https://sinalpublicoetv.vercel.app/?id=premiere4", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-4.png"},
    {"name": "Premiere 5", "url": "https://sinalpublicoetv.vercel.app/?id=premiere5", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-5.png"},
    {"name": "Premiere 6", "url": "https://sinalpublicoetv.vercel.app/?id=premiere6", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-6.png"},
    {"name": "Premiere 7", "url": "https://sinalpublicoetv.vercel.app/?id=premiere7", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-7.png"},
    {"name": "Premiere 8", "url": "https://sinalpublicoetv.vercel.app/?id=premiere8", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/premiere-8.png"},
    {"name": "SporTV", "url": "https://sinalpublicoetv.vercel.app/?id=sportv", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportv.png"},
    {"name": "SporTV 2", "url": "https://sinalpublicoetv.vercel.app/?id=sportv2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportv-2.png"},
    {"name": "SporTV 3", "url": "https://sinalpublicoetv.vercel.app/?id=sportv3", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportv-3.png"},
    {"name": "SporTV 4", "url": "https://sinalpublicoetv.vercel.app/?id=sportv4", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sportv-4.png"},
    {"name": "Sporttv 1", "url": "https://sinalpublicoetv.vercel.app/?id=pt_sportv1", "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Logo_SportTV.svg/960px-Logo_SportTV.svg.png"},
    {"name": "Sporttv 2", "url": "https://sinalpublicoetv.vercel.app/?id=pt_sportv2", "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Logo_SportTV.svg/960px-Logo_SportTV.svg.png"},
    {"name": "Sporttv 3", "url": "https://sinalpublicoetv.vercel.app/?id=pt_sportv3", "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Logo_SportTV.svg/960px-Logo_SportTV.svg.png"},
    {"name": "Sporttv 4", "url": "https://sinalpublicoetv.vercel.app/?id=pt_sportv4", "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Logo_SportTV.svg/960px-Logo_SportTV.svg.png"},
    {"name": "Sporttv 5", "url": "https://sinalpublicoetv.vercel.app/?id=pt_sportv5", "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Logo_SportTV.svg/960px-Logo_SportTV.svg.png"},
    {"name": "Sporttv 6", "url": "https://sinalpublicoetv.vercel.app/?id=pt_sportv6", "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Logo_SportTV.svg/960px-Logo_SportTV.svg.png"},
    {"name": "Sporttv 7", "url": "https://sinalpublicoetv.vercel.app/?id=pt_sportv7", "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Logo_SportTV.svg/960px-Logo_SportTV.svg.png"},
    {"name": "ELEVEN 1", "url": "https://sinalpublicoetv.vercel.app/?id=pt_eleven1", "logo": "https://upload.wikimedia.org/wikipedia/commons/d/d6/Logo_Eleven_Sports_2020.png"},
    {"name": "ELEVEN 2", "url": "https://sinalpublicoetv.vercel.app/?id=pt_eleven2", "logo": "https://upload.wikimedia.org/wikipedia/commons/d/d6/Logo_Eleven_Sports_2020.png"},
    {"name": "ELEVEN 3", "url": "https://sinalpublicoetv.vercel.app/?id=pt_eleven3", "logo": "https://upload.wikimedia.org/wikipedia/commons/d/d6/Logo_Eleven_Sports_2020.png"},
    {"name": "Benfica TV", "url": "https://sinalpublicoetv.vercel.app/?id=pt_benficatv", "logo": "https://upload.wikimedia.org/wikipedia/commons/d/d2/Logo_Benfica_TV.png"},
    {"name": "A Bola", "url": "https://sinalpublicoetv.vercel.app/?id=pt_abola", "logo": "https://ringiersportsmediagroup.com/wp-content/uploads/2023/07/abola.png"},
    {"name": "Canal 11", "url": "https://sinalpublicoetv.vercel.app/?id=pt_canal11", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/play-tv.png"},
    {"name": "UFC Fight Pass", "url": "https://sinalpublicoetv.vercel.app/?id=ufcfightpass", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/ufc.png"},
    {"name": "XSports", "url": "https://sinalpublicoetv.vercel.app/?id=xsports", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/ufc.png"},
    {"name": "A&E", "url": "https://sinalpublicoetv.vercel.app/?id=aie", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/aee.png"},
    {"name": "Adult Swim", "url": "https://sinalpublicoetv.vercel.app/?id=adultswim", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/adult-swim.png"},
    {"name": "AMC", "url": "https://sinalpublicoetv.vercel.app/?id=amc", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/amc.png"},
    {"name": "Animal Planet", "url": "https://sinalpublicoetv.vercel.app/?id=animalplanet", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/animal-planet.png"},
    {"name": "Megapix", "url": "https://sinalpublicoetv.vercel.app/?id=megapix", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/megapix.png"},
    {"name": "Arte 1", "url": "https://sinalpublicoetv.vercel.app/?id=arte1", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/arte1.png"},
    {"name": "AXN", "url": "https://sinalpublicoetv.vercel.app/?id=axn", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/axn.png"},
    {"name": "Band", "url": "https://sinalpublicoetv.vercel.app/?id=band", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/band.png"},
    {"name": "Band SP", "url": "https://sinalpublicoetv.vercel.app/?id=bandsp", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/band.png"},
    {"name": "Band RJ", "url": "https://sinalpublicoetv.vercel.app/?id=bandrj", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/band.png"},
    {"name": "Band News", "url": "https://sinalpublicoetv.vercel.app/?id=bandnews", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/band-news.png"},
    {"name": "BIS", "url": "https://sinalpublicoetv.vercel.app/?id=bis", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/bis.png"},
    {"name": "Cultura", "url": "https://sinalpublicoetv.vercel.app/?id=cultura", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/cultura.png"},
    {"name": "Cartoon Network", "url": "https://sinalpublicoetv.vercel.app/?id=cartoonnetwork", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/cartoon-network.png"},
    {"name": "Cartoonito", "url": "https://sinalpublicoetv.vercel.app/?id=cartoonito", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/cartoonito.png"},
    {"name": "Discovery Kids", "url": "https://sinalpublicoetv.vercel.app/?id=discoverykids", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/discovery-kids.png"},
    {"name": "Gloob", "url": "https://sinalpublicoetv.vercel.app/?id=gloob", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/gloob.png"},
    {"name": "Cinemax", "url": "https://sinalpublicoetv.app/?id=cinemax", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/cinemax.png"},
    {"name": "CNN Brasil", "url": "https://sinalpublicoetv.app/?id=cnnbrasil", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/cnn.png"},
    {"name": "Curta!", "url": "https://sinalpublicoetv.app/?id=curta", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/curta.png"},
    {"name": "Discovery Channel", "url": "https://sinalpublicoetv.app/?id=discoverychannel", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/discovery.png"},
    {"name": "Discovery Home & Health", "url": "https://sinalpublicoetv.app/?id=discoveryhh", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/discovery-home-and-health.png"},
    {"name": "Discovery Science", "url": "https://sinalpublicoetv.app/?id=discoveryscience", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/discovery-science.png"},
    {"name": "Discovery Theater", "url": "https://sinalpublicoetv.app/?id=discoverytheather", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/discovery-theater.png"},
    {"name": "Discovery Turbo", "url": "https://sinalpublicoetv.app/?id=discoveryturbo", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/discovery-turbo.png"},
    {"name": "Discovery World", "url": "https://sinalpublicoetv.app/?id=discoveryworld", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/discovery-world.png"},
    {"name": "Fish TV", "url": "https://sinalpublicoetv.app/?id=fishtv", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/fish-tv.png"},
    {"name": "Food Network", "url": "https://sinalpublicoetv.app/?id=foodnetwork", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/food-network.png"},
    {"name": "GNT", "url": "https://sinalpublicoetv.app/?id=gnt", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/gnt.png"},
    {"name": "HBO", "url": "https://sinalpublicoetv.app/?id=hbo", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/hbo.png"},
    {"name": "HBO 2", "url": "https://sinalpublicoetv.app/?id=hbo2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/hbo2.png"},
    {"name": "HBO Family", "url": "https://sinalpublicoetv.app/?id=hbofamily", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/hbofamily.png"},
    {"name": "HBO Mundi", "url": "https://sinalpublicoetv.app/?id=hbomundi", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/hbomundi.png"},
    {"name": "HBO Plus", "url": "https://sinalpublicoetv.app/?id=hboplus", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/hboplus.png"},
    {"name": "HBO Pop", "url": "https://sinalpublicoetv.app/?id=hbopop", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/hbopop.png"},
    {"name": "HBO Xtreme", "url": "https://sinalpublicoetv.app/?id=hboxtreme", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/hboxtreme.png"},
    {"name": "HBO Signature", "url": "https://sinalpublicoetv.app/?id=hbosignathure", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/hbosignature.png"},
    {"name": "HGTV", "url": "https://sinalpublicoetv.app/?id=hgtv", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/hgtv.png"},
    {"name": "History 1", "url": "https://sinalpublicoetv.app/?id=history", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/history-channel.png"},
    {"name": "History 2", "url": "https://sinalpublicoetv.app/?id=history2", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/history-2.png"},
    {"name": "Lifetime", "url": "https://sinalpublicoetv.app/?id=lifetime", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/lifetime.png"},
    {"name": "Modo Viagem", "url": "https://sinalpublicoetv.app/?id=modoviagem", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/modo-viagem.png"},
    {"name": "Multishow", "url": "https://sinalpublicoetv.app/?id=multishow", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/multishow.png"},
    {"name": "Off", "url": "https://sinalpublicoetv.app/?id=off", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/canal-off.png"},
    {"name": "Record News", "url": "https://sinalpublicoetv.app/?id=recordnews", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/record-tv.png"},
    {"name": "Record TV", "url": "https://sinalpublicoetv.app/?id=record", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/record-tv.png"},
    {"name": "Record SP", "url": "https://sinalpublicoetv.app/?id=recordsp", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/record-tv.png"},
    {"name": "Record MG", "url": "https://sinalpublicoetv.app/?id=recordmg", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/record-tv.png"},
    {"name": "Record RJ", "url": "https://sinalpublicoetv.app/?id=recordrj", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/record-tv.png"},
    {"name": "Rede TV", "url": "https://sinalpublicoetv.app/?id=redetv", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/redetv.png"},
    {"name": "SBT", "url": "https://sinalpublicoetv.app/?id=sbt", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sbt.png"},
    {"name": "SBT SP", "url": "https://sinalpublicoetv.app/?id=sbtsp", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sbt.png"},
    {"name": "SBT RJ", "url": "https://sinalpublicoetv.app/?id=sbtrj", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sbtrj.png"},
    {"name": "SBT News", "url": "https://sinalpublicoetv.app/?id=sbtnews", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sbt.png"},
    {"name": "Sony Channel", "url": "https://sinalpublicoetv.app/?id=sony", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/sony.png"},
    {"name": "Space", "url": "https://sinalpublicoetv.app/?id=space", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/space.png"},
    {"name": "Studio Universal", "url": "https://sinalpublicoetv.app/?id=studiouniversal", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/studio-universal.png"},
    {"name": "Telecine Action", "url": "https://sinalpublicoetv.app/?id=telecineaction", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/tc-action.png"},
    {"name": "Telecine Cult", "url": "https://sinalpublicoetv.app/?id=telecinecult", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/tc-cult.png"},
    {"name": "Telecine Fun", "url": "https://sinalpublicoetv.app/?id=telecinefun", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/tc-fun.png"},
    {"name": "Telecine Pipoca", "url": "https://sinalpublicoetv.app/?id=telecinepipoca", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/tc-pipoca.png"},
    {"name": "Telecine Premium", "url": "https://sinalpublicoetv.app/?id=telecinepremium", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/tc-premium.png"},
    {"name": "Telecine Touch", "url": "https://sinalpublicoetv.app/?id=telecinetouch", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/tc-touch.png"},
    {"name": "TLC", "url": "https://sinalpublicoetv.app/?id=tlc", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/tlc.png"},
    {"name": "TNT", "url": "https://sinalpublicoetv.app/?id=tnt", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/tnt.png"},
    {"name": "TNT Novelas", "url": "https://sinalpublicoetv.app/?id=tntnovelas", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/tnt-novelas.png"},
    {"name": "TNT Series", "url": "https://sinalpublicoetv.app/?id=tntseries", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/tnt-series.png"},
    {"name": "Universal TV", "url": "https://sinalpublicoetv.app/?id=universaltv", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/universal.png"},
    {"name": "Warner TV", "url": "https://sinalpublicoetv.app/?id=warnerchannel", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/logo/warner-channel.png"},
    {"name": "24H PlayBoy", "url": "https://sinalpublicoetv.app/?id=playboy", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/24h.png"},
    {"name": "24H SexyHot", "url": "https://sinalpublicoetv.app/?id=sexyhot", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/24h.png"},
    {"name": "24H Naruto", "url": "https://sinalpublicoetv.app/?id=24h_naruto", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/24h.png"},
    {"name": "24H Dragonball", "url": "https://sinalpublicoetv.app/?id=24h_dragonball", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/24h.png"},
    {"name": "24H Os Simpsons", "url": "https://sinalpublicoetv.app/?id=24h_simpsons", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/24h.png"},
    {"name": "24H Chaves", "url": "https://sinalpublicoetv.app/?id=24h_chaves", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/24h.png"},
    {"name": "24H Todo Mundo Odeia o Cris", "url": "https://sinalpublicoetv.app/?id=24h_odeiachris", "logo": "https://d1r94zrla0glo-cloudfront.vercel.app/sinalpublico/foto/embed/24h.png"}
]

session = requests.Session()

def extrair_hls_dinamico(vercel_url):
    """Acessa a página do canal e captura o link de vídeo real"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Referer': 'https://sinalpublicoetv.vercel.app/'
    }
    try:
        # Abre a página para gerar sessão/cookies
        resp_page = session.get(vercel_url, headers=headers, timeout=10)
        html = resp_page.text
        
        # Procura por link direto .m3u8 ou cloudfront no código
        match = re.search(r'(https://[^\s\'"]+\.(m3u8|txt)[^\s\'"]*)', html)
        if not match:
             match = re.search(r'(https://[^\s\'"]+cloudfront[^\s\'"]+)', html)
        
        if match: return match.group(1)
        
        # Tenta via atob (base64)
        base64_matches = re.findall(r'atob\([\'"]([a-zA-Z0-9+/=]+)[\'"]\)', html)
        for b in base64_matches:
            try:
                decoded = base64.b64decode(b).decode('utf-8')
                if 'http' in decoded and ('.m3u8' in decoded or 'cloudfront' in decoded):
                    return decoded
            except: continue

        # Fallback MD5
        channel_id = vercel_url.split('id=')[-1].split('&')[0]
        ch_hash = hashlib.md5(channel_id.encode()).hexdigest()
        return f"https://t5r4e3w2q1y0.s21-cloudfront-net.lat/test/{ch_hash}/file.txt"
    except: return None

@app.route('/')
def index():
    return "Servidor TV Online ATIVO!"

@app.route('/lista.m3u')
def get_m3u():
    m3u = "#EXTM3U\n"
    host = request.host_url.rstrip('/')
    for ch in LINKS:
        # O player vai chamar /play.m3u8 que vai extrair o link real
        link_proxy = f"{host}/play.m3u8?u={ch['url']}"
        m3u += f'#EXTINF:-1 tvg-logo="{ch["logo"]}", {ch["name"]}\n{link_proxy}\n'
    return Response(m3u, mimetype='text/plain')

@app.route('/play.m3u8')
def proxy_handler():
    vercel_url = request.args.get('u')
    if not vercel_url: return "URL ausente", 400

    # CAPTURA O LINK HLS NO MOMENTO DO PLAY
    target_url = extrair_hls_dinamico(vercel_url)
    if not target_url: return "Erro ao capturar sinal", 404

    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://t5r4e3w2q1y0-cloudflare-net.vercel.app/',
        'Origin': 'https://t5r4e3w2q1y0-cloudflare-net.vercel.app'
    }
    
    try:
        resp = session.get(target_url, headers=headers, timeout=15)
        if resp.status_code != 200 and "/test/" in target_url:
            target_url = target_url.replace("/test/", "/")
            resp = session.get(target_url, headers=headers, timeout=15)

        domain_base = f"{urlparse(target_url).scheme}://{urlparse(target_url).netloc}"
        host = request.host_url.rstrip('/')
        
        lines = resp.text.splitlines()
        new_lines = []
        for line in lines:
            line = line.strip()
            if not line: continue
            if line.startswith("/") and not line.startswith("//"):
                full_url = domain_base + line
                new_lines.append(f"{host}/segment?u={full_url}")
            elif line and not line.startswith("#") and not line.startswith("http"):
                path_base = target_url.rsplit('/', 1)[0]
                full_url = path_base + "/" + line
                new_lines.append(f"{host}/segment?u={full_url}")
            else: new_lines.append(line)
        
        # Converte o arquivo (mesmo que seja .txt) para o formato M3U8 correto
        return Response("\n".join(new_lines), mimetype='application/vnd.apple.mpegurl')
    except Exception as e: return str(e), 500

@app.route('/segment')
def proxy_segment():
    target_url = request.args.get('u')
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://t5r4e3w2q1y0-cloudflare-net.vercel.app/'
    }
    try:
        resp = session.get(target_url, headers=headers, stream=True, timeout=15)
        return Response(resp.content, content_type=resp.headers.get('Content-Type', 'video/mp2t'))
    except: return "Erro", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
