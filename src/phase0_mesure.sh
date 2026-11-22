#!/bin/bash
# Phase 0, série 2 — une mesure complète à un créneau donné, en une commande.
#
#   1. phase0_lire_flux.py    télécharge une photo du flux, mesure delay / time et le trip_id ;
#   2. phase0_couverture.py   recalcule la couverture HdF sur toutes les photos de data/snapshots/ ;
#   3. phase0_fenetre_flux.py vérifie la fenêtre du flux (D3) et la visibilité après l'arrivée.
#
# Les sorties s'affichent à l'écran et sont gardées dans data/mesures/ (ignoré par git),
# avec la date et l'heure dans le nom du fichier.
# Le GTFS régional utilisé est celui de data/gtfs_region/ : ne pas le changer pendant la série.
#
# Lancement, depuis n'importe quel dossier :  ./src/phase0_mesure.sh

# -e : arrêt à la première erreur (ex. flux indisponible) ;
# -o pipefail : une erreur de Python n'est pas masquée par le « | tee » qui suit.
set -eo pipefail

RACINE="$(cd "$(dirname "$0")/.." && pwd)"   # dossier du dépôt, quel que soit le dossier courant
PYTHON="$RACINE/.venv/bin/python"            # Python de l'environnement virtuel du projet
SORTIES="$RACINE/data/mesures"
HORODATAGE="$(date +%Y%m%d_%H%M)"            # ex. 20261124_0745 (heure locale du Mac)

mkdir -p "$SORTIES"
for script in lire_flux couverture fenetre_flux; do
    echo "===== phase0_$script.py ====="
    "$PYTHON" "$RACINE/src/phase0_$script.py" | tee "$SORTIES/${script}_$HORODATAGE.txt"
done
echo "Sorties enregistrées dans $SORTIES (suffixe $HORODATAGE)"
