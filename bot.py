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
    # Servidores mapeados no Smali
    servers = [f"srv{i}.e-droid.net" for i in range(11, 21)]
    random.shuffle(servers)
    
    headers = {
        'User-Agent': 'Android Vinebre Software',
        'Accept': '*/*',
        'Connection': 'keep-alive'
    }

    for server in servers:
        config_url = f"https://{server}/srv/config.php?v=228&idapp={app_id}"
        try:
            logger.info(f"==> Verificando servidor: {server}")
            response = requests.get(config_url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                continue

            data = response.json()
            cr = data.get("cr", "")
            secciones = data.get("secciones", [])
            
            # AppCreator24 pode mandar como lista ou dicionário
            if isinstance(secciones, dict):
                secciones = secciones.values()

            channels = []
            
            logger.info(f"Total de seções encontradas no app: {len(secciones)}")

            for section in secciones:
                tipo = str(section.get("tipo", ""))
                nome = section.get("tit", "Sem nome")
                
                # Tipo 6 é o tipo padrão de VÍDEO/STREAMING no GehTV
                # Buscamos em todas as seções, mesmo as que não estão no menu principal
                if tipo == "6":
                    url_raw = section.get("url", "")
                    if url_raw:
                        url_decodificada = decode_url(url_raw, cr)
                        logger.info(f"Canal encontrado: {nome}")
                        channels.append({"name": nome, "url": url_decodificada})
                
                # Algumas vezes os canais são do tipo 1 (Web) mas apontam para um player
                elif tipo == "1":
                    url_web = section.get("url", "")
                    if ".m3u8" in url_web or ".mp4" in url_web:
                        channels.append({"name": nome, "url": url_web})

            if channels:
                logger.info(f"Sucesso! Total de {len(channels)} canais capturados.")
                return channels
            else:
                logger.warning(f"Nenhum canal tipo 6 encontrado em {server}. Seções disponíveis: {[s.get('tit') for s in secciones]}")

        except Exception as e:
            logger.error(f"Erro no servidor {server}: {str(e)}")
            continue

    return []

if __name__ == "__main__":
    chans = get_channels()
    for c in chans:
        print(f"{c['name']} -> {c['url']}")
