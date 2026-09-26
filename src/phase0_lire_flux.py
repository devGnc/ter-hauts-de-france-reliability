"""
Phase 0 — Lire le flux GTFS-RT Trip Updates SNCF et tester la correspondance
avec le GTFS publié par la Région Hauts-de-France.

Installation :  pip install -r requirements.txt
Lancement (depuis n'importe quel dossier) :  python src/phase0_lire_flux.py
Arborescence attendue (data/ n'est jamais commité) :
    data/gtfs_region/routes.txt   (fichiers du GTFS régional, noms sans préfixe)
    data/gtfs_region/trips.txt
Les observations brutes sont écrites dans data/snapshots/.
"""
import re
import time
from pathlib import Path

import pandas as pd
import requests
from google.transit import gtfs_realtime_pb2

# Flux national (TGV, Intercités, TER). Les variantes "sncf-all-..." et "sncf-ter-..." renvoient 404.
URL = "https://proxy.transport.data.gouv.fr/resource/sncf-gtfs-rt-trip-updates"
# Chemins construits à partir de l'emplacement du script (src/ -> racine du dépôt),
# pour que le script fonctionne quel que soit le dossier d'où on le lance.
RACINE = Path(__file__).resolve().parent.parent
GTFS_DIR = RACINE / "data" / "gtfs_region"
SNAPSHOTS_DIR = RACINE / "data" / "snapshots"
LIGNES_EXCLUES = {"K1", "K2", "C73", "C76"}  # décision D1 (vraisemblablement Grand Est)

# ---------------------------------------------------------------------------
# 1. Télécharger une observation et la garder telle quelle (donnée brute)
# ---------------------------------------------------------------------------
reponse = requests.get(URL, timeout=30)
reponse.raise_for_status()

SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)  # parents=True : crée aussi data/ s'il manque
fichier = SNAPSHOTS_DIR / f"tu_{int(time.time())}.pb"
fichier.write_bytes(reponse.content)
print(f"Taille d'une observation : {len(reponse.content) / 1024:.0f} Ko")  # -> dimensionnement

# ---------------------------------------------------------------------------
# 2. Décoder le Protocol Buffers en objet Python
# ---------------------------------------------------------------------------
feed = gtfs_realtime_pb2.FeedMessage()
feed.ParseFromString(reponse.content)

print("Horodatage du flux (UTC) :", pd.to_datetime(feed.header.timestamp, unit="s", utc=True))
print("Nombre d'entités :", len(feed.entity))
print("\n--- Une entité brute, pour voir la structure ---")
print(feed.entity[0])

# ---------------------------------------------------------------------------
# 3. Aplatir : une ligne par train (niveau trajet)
# ---------------------------------------------------------------------------
Statut = gtfs_realtime_pb2.TripDescriptor.ScheduleRelationship
lignes = []
for entite in feed.entity:
    if not entite.HasField("trip_update"):
        continue
    tu = entite.trip_update
    dernier = tu.stop_time_update[-1] if tu.stop_time_update else None
    lignes.append({
        "trip_id": tu.trip.trip_id,
        "start_date": tu.trip.start_date,
        "statut": Statut.Name(tu.trip.schedule_relationship),  # SCHEDULED, CANCELED...
        "nb_arrets_maj": len(tu.stop_time_update),
        # Le champ delay est optionnel : on vérifie s'il est rempli avant de le lire
        "retard_dernier_arret_s": (
            dernier.arrival.delay
            if dernier is not None and dernier.HasField("arrival") and dernier.arrival.HasField("delay")
            else None
        ),
    })
rt = pd.DataFrame(lignes)

# ---------------------------------------------------------------------------
# 4. Correspondance avec le périmètre Hauts-de-France (65 lignes)
# ---------------------------------------------------------------------------
routes = pd.read_csv(GTFS_DIR / "routes.txt")
routes = routes[(routes.route_type == 2) & ~routes.route_short_name.isin(LIGNES_EXCLUES)]
trips = pd.read_csv(GTFS_DIR / "trips.txt", dtype=str)
trips = trips[trips.route_id.isin(routes.route_id)]


def numero_train(trip_id):
    """Extrait le numéro de train : 'OCESN16350F8784835:...' -> '16350'.

    Le préfixe varie selon l'agence : OCESN (agence 1187) ou OCEEA (agence 5235, lignes
    picardes). [A-Z]{2} accepte n'importe quelles deux lettres majuscules après 'OCE'.
    """
    m = re.search(r"OCE[A-Z]{2}(\d+)", trip_id)
    return m.group(1) if m else None


rt["num_train"] = rt["trip_id"].map(numero_train)
rt["match_trip_id"] = rt["trip_id"].isin(trips["trip_id"])
rt["match_num_train"] = rt["num_train"].isin(set(trips["trip_headsign"]))

print("\n--- Résultats ---")
print("Trains dans le flux (toutes régions) :", len(rt))
print("Statuts :", rt["statut"].value_counts().to_dict())
print("trip_id sans numéro extractible :", rt["num_train"].isna().sum())
print("Correspondance exacte sur trip_id :", rt["match_trip_id"].sum())
print("Correspondance sur numéro de train :", rt["match_num_train"].sum())
print("Delay renseigné (part des trains) :", round(rt["retard_dernier_arret_s"].notna().mean(), 2))

print("\nExemples de trip_id du flux :", rt["trip_id"].head(5).tolist())
