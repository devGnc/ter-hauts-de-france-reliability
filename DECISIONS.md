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

- **Retenu :** numéro de train + date de circulation. Le numéro de train figure dans `trip_headsign` (`trip_short_name` est vide) et s'extrait du `trip_id` par le motif `OCESN(\d+)`.
- **Écarté :** `trip_id` seul. Il contient un horodatage d'export (ex. `OCESN16350F8784835:2026-09-22T17:41:41Z`, 25 horodatages distincts dans un seul fichier) et change donc d'une version du GTFS à l'autre.
- **Raison :** une jointure sur un identifiant instable perdrait des trains sans erreur visible.
- **Statut :** provisoire, à valider contre le flux temps réel en phase 0 (voir `docs/phase0_feasibility.md`).
