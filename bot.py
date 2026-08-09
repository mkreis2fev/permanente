import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def decode_url(url, cr):
    if not url or not url.startswith("@y@") or not cr: return url
    orig = " !#$%&()+,-./023456789:;<=>?ABCDEFGHIJKLMNOPQRSTUVWXYZ[^_abcdefghijklmnopqrstuvwxz{}~"
    d = "".join([orig[cr.find(c)] if c in cr else c for c in url[3:]])
    return d.replace("@yy1111@", "https://").replace("@yy111@", "https://www.").replace("@yy11@", "http://").replace("@yy1@", "http://www.")

def get_channels():
    app_id = "3713506"
    # Testamos v=260 que costuma trazer os submenus abertos
    url = f"https://config.e-droid.net/srv/config.php?v=260&idapp={app_id}"
    headers = {'User-Agent': 'Android Vinebre Software'}
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200: return []
        
        data = res.json()
        cr = data.get("cr", "")
        secciones = data.get("secciones", [])
        if isinstance(secciones, dict): secciones = secciones.values()
        
        channels = []

        def crawl(items):
            for i in items:
                if isinstance(i, dict):
                    # Se for tipo 6 ou tiver URL de streaming
                    u = i.get("url", "")
                    if str(i.get("tipo")) == "6" or ".m3u8" in u or u.startswith("@y@"):
                        if u:
                            channels.append({
                                "name": i.get("tit", "Canal"),
                                "url": decode_url(u, cr)
                            })
                    
                    # Procura em sub-pastas (TV > VARIEDADES)
                    for key in ["atribs", "submenu_items", "items"]:
                        if key in i and i[key]:
                            sub = i[key]
                            if isinstance(sub, dict): sub = sub.values()
                            crawl(sub)

        crawl(secciones)
        return channels
    except:
        return []
