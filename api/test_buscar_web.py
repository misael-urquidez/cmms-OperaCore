import urllib.request
from urllib.parse import quote_plus
import re

def buscar_web(query, max_resultados=5):
    url = 'https://html.duckduckgo.com/html/?q=' + quote_plus(query)
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
    })
    with urllib.request.urlopen(req, timeout=10) as res:
        status = res.status
        html_doc = res.read().decode('utf-8', errors='ignore')

    print("STATUS:", status)
    print("LEN HTML:", len(html_doc))
    print("PRIMEROS 800 CHARS:")
    print(html_doc[:800])
    print("---")

    patron = re.compile(
        r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>(.*?)</a>.*?'
        r'<a class="result__snippet"[^>]*>(.*?)</a>',
        re.DOTALL,
    )
    matches = patron.findall(html_doc)
    print("RESULTADOS ENCONTRADOS POR EL REGEX:", len(matches))

buscar_web("transportador industrial banda causas fallas comunes reparacion")