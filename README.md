# Grille de repérage TND — 0 à 6 ans

Outil de saisie assistée de la grille de repérage des troubles du
neurodéveloppement chez l'enfant de moins de 7 ans.

Page HTML statique servie par nginx dans un conteneur. Aucune base de données,
aucun backend, aucune donnée persistée : la grille est remplie dans le
navigateur du médecin et disparaît à la fermeture de l'onglet.

**Tourne sur n'importe quel hôte Docker** — NAS Synology, serveur Linux, VPS.
Le conteneur est identique partout ; seule la terminaison HTTPS change.

---

## Pourquoi cet outil existe

Le site officiel **tndtest.com**, édité par le GNCRA pour la Délégation
interministérielle à la stratégie nationale pour les TND, est **hors service
depuis le 1er juillet 2026**.

Cause : le domaine est passé en `clientHold` chez son registrar (Gandi),
c'est-à-dire retiré de la zone DNS. Ce n'est ni une fermeture ni un impayé —
l'enregistrement est valide jusqu'au 30 juin 2027. C'est une suspension
administrative, très probablement une validation de coordonnées ICANN jamais
effectuée. Le nom ne résout plus du tout : ni site, ni messagerie.

Le contenu du site est **irrécupérable depuis les archives**. C'était une
application Angular qui chargeait ses questions à l'exécution depuis une API
WordPress (`api.tndtest.com/wp-json/acf/v3/…`). Les robots d'archivage
n'exécutent pas le JavaScript : ils ont capturé la coquille, jamais les
questions. Vérifié sur les 20 captures Wayback de l'API entre 2021 et 2025
(toutes des redirections ou la page de login) et sur archive.today (aucune
capture).

Cette page est donc une **reconstruction à partir du livret officiel**, pas une
copie du site disparu.

## Source du contenu

> « Détecter les signes d'un développement inhabituel chez les enfants de moins
> de 7 ans », **2ᵉ édition, janvier 2024**
> Délégation interministérielle à la stratégie nationale pour les TND

C'est la version en vigueur, celle intégrée au carnet de santé. Le site disparu
servait encore la version de 2019 : son application n'avait pas été recompilée
depuis octobre 2020.

Le PDF officiel est archivé dans `tools/guide-officiel-2024.pdf`. **C'est lui, et
lui seul, qui doit être transmis à la plateforme de coordination et
d'orientation.**

### Fidélité au livret

Les **103 items d'âge** et les **23 items transversaux** ont été comparés au PDF
officiel par script : libellé exact et domaine d'appartenance, section par
section. Quatre écarts trouvés et corrigés.

Une seule divergence assumée : le livret imprime « non apais**i**bles »
(coquille), corrigé ici en « non apais**a**bles ».

Les scripts sont rejouables à chaque nouvelle édition du livret :

```bash
python tools/verif-items-age.py
python tools/verif-items-transversaux.py
```

Le second signale deux faux positifs connus : une différence de casse sur
« Perte objective… » et la coquille ci-dessus.

## Ce que fait la page

- Saisie de la date de naissance → sélection automatique de la tranche d'âge
- 8 tranches : 6, 12, 18, 24 mois puis 3, 4, 5, 6 ans — 103 items, tous distincts
- 4 domaines de développement jusqu'à 3 ans, 5 à partir de 4 ans (la Cognition
  est individualisée à cet âge)
- 23 items transversaux, identiques à tout âge : facteurs de risque, régression,
  comportements instinctuels / sensoriels / émotionnels, inquiétudes
- Comptage des signes par domaine en direct, verdict permanent en pied de page
- Règle appliquée : **2 signes dans ≥ 2 domaines** (0-3 ans), **3 signes dans
  ≥ 2 domaines** (4-6 ans)
- Une **régression des compétences** déclenche l'orientation en urgence et prime
  sur le score
- Dépliant « tranche précédente », hors score (voir plus bas)
- Impression avec feuille de style dédiée

Aucune donnée n'est enregistrée, ni en local, ni côté serveur. Aucun traceur,
aucune requête réseau, aucune ressource externe — contrairement au site d'origine
qui embarquait Google Analytics.

### Tranche précédente

Les signes ne sont pas relistés à chaque âge : un enfant en difficulté peut
n'avoir aucun signe sur sa propre classe d'âge tout en en cumulant sur la
précédente. Le livret demande donc de l'interroger, « à partir de 4 ans, au
moindre doute ».

Un dépliant sous la grille contient les items de la tranche antérieure — replié
jusqu'à 3 ans, **ouvert d'office à partir de 4 ans**, absent à 6 mois. Les
réponses y sont comptées et affichées séparément mais **n'entrent jamais dans le
score** : la règle officielle porte sur le volet de l'âge de l'enfant. Le
dépliant s'imprime même replié.

---

## Contenu

```
reperage-tnd/
├── .env                    # BIND_ADDR et HOST_PORT (aucun secret)
├── docker-compose.yml      # le conteneur, durci
├── nginx/default.conf      # serveur + en-têtes de sécurité
├── site/index.html         # la grille — source unique
├── tools/                  # PDF officiel + scripts de vérification
└── README.md
```

