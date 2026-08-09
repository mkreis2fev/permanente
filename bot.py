import requests
import json
import logging
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def decode_url(obfuscated_url, cr):
    if not obfuscated_url.startswith("@y@") or not cr:
        return obfuscated_url
    mapping_orig = " !#$%&()+,-./023456789:;<=>?ABCDEFGHIJKLMNOPQRSTUVWXYZ[^_abcdefghijklmnopqrstuvwxz{}~"
    url = obfuscated_url[3:]
    decoded = ""
    for char in url:
        index = cr.find(char)
        if index != -1:
            decoded += mapping_orig[index]
        else:
            decoded += char
    return decoded.replace("@yy1111@", "https://").replace("@yy111@", "https://www.").replace("@yy11@", "http://").replace("@yy1@", "http://www.")

def get_channels():
    app_id = "3713506"
    # Testando os servidores principais mapeados no Smali
    servers = [f"srv{i}.e-droid.net" for i in range(11, 20)]
    random.shuffle(servers)
    
    headers = {
        'User-Agent': 'Android Vinebre Software',
        'Accept': '*/*',
        'Accept-Language': 'pt-BR,pt;q=0.9',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache'
    }

    for server in servers:
        config_url = f"https://{server}/srv/config.php?v=228&idapp={app_id}"
        try:
            logger.info(f"Tentando capturar de: {server}")
            response = requests.get(config_url, headers=headers, timeout=15)
            
            # LOG DE DIAGNÓSTICO: Isso vai aparecer no seu painel do Railway
            logger.info(f"Status Code: {response.status_code}")
            
            if response.status_code != 200:
                continue

            # Se não for JSON, o AppCreator pode ter enviado um erro em HTML
            if "json" not in response.headers.get("Content-Type", "").lower():
                logger.warning(f"Resposta de {server} não é JSON. Verifique se o IP foi bloqueado.")
                logger.debug(f"Conteúdo recebido: {response.text[:200]}")
                continue

            data = response.json()
            cr = data.get("cr", "")
            secciones = data.get("secciones", [])
            
            if isinstance(secciones, dict):
                secciones = secciones.values()

            channels = []
            for section in secciones:
                if str(section.get("tipo")) == "6":
                    name = section.get("tit", "Canal")
                    url_raw = section.get("url", "")
                    if url_raw:
                        channels.append({"name": name, "url": decode_url(url_raw, cr)})
            
            if channels:
                logger.info(f"Sucesso! {len(channels)} canais extraídos.")
                return channels

        except Exception as e:
            logger.error(f"Falha ao conectar em {server}: {str(e)}")
            continue

    return []
