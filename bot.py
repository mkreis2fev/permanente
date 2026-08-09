import requests
import json
import logging
import random

# Forçar exibição de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def decode_url(obfuscated_url, cr):
    if not obfuscated_url or not obfuscated_url.startswith("@y@") or not cr:
        return obfuscated_url
    mapping_orig = " !#$%&()+,-./023456789:;<=>?ABCDEFGHIJKLMNOPQRSTUVWXYZ[^_abcdefghijklmnopqrstuvwxz{}~"
    url = obfuscated_url[3:]
    decoded = ""
    for char in url:
        index = cr.find(char)
        if index != -1: decoded += mapping_orig[index]
        else: decoded += char
    return decoded.replace("@yy1111@", "https://").replace("@yy111@", "https://www.").replace("@yy11@", "http://").replace("@yy1@", "http://www.")

def get_channels():
    app_id = "3713506"
    # Testando v=260 (mais recente) e v=228
    versions = ["260", "228"]
    servers = ["srv11.e-droid.net", "config.e-droid.net", "srv15.e-droid.net"]
    
    headers = {
        'User-Agent': 'Android Vinebre Software',
        'Accept': '*/*',
        'Connection': 'keep-alive'
    }

    for v in versions:
        for server in servers:
            config_url = f"https://{server}/srv/config.php?v={v}&idapp={app_id}"
            try:
                logger.info(f"==> TENTANDO: {config_url}")
                # verify=False ajuda se o Railway tiver problema de SSL com eles
                response = requests.get(config_url, headers=headers, timeout=15, verify=False)
                
                logger.info(f"STATUS: {response.status_code}")
                
                if response.status_code == 200:
                    # Se não for JSON, o IP está bloqueado!
                    if "<html" in response.text.lower():
                        logger.error(f"IP BLOQUEADO: O servidor {server} retornou HTML (Captcha/Aviso) em vez de dados.")
                        continue
                    
                    data = response.json()
                    cr = data.get("cr", "")
                    secciones = data.get("secciones", [])
                    
                    if isinstance(secciones, dict): secciones = list(secciones.values())

                    channels = []
                    logger.info(f"Seções encontradas: {[s.get('tit') for s in secciones]}")

                    for section in secciones:
                        tipo = str(section.get("tipo", ""))
                        if tipo == "6" and section.get("url"):
                            url_dec = decode_url(section.get("url"), cr)
                            channels.append({"name": section.get("tit"), "url": url_dec})
                    
                    if channels:
                        logger.info(f"SUCESSO: {len(channels)} canais capturados.")
                        return channels
            except Exception as e:
                logger.error(f"Erro no servidor {server}: {str(e)}")
                continue

    return []
