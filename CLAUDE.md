# CLAUDE.md — contexte du projet

## Le projet

Projet de portfolio data d'un étudiant (EDHEC PGE, double diplôme Centrale Lille), lié à la recherche d'un stage à l'étranger (été 2027). **Livrable V1 avant fin janvier 2027**, période de publication des offres « summer 2027 » ; V2 mise à jour en février.

**Question centrale :** quelles lignes TER Hauts-de-France sont les moins fiables, à quels moments, et où la Région devrait-elle concentrer ses efforts ?
Cadrage conseil : la Région est un client fictif. Le projet se conclut par 3 recommandations chiffrées au maximum.

**Principe :** aucune source publique ne donne la régularité par ligne TER. Le dataset est reconstruit en archivant le flux GTFS-RT SNCF pendant 4 à 8 semaines, puis analysé en SQL et restitué dans Power BI.

**Chaîne technique :** Python (collecte et chargement uniquement) → PostgreSQL sur Supabase (plan gratuit, 500 Mo) → vues SQL (toute la logique d'analyse) → Power BI Desktop.

**Hors périmètre :** prédiction des retards (machine learning) et analyse des causes.

## Règles de travail

- **L'auteur doit pouvoir expliquer chaque ligne de code en entretien.** Code commenté en français, de façon pédagogique mais sans excès. Tout choix technique non évident est expliqué en une ou deux phrases dans la réponse.
- **Ne jamais construire les phases suivantes à l'avance.** Les choix ouverts appartiennent à l'auteur : quelle observation fait foi, définition d'un train supprimé, seuils, trous de collecte, etc. Proposer des options, ne pas trancher.
- Aucune donnée brute commitée (licence ODbL, licence régionale non spécifiée). Aucun identifiant dans le code : tout passe par des variables d'environnement (`.env`, voir `.env.example`).
- Chaque décision va dans `DECISIONS.md` : option retenue, alternatives écartées, raison, en 2 à 4 lignes.
- README, `DECISIONS.md` et `docs/` en anglais (nombres au format anglais : 26.0, 1,200). Code, commentaires et ce fichier en français.
- **Commits :** auteur `Devrim Genc <144224875+devGnc@users.noreply.github.com>` (configuré dans le `git config` du dépôt ; le vérifier au début de chaque session). Messages en anglais, commits petits et explicites. **Aucun trailer** dans les messages : ni `Co-Authored-By`, ni `Claude-Session`.

## Sources

- GTFS-RT Trip Updates SNCF, toutes activités (TGV, Intercités, TER ; ressource transport.data.gouv.fr n° 83583) : `https://proxy.transport.data.gouv.fr/resource/sncf-gtfs-rt-trip-updates`. Vérifié le 23/09/2026 : les URL `sncf-all-gtfs-rt-trip-updates` et `sncf-ter-gtfs-rt-trip-updates` renvoient **404**, ne pas les utiliser.
- GTFS Région Hauts-de-France : `https://transport.data.gouv.fr/resources/83620/download` (à dézipper dans `data/gtfs_region/`).
- GTFS TER national SNCF (contrôle croisé, ODbL) : `https://eu.ftp.opendatasoft.com/sncf/plandata/export-ter-gtfs-last.zip`.
- Régularité mensuelle TER (SNCF Open Data, seuil de 5 min au terminus) : référence pour la phase 3.

## Décisions prises

- **D1 — Périmètre :** GTFS de la Région, 71 lignes, `route_id` identiques au GTFS national. Exclus : cars (`route_type = 3`) et K1, K2, C73, C76 (vraisemblablement Grand Est, à confirmer). **65 lignes ferroviaires.** `agency_id` et `route_short_name` sont écartés comme critères (non discriminants ou non uniques).
- **D2 — Clé de trajet :** numéro de train + date de circulation. Le `trip_id` contient un horodatage d'export et change entre les versions. Le numéro est dans `trip_headsign` et s'extrait du `trip_id` par `OCE[A-Z]{2}(\d+)` (préfixe `OCESN` agence 1187, `OCEEA` agence 5235 ; `OCESN(\d+)` seul ratait toutes les lignes picardes). **Validée** le 22/11/2026 : 0 correspondance exacte sur `trip_id`, 404/404 par numéro + date (série 1), 62/62 et 61/61 sur le GTFS actuel.
- **D3 — Train prévu à l'instant T :** en circulation (départ ≤ T ≤ arrivée, horaires théoriques) ou départ dans l'heure qui suit (T < départ ≤ T + 60 min). Fenêtre mesurée sur 5 observations avec `src/phase0_fenetre_flux.py` (33 à 44 % des trains du flux pas encore partis ; trains visibles 4 à 5 min après l'arrivée, non intégré).
- **D4 — Cars de remplacement :** les trajets dont le mode est `Car TER` (lu dans le `stop_id` du GTFS) sont exclus des trains prévus, même sous une ligne ferroviaire : le flux ne suit presque pas les cars (1 sur 13 observés).
- **D5 — Intervalle de collecte :** une photo toutes les 2 min (les trains quittent le flux 4 à 5 min après leur arrivée ; le flux est rafraîchi toutes les 2 min selon sa documentation).
- **D6 — Vacances de Noël et gel V1 :** collecte sans interruption dès le 13/12 ; chaque jour étiqueté (normal, vacances scolaires 19/12–04/01 à confirmer, férié) ; chiffres principaux et recommandations sur les jours normaux, vacances en segment à part. Gel des données V1 le 17/01/2027, collecte poursuivie jusqu'à 8 semaines pour une V2 en février.
- **D7 — Hébergement :** VM Google Cloud e2-micro (offre gratuite), zone `us-east1-b`, Debian 13, disque standard de 30 Go, sans compte de service. Créée le 22/11/2026 pendant l'essai gratuit (300 $, jusqu'au ~20/02/2027) ; alerte de budget à 1, 5 et 10 €/mois (coût avant crédits). Identifiants (projet, IP, facturation) hors du dépôt. Le collecteur n'est pas encore installé.

Détail complet : `DECISIONS.md`.

## Pièges connus

- **Heures :** le GTFS statique est en heure locale, avec des heures possibles au-delà de 24:00:00. Le GTFS-RT est en horodatages Unix UTC. Harmoniser avant tout calcul. Changement d'heure fin octobre (25/10/2026).
- **Doublons :** un même train apparaît dans des dizaines d'observations successives. Compter les lignes brutes surestime tout.
- **Absence ≠ ponctualité :** un train prévu absent du flux est une donnée manquante, pas un train à l'heure.
- **Identifiants instables :** voir D2. Une jointure qui perd des trains en silence fausse tous les résultats.
- **GitHub Actions :** les tâches planifiées peuvent être retardées ou sautées. Vérifier leurs limites avant de choisir : fréquence minimale, quotas public/privé, désactivation après inactivité.
- **Stockage :** dimensionner dès la phase 0 par rapport aux 500 Mo de Supabase.
- **GTFS en fenêtre glissante :** le GTFS régional couvre ~90 jours à partir de sa date de publication ; les jours passés en sortent. Archiver chaque version (`data/gtfs_archive/`).
- **Suppressions effacées après coup :** une version plus récente du GTFS retire les trains supprimés (constaté : 8 `CANCELED` → 1 pour le 25/09 18 h). Un GTFS publié après les faits sous-estime les suppressions : choisir quelle version fait foi (décision à venir).
- **Fin de l'essai Google Cloud (~20/02/2027, date exacte dans Facturation → Vue d'ensemble) :** ne **jamais** passer en compte payant (seul moyen d'être débité). Collecte terminée vers le 07/02, données rapatriées puis VM supprimée avant la fin de l'essai ; sinon Google arrête la VM sans débiter. Seul le projet « Collecteur TER » est relié à la facturation (vérifié le 22/11).
- **Qualité du flux :** le validateur de transport.data.gouv.fr signalait de nombreuses erreurs sur le flux national (mars 2026). Prévoir du nettoyage.

## Phase en cours

**Phase 0 — Test de faisabilité** (septembre – novembre 2026).
Scripts : `src/phase0_lire_flux.py` (une photo), `src/phase0_fenetre_flux.py` (fenêtre du flux), `src/phase0_couverture.py` (couverture), `src/phase0_mesure.sh` (les trois en une commande, sorties dans `data/mesures/`). Rapport : `docs/phase0_feasibility.md`. Série 1 (23–26/09) : 404/404 trains HdF prévus présents. Série 2 sur le GTFS du 21/11 (archivé) : week-end fait le 22/11 (62/62 et 61/61) ; restent les créneaux de semaine (pointe du matin, heure creuse, pointe du soir), à lancer par l'auteur avec `./src/phase0_mesure.sh` avant le 12/12. Restent ensuite la décision go / no-go de l'auteur, puis le choix de ce qu'on garde sur le disque et le collecteur (intervalle 2 min, D5 ; VM prête, D7).
En cas de no-go : examiner le flux SIRI ET Lite et un éventuel flux régional, puis, en dernier recours, basculer sur une comparaison des régions à partir des données mensuelles.

**Environnement cloud :** l'environnement « ter-hauts-de-france-reliability » autorise proxy.transport.data.gouv.fr, transport.data.gouv.fr et eu.ftp.opendatasoft.com. L'environnement par défaut bloque ces sources : démarrer les sessions qui ont besoin du flux sur le premier.

## Calendrier

| Période | Phase |
| --- | --- |
| Novembre – 12/12/2026 | 0 : fin de la série 2, go / no-go ; hébergement ; collecteur testé dès début décembre ; 1 : référentiel statique en base |
| 13/12/2026 | 2 : début de la collecte, au changement de service annuel (nuit du 12 au 13/12) |
| 13/12/2026 – 17/01/2027 | 3 et 4 : vues SQL et tableau Power BI construits pendant la collecte, sur les données déjà arrivées |
| 17/01/2027 | Gel des données de la V1 : 5 semaines, dont environ 3 en période normale (D6) |
| 18/01 – fin janvier 2027 | 5 et 6 : calculs finaux, 3 recommandations, README, note de synthèse, pitch de 2 min → **V1 publiée** |
| Jusqu'à ~07/02/2027 | Collecte poursuivie jusqu'à 8 semaines → **V2** mise à jour en février |

## Arborescence

```
src/              scripts Python (collecte, chargement)
sql/00_schema/    création des tables
sql/01_reference/ référentiel statique
sql/03_transform/ transformations
sql/04_analysis/  une requête commentée par sous-question
docs/             phase0_feasibility.md, data_quality.md
dashboard/        fichier Power BI et captures
data/             données locales, ignorées par git (gtfs_region/, snapshots/)
```
