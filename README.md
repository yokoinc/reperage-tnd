# reperage-tnd

Grille de repérage des troubles du neurodéveloppement chez l'enfant de moins de
7 ans. Page HTML statique, servie par nginx en conteneur.

> **Outil non officiel**, sans lien avec la Délégation interministérielle à la
> stratégie nationale pour les TND ni le GNCRA. Le document de référence, seul à
> transmettre à la plateforme de coordination et d'orientation, reste le livret
> officiel publié sur handicap.gouv.fr.

## Contexte

Le site officiel `tndtest.com` est hors service depuis le 1er juillet 2026 —
domaine en `clientHold`, retiré de la zone DNS. Son contenu était chargé depuis
une API aujourd'hui inaccessible et n'a jamais été archivé.

Cette page est une reconstruction à partir du livret officiel « Détecter les
signes d'un développement inhabituel chez les enfants de moins de 7 ans »,
2ᵉ édition, janvier 2024, archivé dans `tools/`.

## Contenu

- 8 tranches d'âge, de 6 mois à 6 ans — 103 items, plus 23 items transversaux
- 4 domaines de développement jusqu'à 3 ans, 5 à partir de 4 ans
- Seuils d'orientation : 2 signes dans ≥ 2 domaines (0-3 ans), 3 signes dans
  ≥ 2 domaines (4-6 ans)
- Régression des compétences : orientation en urgence, prime sur le score
- Items de la tranche précédente consultables, comptés à part, hors score
- Sélection automatique de la tranche depuis la date de naissance
- Impression avec feuille de style dédiée

Aucune donnée n'est stockée ni transmise. Aucune ressource externe, aucun
traceur.

## Démarrage

```bash
docker compose up -d
curl http://127.0.0.1:8791/healthz
```

`site/index.html` s'ouvre aussi directement dans un navigateur, sans serveur.

### Configuration

| Variable | Défaut | Rôle |
|---|---|---|
| `BIND_ADDR` | `127.0.0.1` | interface d'écoute sur l'hôte |
| `HOST_PORT` | `8791` | port sur l'hôte |

Le port interne du conteneur est 8080 et ne se change pas : l'image tourne en
UID 101 et ne peut pas se lier sous 1024.

### Permissions

nginx tourne en UID 101 et ne correspond à aucun utilisateur de l'hôte : les
fichiers montés doivent être lisibles par `other`, sinon 403 alors que le
conteneur reste `healthy`.

```bash
chmod 755 site nginx && chmod 644 site/index.html nginx/default.conf
```

## HTTPS

Le conteneur ne fait pas de TLS.

**Caddy**

```caddy
tnd.example.org {
    reverse_proxy 127.0.0.1:8791
}
```

**nginx**

```nginx
location / {
    proxy_pass http://127.0.0.1:8791;
    proxy_set_header Host              $host;
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

**Synology DSM** — Portail de connexion → Proxy inversé :
`HTTPS / tnd.example.org / 443` → `HTTP / localhost / 8791`, HSTS activé,
certificat Let's Encrypt assigné à l'entrée.

**Traefik** — commenter `ports:` et joindre le service par le réseau Docker :

```yaml
labels:
  traefik.enable: "true"
  traefik.http.routers.tnd.rule: "Host(`tnd.example.org`)"
  traefik.http.routers.tnd.entrypoints: "websecure"
  traefik.http.routers.tnd.tls.certresolver: "letsencrypt"
  traefik.http.services.tnd.loadbalancer.server.port: "8080"
```

Le rate limiting appartient au reverse proxy : derrière une terminaison locale,
nginx ne voit que `127.0.0.1`.

## Vérification du contenu

```bash
python tools/verif-items-age.py
python tools/verif-items-transversaux.py
```

Les items de la page sont comparés au texte du PDF officiel — libellé exact et
domaine d'appartenance, section par section. À rejouer à chaque nouvelle édition
du livret.

Deux faux positifs connus sur les transversaux : une différence de casse sur
« Perte objective… », et « non apais**i**bles » du livret, corrigé ici en
« apais**a**bles ».

## Durcissement

`nginx-unprivileged` en UID 101 · `read_only` · `cap_drop: ALL` ·
`no-new-privileges` · 64 Mo / 64 PID · écoute sur `127.0.0.1` par défaut ·
GET et HEAD seuls, 405 sinon · CSP `default-src 'none'` · `X-Robots-Tag:
noindex` · logs plafonnés à 3 × 5 Mo.

Les logs d'accès enregistrent l'IP des visiteurs. Pour ne rien journaliser,
`access_log off;` dans `nginx/default.conf`.

## Licence

Le contenu clinique — items, seuils, libellés — est repris du livret de la
Délégation interministérielle à la stratégie nationale pour les TND. Document
public, à citer comme tel.

Le reste — page, configuration, scripts — est librement réutilisable.

## Avertissement

Aide à la saisie. Ne pose aucun diagnostic et ne se substitue pas au jugement
clinique.

Adresses des plateformes de coordination et d'orientation :
[ameli.fr](https://www.ameli.fr/content/adresses-et-telephones-plateformes-de-coordination-et-d-orientation-pco)
