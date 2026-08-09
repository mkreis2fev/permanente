import requests
import json
import logging
import random

# Configura logs detalhados
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
        if index != -1:
            decoded += mapping_orig[index]
        else:
            decoded += char
            
    return decoded.replace("@yy1111@", "https://").replace("@yy111@", "https://www.").replace("@yy11@", "http://").replace("@yy1@", "http://www.")

def get_channels():
    app_id = "3713506"
    # Servidores capturados do motor Smali do GehTV
    servers = [f"srv{i}.e-droid.net" for i in range(11, 20)]
    random.shuffle(servers)
    
    headers = {
        'User-Agent': 'Android Vinebre Software',
        'Accept': '*/*',
        'Accept-Language': 'pt-BR,pt;q=0.9',
        'Connection': 'keep-alive'
    }

    for server in servers:
        # v=228 extraído do Smali (VSOURCE = 0xe4)
        config_url = f"https://{server}/srv/config.php?v=228&idapp={app_id}"
        try:
            logger.info(f"Conectando a: {server}")
            # timeout aumentado para 20s para evitar erro no Railway
            response = requests.get(config_url, headers=headers, timeout=20, verify=True)
            
            if response.status_code != 200:
                logger.warning(f"Servidor {server} negou acesso (Status {response.status_code})")
                continue

            data = response.json()
            cr = data.get("cr", "")
            secciones = data.get("secciones", [])
            
            # Secciones pode vir como dicionário {"0":{...}, "1":{...}} ou lista [...]
            if isinstance(secciones, dict):
                secciones = list(secciones.values())

            channels = []

            # Função para varrer todas as subseções (TV > Variedades > Canais)
            def find_video_recursively(items):
                found = []
                if not items: return found
                
                # Garante que estamos iterando uma lista
                current_items = list(items.values()) if isinstance(items, dict) else items
                
                for item in current_items:
                    tipo = str(item.get("tipo", ""))
                    url_raw = item.get("url", "")
                    tit = item.get("tit", "Canal")

                    # Tipo 6 é vídeo (canal de TV)
                    if tipo == "6" and url_raw:
                        found.append({
                            "name": tit,
                            "url": decode_url(url_raw, cr)
                        })
                        logger.info(f"Canal detectado: {tit}")
                    
                    # Procura dentro de menus ou atributos extras (recursividade)
                    for key in ["atribs", "submenu_items", "items"]:
                        if key in item:
                            found.extend(find_video_recursively(item[key]))
                return found

            channels = find_video_recursively(secciones)

            if channels:
                logger.info(f"Total de {len(channels)} canais capturados!")
                return channels
            else:
                logger.warning(f"O servidor {server} respondeu, mas não há canais tipo 6 ativos.")

        except Exception as e:
            logger.error(f"Erro de conexão no {server}: {str(e)}")
            continue

    logger.critical("FALHA TOTAL: O backend do GehTV recusou todas as tentativas.")
    return []

if __name__ == "__main__":
    chans = get_channels()
    for c in chans:
        print(f"CANAL: {c['name']} | URL: {c['url']}")