`site/index.html` est la **seule** copie de la grille : elle se suffit à
elle-même et s'ouvre directement dans un navigateur, sans serveur, pour tester
une modification avant de la déployer.

---

## Déploiement

### 1. Lancer le conteneur

Identique sur tout hôte Docker :

```bash
docker compose up -d
curl -s http://127.0.0.1:8791/healthz     # -> ok
```

Réglages dans `.env` :

| Variable | Défaut | Rôle |
|---|---|---|
| `BIND_ADDR` | `127.0.0.1` | interface d'écoute sur l'hôte |
| `HOST_PORT` | `8791` | port sur l'hôte (8080 en interne, jamais à changer) |

Par défaut le service **n'est joignable que depuis l'hôte lui-même**, pas depuis
le réseau. C'est volontaire : le HTTPS est apporté par le reverse proxy. Vérifier
qu'un port est libre :

```bash
ss -tulpn | grep 8791
```

### 1 bis. Permissions des fichiers — le piège classique

**Pas de `PUID`/`PGID` ici.** Ces variables sont une convention LinuxServer.io,
pas un standard Docker ; l'image nginx officielle les ignore. Elles seraient de
toute façon inutiles : les deux montages sont en lecture seule et le conteneur
n'écrit jamais rien, donc il n'y a aucune propriété de fichier à faire
correspondre.

En revanche les UID ne sont **pas traduits** à la frontière du conteneur, ils
sont comparés numériquement. nginx tourne en `uid=101` ; un fichier appartenant
à `uid=1000` sur l'hôte lui est donc étranger, et il retombe sur les permissions
`other`. Vérifié au banc :

| Permissions sur l'hôte | Réponse |
|---|---|
| `644` (`-rw-r--r--`) | **200** |
| `600` (`-rw-------`) | **403** — `open() failed (13: Permission denied)` |

Les fichiers doivent donc être **lisibles par tous**, et non appartenir à un
utilisateur précis :

```bash
chmod 755 site nginx
chmod 644 site/index.html nginx/default.conf
```

C'est l'échec le plus probable au premier déploiement, en particulier sur
Synology où File Station et les ACL DSM posent souvent des permissions
restrictives. **Symptôme trompeur** : le conteneur reste `healthy` — la sonde
`/healthz` ne lit aucun fichier — mais la page renvoie 403. Diagnostic :

```bash
docker compose logs --tail 20 | grep denied
```

Ne pas ajouter de `user:` au compose pour forcer un autre UID : l'image
pré-attribue ses répertoires internes à l'UID 101, et changer l'utilisateur
casserait l'écriture du cache et du fichier PID. Corriger les permissions côté
hôte, pas l'identité côté conteneur.

### 2. Terminaison HTTPS

Le conteneur ne fait **pas** de TLS. Choisir une des options ci-dessous.

#### Caddy — le plus court sur un serveur Linux

Certificat automatique, renouvellement automatique. Tout le `Caddyfile` :

```caddy
tnd.mondomaine.fr {
    reverse_proxy 127.0.0.1:8791
}
```

#### nginx sur l'hôte

```nginx
server {
    listen 443 ssl http2;
    server_name tnd.mondomaine.fr;

    ssl_certificate     /etc/letsencrypt/live/tnd.mondomaine.fr/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tnd.mondomaine.fr/privkey.pem;

    add_header Strict-Transport-Security "max-age=31536000" always;

    location / {
        proxy_pass http://127.0.0.1:8791;
        proxy_set_header Host              $host;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Certificat : `certbot --nginx -d tnd.mondomaine.fr`

#### Synology DSM

1. **Certificat** : Panneau de configuration → Sécurité → Certificat → Ajouter →
   Let's Encrypt, avec `tnd.mondomaine.fr`
2. **Proxy inversé** : Panneau de configuration → Portail de connexion →
   Proxy inversé → Créer

   | | Source | Destination |
   |---|---|---|
   | Protocole | HTTPS | HTTP |
   | Nom d'hôte | `tnd.mondomaine.fr` | `localhost` |
   | Port | `443` | `8791` |

   *Paramètres avancés* → activer **HSTS**, puis assigner le certificat à cette
   entrée.
3. **Projet** : Container Manager → Projet → Créer → *Utiliser docker-compose.yml
   existant*, chemin `/volume1/docker/tnd-reperage`

> NAS sous l'ancien paquet Docker (DSM 6 / 7.0) : ajouter `version: "3.8"` en
> première ligne du docker-compose.yml.

#### Reverse proxy conteneurisé (Traefik, nginx-proxy)

Commenter la section `ports:` du docker-compose.yml — inutile de publier sur
l'hôte — et joindre le service par le réseau Docker. Pour Traefik, ajouter au
service :

```yaml
    networks: [proxy]
    labels:
      traefik.enable: "true"
      traefik.http.routers.tnd.rule: "Host(`tnd.mondomaine.fr`)"
      traefik.http.routers.tnd.entrypoints: "websecure"
      traefik.http.routers.tnd.tls.certresolver: "letsencrypt"
      traefik.http.services.tnd.loadbalancer.server.port: "8080"
