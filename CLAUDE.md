# CLAUDE.md — contexte du projet

## Le projet

Projet de portfolio data d'un étudiant (EDHEC PGE, double diplôme Centrale Lille), à présenter début janvier 2027 pour un stage à l'étranger.

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
- README en anglais. Code, commentaires et documents internes en français.

## Sources

- GTFS-RT Trip Updates SNCF, toutes activités : `https://proxy.transport.data.gouv.fr/resource/sncf-all-gtfs-rt-trip-updates`. L'ancienne URL `sncf-ter-gtfs-rt-trip-updates` est **obsolète** et ne couvre pas tous les TER.
- GTFS Région Hauts-de-France : `https://transport.data.gouv.fr/resources/83620/download` (à dézipper dans `data/gtfs_region/`).
- GTFS TER national SNCF (contrôle croisé, ODbL) : `https://eu.ftp.opendatasoft.com/sncf/plandata/export-ter-gtfs-last.zip`.
- Régularité mensuelle TER (SNCF Open Data, seuil de 5 min au terminus) : référence pour la phase 3.

## Décisions prises

- **D1 — Périmètre :** GTFS de la Région, 71 lignes, `route_id` identiques au GTFS national. Exclus : cars (`route_type = 3`) et K1, K2, C73, C76 (vraisemblablement Grand Est, à confirmer). **65 lignes ferroviaires.** `agency_id` et `route_short_name` sont écartés comme critères (non discriminants ou non uniques).
- **D2 — Clé de trajet :** numéro de train + date de circulation. Le `trip_id` contient un horodatage d'export et change entre les versions. Le numéro est dans `trip_headsign` et s'extrait du `trip_id` par `OCESN(\d+)`. Provisoire : à valider contre le flux en phase 0.

Détail complet : `DECISIONS.md`.

## Pièges connus

- **Heures :** le GTFS statique est en heure locale, avec des heures possibles au-delà de 24:00:00. Le GTFS-RT est en horodatages Unix UTC. Harmoniser avant tout calcul. Changement d'heure fin octobre (25/10/2026).
- **Doublons :** un même train apparaît dans des dizaines d'observations successives. Compter les lignes brutes surestime tout.
- **Absence ≠ ponctualité :** un train prévu absent du flux est une donnée manquante, pas un train à l'heure.
- **Identifiants instables :** voir D2. Une jointure qui perd des trains en silence fausse tous les résultats.
- **GitHub Actions :** les tâches planifiées peuvent être retardées ou sautées. Vérifier leurs limites avant de choisir : fréquence minimale, quotas public/privé, désactivation après inactivité.
- **Stockage :** dimensionner dès la phase 0 par rapport aux 500 Mo de Supabase.
- **Qualité du flux :** le validateur de transport.data.gouv.fr signalait de nombreuses erreurs sur le flux national (mars 2026). Prévoir du nettoyage.

## Phase en cours

**Phase 0 — Test de faisabilité** (fin septembre – début octobre 2026).
Script : `src/phase0_lire_flux.py`. Rapport à remplir : `docs/phase0_feasibility.md`. Livrable : une décision go / no-go écrite.
En cas de no-go : examiner le flux SIRI ET Lite et un éventuel flux régional, puis, en dernier recours, basculer sur une comparaison des régions à partir des données mensuelles.

## Calendrier

| Période | Phase |
| --- | --- |
| Fin septembre – début octobre | 0 : faisabilité, go / no-go |
| Octobre | 1 : référentiel statique en base |
| Mi-octobre – mi-décembre | 2 : collecte continue (4 semaines min., idéalement 8) |
| Novembre – décembre | 3 et 4 : transformations, analyses SQL |
| Décembre – début janvier | 5 : Power BI ; 6 : recommandations, README, note de synthèse, pitch de 2 min |

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
