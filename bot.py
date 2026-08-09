import requests
import json
import logging

# Configura o log para vermos o erro exato no console do Railway/Terminal
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
            
    decoded = decoded.replace("@yy1111@", "https://")
    decoded = decoded.replace("@yy111@", "https://www.")
    decoded = decoded.replace("@yy11@", "http://")
    decoded = decoded.replace("@yy1@", "http://www.")
    return decoded

def get_channels():
    app_id = "3713506"
    # User-Agent exato do motor do AppCreator24
    headers = {
        'User-Agent': 'Android Vinebre Software',
        'Accept-Language': 'pt-BR,pt;q=0.9',
        'Connection': 'Keep-Alive'
    }
    
    config_url = f"https://config.e-droid.net/srv/config.php?v=228&idapp={app_id}"
    
    try:
        logger.info(f"Buscando configurações em: {config_url}")
        response = requests.get(config_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Tenta parsear o JSON
        try:
            data = response.json()
        except Exception:
            logger.error("O servidor não retornou um JSON válido.")
            return []

        cr = data.get("cr", "")
        secciones = data.get("secciones", [])
        channels = []

        # Tratamento: 'secciones' pode ser uma lista ou um dicionário
        items = []
        if isinstance(secciones, list):
            items = secciones
        elif isinstance(secciones, dict):
            items = secciones.values()

        for section in items:
            # tipo 6 = Vídeo/Streaming no GehTV
            if str(section.get("tipo")) == "6":
                name = section.get("tit", "Canal")
                url_raw = section.get("url", "")
                
                if url_raw:
                    final_url = decode_url(url_raw, cr)
                    channels.append({"name": name, "url": final_url})
        
        logger.info(f"Sucesso: {len(channels)} canais encontrados.")
        return channels

    except Exception as e:
        logger.error(f"Erro na captura: {str(e)}")
        return []

if __name__ == "__main__":
    print(json.dumps(get_channels(), indent=2))
