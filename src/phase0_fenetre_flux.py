"""
Phase 0 — Mesurer la fenêtre temporelle réelle du flux GTFS-RT.

Pour chaque photo déjà enregistrée dans data/snapshots/, on regarde où se situent
le départ et l'arrivée de chaque train par rapport à l'heure de la photo.
But : savoir quels trains le flux montre vraiment (en circulation seulement ?
aussi ceux qui partent dans l'heure ?) pour choisir la définition de « train prévu » (D3).

Lancement :  python src/phase0_fenetre_flux.py   (aucun téléchargement)
"""
from pathlib import Path

import pandas as pd
from google.transit import gtfs_realtime_pb2

RACINE = Path(__file__).resolve().parent.parent
SNAPSHOTS_DIR = RACINE / "data" / "snapshots"

# Tranches d'écart, en minutes par rapport à l'heure de la photo (négatif = avant la photo)
TRANCHES = [-float("inf"), -60, 0, 60, float("inf")]
NOMS_DEPART = ["parti depuis plus d'1 h", "parti dans la dernière heure",
               "part dans l'heure à venir", "part dans plus d'1 h"]
NOMS_ARRIVEE = ["arrivé depuis plus d'1 h", "arrivé dans la dernière heure",
                "arrive dans l'heure à venir", "arrive dans plus d'1 h"]


def heure_depart(arret):
    """Heure de départ d'un arrêt (à défaut, d'arrivée), en horodatage Unix. None si absente."""
    if arret.HasField("departure") and arret.departure.HasField("time"):
        return arret.departure.time
    if arret.HasField("arrival") and arret.arrival.HasField("time"):
        return arret.arrival.time
    return None


def heure_arrivee(arret):
    """Heure d'arrivée d'un arrêt (à défaut, de départ), en horodatage Unix. None si absente."""
    if arret.HasField("arrival") and arret.arrival.HasField("time"):
        return arret.arrival.time
    if arret.HasField("departure") and arret.departure.HasField("time"):
        return arret.departure.time
    return None


# sorted() : les noms contiennent l'horodatage, donc les photos sortent dans l'ordre chronologique
for fichier in sorted(SNAPSHOTS_DIR.glob("*.pb")):
    # 1. Relire la photo enregistrée (même décodage que dans phase0_lire_flux.py)
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(fichier.read_bytes())
    t_photo = feed.header.timestamp

    # 2. Pour chaque train : écart (en minutes) entre la photo et son départ / son arrivée
    ecarts = []
    for entite in feed.entity:
        # On ignore les entités sans train ou sans arrêt (certains trains supprimés n'en ont pas)
        if not entite.HasField("trip_update") or not entite.trip_update.stop_time_update:
            continue
        arrets = entite.trip_update.stop_time_update
        depart = heure_depart(arrets[0])      # premier arrêt = gare de départ
        arrivee = heure_arrivee(arrets[-1])   # dernier arrêt = terminus
        ecarts.append({
            "depart_min": (depart - t_photo) / 60 if depart is not None else None,
            "arrivee_min": (arrivee - t_photo) / 60 if arrivee is not None else None,
        })
    df = pd.DataFrame(ecarts, dtype=float)

    # 3. Ranger les écarts dans les tranches et afficher le décompte
    heure_paris = pd.to_datetime(t_photo, unit="s", utc=True).tz_convert("Europe/Paris")
    print(f"\n=== Photo du {heure_paris:%d/%m à %H:%M} (heure de Paris) : {len(df)} trains ===")
    for colonne, noms, titre in [("depart_min", NOMS_DEPART, "Départ du train"),
                                 ("arrivee_min", NOMS_ARRIVEE, "Arrivée du train")]:
        tranches = pd.cut(df[colonne], bins=TRANCHES, labels=noms)
        print(f"\n{titre} par rapport à la photo :")
        print(tranches.value_counts(sort=False).to_string())
        print(f"sans heure renseignée : {df[colonne].isna().sum()}")

    # 4. Les extrêmes : jusqu'où le flux regarde en avant, et combien de temps il garde un train arrivé
    print(f"\nDépart le plus lointain : {df['depart_min'].max():+.0f} min")
    print(f"Arrivée la plus ancienne : {df['arrivee_min'].min():+.0f} min")