```

et déclarer le réseau externe en fin de fichier :

```yaml
networks:
  proxy:
    external: true
```

### 3. Pare-feu

N'ouvrir que le 443. Le port du conteneur n'a pas à être joignable de
l'extérieur, et ne doit pas l'être.

Activer une protection contre les abus au niveau de l'hôte — voir
« Limites connues ». Sur Synology : Protection DoS dans le pare-feu et Blocage
automatique. Sur Linux : fail2ban, ou le rate limiting du reverse proxy.

### 4. Vérifier

```bash
curl -sI https://tnd.mondomaine.fr
```

Attendu : `200`, `Content-Security-Policy: default-src 'none'`,
`X-Robots-Tag: noindex`, et un `Strict-Transport-Security` ajouté par le proxy.

---

## Exploitation

### Mettre à jour la grille

Le fichier est monté en volume : remplacer `site/index.html`, recharger la page.
**Pas de reconstruction, pas de redémarrage.**

### Arrêter

```bash
docker compose down
```

Rien à nettoyer ailleurs : pas de volume nommé, aucune écriture hors du dossier
du projet.

### Journalisation

Les logs d'accès nginx enregistrent l'**adresse IP des visiteurs** — donnée
personnelle. Rotation à 3 × 5 Mo. Pour ne rien journaliser, dans
`nginx/default.conf` :

```
access_log /dev/stdout;   ->   access_log off;
```

---

## Durcissement

| Réglage | Raison |
|---|---|
| `nginx-unprivileged` | le processus tourne en UID 101, jamais en root |
| `read_only: true` | système de fichiers du conteneur non modifiable |
| `cap_drop: ALL` | aucune capacité Linux conservée |
| `no-new-privileges` | interdit toute escalade via setuid |
| `${BIND_ADDR}` = `127.0.0.1` | pas d'exposition réseau directe, HTTPS obligatoire |
| méthodes limitées à GET/HEAD | tout le reste renvoie 405 |
| CSP `default-src 'none'` | la page n'a le droit de charger strictement rien |
| `X-Robots-Tag: noindex` | ne doit pas concurrencer handicap.gouv.fr dans Google |
| `mem_limit` 64 Mo / `pids_limit` 64 | plafonds sur une charge qui n'a besoin de rien |
| rotation des logs | pas de saturation du volume |

### Vérifié au banc

Testé le 26/07/2026, Docker 29.1.3 / Compose 2.40.3 :

| Contrôle | Résultat |
|---|---|
| État | `healthy` |
| `/healthz` | `ok` |
| Identité | `uid=101(nginx)` |
| Écriture racine web et `/etc` | refusée, *read-only file system* |
| Inspection | `CapDrop=[ALL]`, `no-new-privileges`, 64 Mo, 64 PID |
| `POST /` | 405 |
| Page inexistante | 404 |
| gzip | 30 Ko → 11,7 Ko |
| En-tête `Server` | `nginx` seul, pas de version |
| Page derrière la CSP réelle | fonctionnelle, zéro erreur console |
| Fichier en `644` / en `600` | 200 / 403 — voir « Permissions des fichiers » |

## Limites connues

**Pas de limitation de débit dans le conteneur.** Derrière un reverse proxy
local, toutes les requêtes arrivent avec l'IP source `127.0.0.1` : un `limit_req`
verrait un client unique et bloquerait tout le monde d'un coup. La protection
contre les abus appartient à l'hôte ou au reverse proxy, qui eux voient la vraie
IP source.

**Terminaison HTTPS non testée** : seul le conteneur l'a été. Reverse proxy,
certificat et DNS restent à valider sur l'hôte cible.

## Licence et réutilisation

Le **contenu clinique** (items, seuils, libellés) est repris du livret publié par
la Délégation interministérielle à la stratégie nationale pour les TND. C'est un
document public, diffusé pour être utilisé largement par les médecins de
première ligne. Il appartient à ses auteurs, pas à ce dépôt, et doit rester cité
comme tel.

Le **reste** — page HTML, configuration nginx, compose, scripts de
vérification — est librement réutilisable, sans condition. Reprends, adapte,
héberge chez toi.

Si tu redéploies cet outil, garde le bandeau d'avertissement de la page : il
protège autant tes utilisateurs que toi.

## Avertissement

Cette page **n'est pas le site officiel** et n'a aucun lien avec la Délégation
interministérielle, le GNCRA ou une quelconque administration. C'est une aide à
la saisie : elle ne pose aucun diagnostic et ne se substitue pas au jugement
clinique. Le document de référence reste le livret officiel.

Adresses des plateformes de coordination et d'orientation :
`ameli.fr/content/adresses-et-telephones-plateformes-de-coordination-et-d-orientation-pco`
