# Phase 0 — Test de faisabilité

**Date(s) des tests :** …
**Version du GTFS régional utilisée :** … (date de téléchargement)
**Script :** `src/phase0_lire_flux.py`

---

## 1. Couverture : trains HdF prévus vs présents dans le flux

Mesurer à plusieurs heures (pointe du matin, heure creuse, pointe du soir, week-end) pour éviter une conclusion fondée sur un seul instant.

| Date et heure (locale) | Trains HdF prévus dans les 60 min | Trains HdF présents dans le flux | Taux de couverture | Remarques |
| --- | --- | --- | --- | --- |
| … | … | … | … % | … |
| … | … | … | … % | … |
| … | … | … | … % | … |
| … | … | … | … % | … |

**Méthode de comptage des trains prévus :** …

**Constat :** …

## 2. Correspondance `trip_id` / numéro de train (validation de D2)

| Indicateur | Valeur |
| --- | --- |
| Trains dans le flux (toutes régions) | … |
| `trip_id` sans numéro extractible (`OCESN(\d+)`) | … |
| Correspondance exacte sur `trip_id` | … |
| Correspondance sur numéro de train | … |
| Exemples de `trip_id` du flux | … |

**Le format des `trip_id` du flux est-il le même que celui du GTFS statique ?** …

**Conclusion sur D2 (confirmée / à revoir) :** …

## 3. Renseignement des retards : `delay` vs `time`

Dans GTFS-RT, un `StopTimeEvent` peut contenir un `delay` (écart en secondes), un `time` (horodatage absolu), ou les deux.

| Indicateur | Valeur |
| --- | --- |
| Part des trains avec `delay` renseigné (dernier arrêt) | … % |
| Part des trains avec `time` renseigné (dernier arrêt) | … % |
| Part des trains sans aucun des deux | … % |
| Statuts observés (`SCHEDULED`, `CANCELED`, …) | … |

**Conséquence pour le calcul du retard :** …

## 4. Volume de stockage

| Indicateur | Valeur |
| --- | --- |
| Taille d'une observation brute (`.pb`) | … Ko |
| Observations par jour (1 toutes les … min) | … |
| Volume brut sur 8 semaines | … Mo |
| Volume estimé après filtrage HdF / mise en table | … Mo |
| Quota Supabase (plan gratuit) | 500 Mo |

**Calcul détaillé :** …

**Le volume tient-il dans le quota ? Sinon, quelle stratégie de réduction sans perte d'information ?** …

## 5. Décision

- [ ] **Go**
- [ ] **No-go** : pistes alternatives (SIRI ET Lite, flux régional, comparaison des régions sur données mensuelles)

**Justification (3 à 5 lignes) :** …

**Décisions à reporter dans `DECISIONS.md` :** …
