# -*- coding: utf-8 -*-
import re, io, unicodedata

import os
_ICI  = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.dirname(_ICI)
HTML = os.path.join(_RACINE, "site", "index.html")
PDF  = os.path.join(_ICI, "guide-officiel-2024.txt")

def norm(s):
    s = unicodedata.normalize("NFC", s)
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace(" ", " ").replace(" ", " ").replace(" ", " ")
    s = s.replace("–", "-").replace("—", "-").replace("…", "...")
    s = s.replace("œ", "oe").replace("«", '"').replace("»", '"')
    return re.sub(r"\s+", " ", s).strip()

pdf = norm(io.open(PDF, encoding="utf-8").read())
pdf = re.sub(r"\b(Oui|Non)\b", " ", pdf)
pdf = re.sub(r"\s+", " ", pdf)

html = io.open(HTML, encoding="utf-8").read()
bloc = html[html.index("const TRANSVERSAL"):html.index("const AGES")]

total = ok = 0
for m in re.finditer(r'\{titre:"([^"]+)"(?:, alerte:true)?, items:\[(.*?)\]\}', bloc, re.S):
    titre = m.group(1)
    items = re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(2))
    for it in items:
        total += 1
        n = norm(it.replace('\\"', '"'))
        if n in pdf:
            ok += 1
        else:
            # tolere les reformulations de regroupement : on teste par fragments
            frags = [f for f in re.split(r"[(),;/]", n) if len(f.strip()) > 18]
            trouves = sum(1 for f in frags if f.strip() in pdf)
            if frags and trouves == len(frags):
                ok += 1
                print("[OK fragments] %s : %s" % (titre, n[:80]))
            else:
                print("[ECART] %s" % titre)
                print("   HTML : %s" % n[:120])
                for f in frags:
                    if f.strip() not in pdf:
                        print("   manquant : %r" % f.strip()[:80])

print()
print("transversaux : %d / %d conformes" % (ok, total))
