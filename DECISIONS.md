# Journal de décisions

Chaque choix ouvert du projet est consigné ici : option retenue, alternatives écartées, raison.
Ce journal alimente la section *Method* du README.

---

## D1 — Périmètre Hauts-de-France

- **Retenu :** périmètre défini par le GTFS publié par la Région (« Trains régionaux Hauts-de-France mobilités », 71 lignes, `route_id` identiques au GTFS national SNCF). Exclus : les lignes de cars (`route_type = 3` : P64 Laon–Hirson, K61 Charleville–Lille car) et les lignes vraisemblablement TER Grand Est desservant l'Aisne (K1 Paris–Strasbourg, K2 Paris–Saint-Dizier, C73 Château-Thierry–Reims, C76 Reims–Laon). **Périmètre final : 65 lignes ferroviaires.**
- **Écartés :** `agency_id` (l'agence 1187 couvre toute la France, l'agence 5235 seulement 10 lignes picardes) ; `route_short_name` (codes non uniques au niveau national : K12 = Paris–Lille et Nantes–Brest, K44 = Lille–Amiens et Lyon–Valence, P53 existe aussi en Grand Est).
- **Raison :** la Région est l'autorité organisatrice et le client fictif : son propre référentiel est la définition la plus défendable du périmètre.
- **À confirmer :** le rattachement de K1, K2, C73 et C76 au Grand Est.

## D2 — Clé de trajet

- **Retenu :** numéro de train + date de circulation. Le numéro de train figure dans `trip_headsign` (`trip_short_name` est vide) et s'extrait du `trip_id` par le motif `OCE[A-Z]{2}(\d+)` : préfixe `OCESN` pour l'agence 1187, `OCEEA` pour l'agence 5235 (lignes picardes). Le premier motif, `OCESN(\d+)`, ratait toutes les lignes de l'agence 5235 (constaté en phase 0, 27/09).
- **Écarté :** `trip_id` seul. Il contient un horodatage d'export (ex. `OCESN16350F8784835:2026-09-22T17:41:41Z`, 25 horodatages distincts dans un seul fichier) et change donc d'une version du GTFS à l'autre.
- **Raison :** une jointure sur un identifiant instable perdrait des trains sans erreur visible.
- **Statut :** provisoire, à valider contre le flux temps réel en phase 0 (voir `docs/phase0_feasibility.md`).

## D3 — Définition d'un « train prévu » au moment d'une observation

- **Retenu :** un train est prévu à l'instant T s'il est en circulation (départ théorique ≤ T ≤ arrivée théorique) ou si son départ théorique a lieu dans l'heure qui suit (T < départ ≤ T + 60 min).
- **Écarté :** trains en circulation uniquement. Sur 5 observations (23 au 26/09), 33 à 44 % des trains du flux n'étaient pas encore partis, tous dans les 60 min : les exclure du dénominateur gonflerait la couverture d'environ 60 %.
- **Raison :** le dénominateur doit correspondre à ce que le flux montre réellement. Fenêtre mesurée avec `src/phase0_fenetre_flux.py` ; elle confirme la documentation (« trains des 60 prochaines minutes »).
- **Limite :** les trains restent visibles 4 à 5 min après leur arrivée ; effet négligeable, non intégré. Mesure faite sur tous les trains de France, à confirmer pour les TER HdF.

## D4 — Cars de remplacement

- **Retenu :** les services assurés par car (mode `Car TER` dans l'identifiant d'arrêt du GTFS), même rangés sous une ligne ferroviaire, sont exclus des trains prévus. Seuls les trains sont mesurés.
- **Écarté :** les garder comme trains prévus absents. Le flux temps réel ne suit pas les cars : sur 3 observations (25 et 26/09), les 12 absents étaient tous des cars, sans aucune trace dans le flux. Ils seraient toujours comptés comme données manquantes.
- **Raison :** le projet porte sur la fiabilité des trains ; un car prévu au plan de transport n'est pas un train.
- **Limite :** les services par car (travaux) ne sont pas mesurés, à signaler dans les limites. Question ouverte pour la phase 3 : un train remplacé par un car compte-t-il comme une suppression pour le voyageur ?
