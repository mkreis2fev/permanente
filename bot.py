import requests
import json
import logging
import random

# Força logs detalhados no console do Railway
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
    # O GehTV usa o srv15 com frequência, vamos tentar ele e o principal
    urls = [
        f"https://config.e-droid.net/srv/config.php?v=260&idapp={app_id}",
        f"https://srv15.e-droid.net/srv/config.php?v=260&idapp={app_id}",
        f"http://config.e-droid.net/srv/config.php?v=260&idapp={app_id}" # Tentando HTTP puro
    ]
    
    headers = {
        'User-Agent': 'Android Vinebre Software',
        'Accept': '*/*',
        'Accept-Language': 'pt-BR,pt;q=0.9',
        'Connection': 'keep-alive'
    }

    for url in urls:
        try:
            logger.info(f"==> Tentando URL: {url}")
            # verify=False ignora erros de certificado SSL que o Railway às vezes tem
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            
            logger.info(f"Resposta HTTP: {response.status_code}")
            
            if response.status_code != 200:
                continue

            # DIAGNÓSTICO: Se não for JSON, imprime os primeiros 300 caracteres do que veio
            if "json" not in response.headers.get("Content-Type", "").lower():
                logger.error(f"O servidor nao mandou JSON. Resposta: {response.text[:300]}")
                continue

            data = response.json()
            cr = data.get("cr", "")
            secciones = data.get("secciones", [])
            
            if isinstance(secciones, dict): secciones = list(secciones.values())

            channels = []
            
            # Varredura Recursiva Completa
            def scan(items):
                res = []
                for item in (items.values() if isinstance(items, dict) else items):
                    # Pega canais (tipo 6)
                    if str(item.get("tipo")) == "6" and item.get("url"):
                        res.append({"name": item.get("tit", "Canal"), "url": decode_url(item.get("url"), cr)})
                    
                    # Entra em submenus (TV > Variedades)
                    for key in ["atribs", "submenu_items", "items"]:
                        if key in item: res.extend(scan(item[key]))
                return res

            channels = scan(secciones)
            
            if channels:
                logger.info(f"Sucesso: {len(channels)} canais extraidos de {url}")
                return channels
            else:
                logger.warning(f"Nenhum canal tipo 6 achado no JSON de {url}")

        except Exception as e:
            logger.error(f"Erro ao acessar {url}: {str(e)}")
            continue

    return []
