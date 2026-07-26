# -*- coding: utf-8 -*-
import re, io, sys, unicodedata

import os
_ICI  = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.dirname(_ICI)
HTML = os.path.join(_RACINE, "site", "index.html")
PDF  = os.path.join(_ICI, "guide-officiel-2024.txt")

def norm(s):
    s = unicodedata.normalize("NFC", s)
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace(" ", " ").replace(" ", " ").replace(" ", " ")
    s = s.replace("–", "-").replace("—", "-").replace("…", "...")
    s = s.replace("œ", "oe").replace("Œ", "OE")
    s = s.replace("«", '"').replace("»", '"')
    s = re.sub(r"\s+", " ", s)
    return s.strip()

# ---------- PDF ----------
raw = io.open(PDF, encoding="utf-8").read()
# retire le bruit de mise en page
noise = [
    "Detecter les signes d'un developpement inhabituel chez les enfants de moins de 7 ans",
    "Deuxieme edition. Janvier 2024",
    "DEUXIEME EDITION. JANVIER 2024",
]
lines = []
for ln in raw.split("\n"):
    n = norm(ln)
    if not n:
        continue
    flat = "".join(c for c in unicodedata.normalize("NFD", n) if unicodedata.category(c) != "Mn")
    if any(flat.lower().startswith(x.lower()[:40]) for x in noise):
        continue
    if re.fullmatch(r"\d{1,3}", n):          # numeros de page
        continue
    lines.append(n)
pdf = " ".join(lines)
# retire les colonnes de cases Oui / Non
pdf = re.sub(r"\b(Oui|Non)\b", " ", pdf)
pdf = re.sub(r"\s+", " ", pdf)

# ---------- HTML ----------
html = io.open(HTML, encoding="utf-8").read()
bloc = html[html.index("const AGES"):html.index("let ageActuel")]

ages = []
for m in re.finditer(r'\{id:"(\w+)", court:"([^"]+)", titre:"([^"]+)", plage:"([^"]+)"', bloc):
    ages.append({"id": m.group(1), "court": m.group(2), "plage": m.group(4), "pos": m.start(), "domaines": []})
for i, a in enumerate(ages):
    fin = ages[i+1]["pos"] if i+1 < len(ages) else len(bloc)
    seg = bloc[a["pos"]:fin]
    for dm in re.finditer(r'\{nom:"([^"]+)", items:\[(.*?)\]\}', seg, re.S):
        items = re.findall(r'"((?:[^"\\]|\\.)*)"', dm.group(2))
        a["domaines"].append({"nom": dm.group(1), "items": [it.replace('\\"', '"') for it in items]})

# ---------- decoupage du PDF par tranche d'age ----------
bornes = []
for m in re.finditer(r"SIGNES D'ALERTE (?:A|À) ([^,]{1,30}?) \(de ", pdf):
    bornes.append((m.start(), m.group(1).strip()))
sections = {}
for i, (p, lab) in enumerate(bornes):
    fin = bornes[i+1][0] if i+1 < len(bornes) else len(pdf)
    sections[i] = (lab, pdf[p:fin])

print("sections PDF detectees : %d -> %s" % (len(bornes), [b[1] for b in bornes]))
print("tranches HTML          : %d -> %s" % (len(ages), [a["court"] for a in ages]))
print()

total = ok = 0
problemes = []

for i, a in enumerate(ages):
    lab, sec = sections.get(i, ("?", ""))
    # positions des titres de domaine dans la section
    dpos = []
    for d in a["domaines"]:
        cle = norm(d["nom"]).split(" (")[0]
        j = sec.find(cle)
        dpos.append((cle, j))
    for d in a["domaines"]:
        cle = norm(d["nom"]).split(" (")[0]
        dstart = sec.find(cle)
        suivants = [p for (c, p) in dpos if p > dstart and p >= 0]
        dend = min(suivants) if suivants else len(sec)
        for it in d["items"]:
            total += 1
            n = norm(it)
            pos_global = pdf.find(n)
            pos_sec = sec.find(n)
            if pos_global < 0:
                problemes.append(("ABSENT", a["court"], d["nom"], it))
            elif pos_sec < 0:
                problemes.append(("HORS TRANCHE", a["court"], d["nom"], it))
            elif not (dstart <= pos_sec < dend):
                problemes.append(("MAUVAIS DOMAINE", a["court"], d["nom"], it))
            else:
                ok += 1

print("items verifies : %d / %d conformes" % (ok, total))
print()
if problemes:
    for typ, age, dom, it in problemes:
        print("[%s] %s / %s" % (typ, age, dom))
        print("     %s" % it[:110])
else:
    print("aucun ecart detecte")
