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
    decoded = decoded.replace("@yy1111@", "https://").replace("@yy111@", "https://www.").replace("@yy11@", "http://").replace("@yy1@", "http://www.")
    return decoded

def get_channels():
    app_id = "3713506"
    # O Smali mostra que o app tenta vários servidores (srv11 a srv19)
    servers = [f"srv{i}.e-droid.net" for i in range(11, 20)]
    random.shuffle(servers) # Tenta em ordem aleatória
    
    headers = {
        'User-Agent': 'Android Vinebre Software',
        'Accept-Language': 'pt-BR,pt;q=0.9',
        'Connection': 'keep-alive'
    }

    for server in servers:
        config_url = f"https://{server}/srv/config.php?v=228&idapp={app_id}"
        try:
            logger.info(f"Tentando servidor: {server}")
            response = requests.get(config_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Servidor {server} retornou erro {response.status_code}")
                continue

            data = response.json()
            cr = data.get("cr", "")
            secciones = data.get("secciones", [])
            
            # Se for dicionário, converte para lista
            if isinstance(secciones, dict):
                secciones = secciones.values()

            channels = []
            for section in secciones:
                # tipo 6 = Vídeo/TV
                if str(section.get("tipo")) == "6":
                    name = section.get("tit", "Canal")
                    url_raw = section.get("url", "")
                    if url_raw:
                        channels.append({
                            "name": name, 
                            "url": decode_url(url_raw, cr)
                        })
            
            if channels:
                logger.info(f"Sucesso! {len(channels)} canais capturados via {server}")
                return channels

        except Exception as e:
            logger.error(f"Erro no servidor {server}: {str(e)}")
            continue

    logger.critical("Falha total: Nenhum servidor respondeu com canais válidos.")
    return []

if __name__ == "__main__":
    print(get_channels())
