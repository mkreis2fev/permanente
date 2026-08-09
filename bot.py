import requests
import json
import logging
import random

# Forçar exibição de logs no nível máximo
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
    # Tenta vários subdomínios e também o domínio direto
    servers = [f"srv{i}.e-droid.net" for i in range(11, 21)]
    servers.append("config.e-droid.net")
    random.shuffle(servers)
    
    headers = {
        'User-Agent': 'Android Vinebre Software',
        'Accept-Encoding': 'gzip',
        'Connection': 'Keep-Alive'
    }

    for server in servers:
        # A URL exata que o app usa
        config_url = f"https://{server}/srv/config.php?v=228&idapp={app_id}"
        try:
            logger.info(f"==> Testando: {server}")
            # verify=False ignora erros de SSL que às vezes o Railway tem com a e-droid
            response = requests.get(config_url, headers=headers, timeout=12, verify=True)
            
            logger.info(f"Resposta de {server}: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                except:
                    # Se falhar o JSON, vamos ver o que veio no texto (pode ser um erro do Cloudflare)
                    logger.warning(f"Recebido texto em vez de JSON: {response.text[:100]}")
                    continue

                cr = data.get("cr", "")
                secciones = data.get("secciones", [])
                
                if isinstance(secciones, dict):
                    secciones = secciones.values()

                channels = []
                for section in secciones:
                    # TIPO 6 = TV/VÍDEO
                    if str(section.get("tipo")) == "6":
                        name = section.get("tit", "Canal")
                        url_raw = section.get("url", "")
                        if url_raw:
                            channels.append({"name": name, "url": decode_url(url_raw, cr)})
                
                if channels:
                    logger.info(f"SUCESSO! {len(channels)} canais encontrados no {server}")
                    return channels
            
            elif response.status_code == 403:
                logger.error(f"BLOQUEIO: O IP do Railway foi banido pelo {server}")
                
        except Exception as e:
            logger.error(f"Erro de conexão com {server}: {str(e)}")
            continue

    logger.critical("NENHUM SERVIDOR RESPONDEU. Possível bloqueio total de IP.")
    return []

if __name__ == "__main__":
    print(get_channels())
