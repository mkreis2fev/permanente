import requests
import json
import logging
import random

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
    # O servidor config.e-droid.net é o balanceador principal
    url = f"https://config.e-droid.net/srv/config.php?v=260&idapp={app_id}"
    
    headers = {
        'User-Agent': 'Android Vinebre Software',
        'Accept': '*/*',
        'Connection': 'keep-alive'
    }

    try:
        logger.info(f"Buscando config em: {url}")
        # timeout longo e verify=False para evitar travas no Railway
        response = requests.get(url, headers=headers, timeout=20, verify=False)
        
        if response.status_code != 200:
            logger.error(f"Erro no servidor: {response.status_code}")
            return []

        data = response.json()
        cr = data.get("cr", "")
        secciones = data.get("secciones", [])
        
        if isinstance(secciones, dict):
            secciones = list(secciones.values())

        channels = []
        
        # O GehTV tem canais em vários lugares. Vamos varrer TUDO.
        for s in secciones:
            tipo = str(s.get("tipo", ""))
            tit = s.get("tit", "Sem Nome")
            
            # Caso 1: Canal direto (Tipo 6)
            if tipo == "6":
                url_raw = s.get("url", "")
                if url_raw:
                    channels.append({"name": tit, "url": decode_url(url_raw, cr)})
            
            # Caso 2: Canais dentro de Submenus ou Listas (Deep Scan)
            # Procuramos por campos comuns onde o AppCreator24 guarda sub-itens
            for key in ["atribs", "submenu_items", "items"]:
                sub_items = s.get(key, [])
                if isinstance(sub_items, dict): sub_items = sub_items.values()
                
                for item in sub_items:
                    # Se o item dentro da categoria tiver uma URL de vídeo
                    item_url = item.get("url", "")
                    if item_url.startswith("@y@") or ".m3u8" in item_url:
                        item_tit = item.get("tit", tit)
                        channels.append({"name": item_tit, "url": decode_url(item_url, cr)})

        if not channels:
            # DEBUG: Se não achar nada, imprime as seções que o servidor mandou
            nomes = [s.get("tit") for s in secciones]
            logger.warning(f"Nenhum canal achado. Seções lidas: {nomes}")

        return channels

    except Exception as e:
        logger.error(f"Erro geral no bot: {str(e)}")
        return []
