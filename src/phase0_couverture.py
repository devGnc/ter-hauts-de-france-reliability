"""
Phase 0 — Mesurer la couverture du flux GTFS-RT pour les TER Hauts-de-France.

Pour chaque photo déjà enregistrée dans data/snapshots/ :
  - dénominateur : trains HdF prévus à l'heure de la photo, selon D3
    (en circulation, ou départ dans l'heure qui suit) ;
  - numérateur : parmi eux, ceux qui apparaissent dans la photo, quel que soit
    leur statut (un train CANCELED présent dans le flux compte comme couvert) ;
  - les deux sources sont reliées par numéro de train + date de circulation (D2).

Lancement :  python src/phase0_couverture.py   (aucun téléchargement)
"""
import re
from pathlib import Path

import pandas as pd
from google.transit import gtfs_realtime_pb2

RACINE = Path(__file__).resolve().parent.parent
GTFS_DIR = RACINE / "data" / "gtfs_region"
SNAPSHOTS_DIR = RACINE / "data" / "snapshots"
LIGNES_EXCLUES = {"K1", "K2", "C73", "C76"}  # D1, même règle que phase0_lire_flux.py
FENETRE = pd.Timedelta(minutes=60)           # D3 : trains qui partent dans l'heure qui suit
# Colonnes de calendar.txt, dans l'ordre de dayofweek (0 = lundi ... 6 = dimanche)
JOURS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

# ---------------------------------------------------------------------------
# 1. Référentiel : les trains HdF, avec leur heure de départ et d'arrivée prévue
# ---------------------------------------------------------------------------
# dtype=str partout : on garde les valeurs telles qu'écrites dans les fichiers (pas de conversion)
routes = pd.read_csv(GTFS_DIR / "routes.txt", dtype=str)
routes = routes[(routes.route_type == "2") & ~routes.route_short_name.isin(LIGNES_EXCLUES)]

trips = pd.read_csv(GTFS_DIR / "trips.txt", dtype=str)
trips = trips[trips.route_id.isin(routes.route_id)]
trips = trips.merge(routes[["route_id", "route_short_name"]], on="route_id")  # ajoute le nom de ligne
trips = trips.rename(columns={"trip_headsign": "num"})  # D2 : le numéro de train est dans trip_headsign

# Premier départ et dernière arrivée de chaque trajet, d'après stop_times.txt
stop_times = pd.read_csv(GTFS_DIR / "stop_times.txt", dtype=str,
                         usecols=["trip_id", "arrival_time", "departure_time", "stop_sequence"])
stop_times = stop_times[stop_times.trip_id.isin(trips.trip_id)]
stop_times["stop_sequence"] = stop_times["stop_sequence"].astype(int)  # pour trier 10 après 9
extremites = (stop_times.sort_values(["trip_id", "stop_sequence"])
              .groupby("trip_id")
              .agg(depart=("departure_time", "first"), arrivee=("arrival_time", "last"))
              .reset_index())
trips = trips.merge(extremites, on="trip_id")

calendar = pd.read_csv(GTFS_DIR / "calendar.txt", dtype=str)
calendar_dates = pd.read_csv(GTFS_DIR / "calendar_dates.txt", dtype=str)


def services_actifs(jour):
    """Ensemble des service_id qui circulent le jour donné."""
    date = jour.strftime("%Y%m%d")  # même format que les fichiers : 20260923
    # Règle générale (calendar.txt) : dans la période de validité ET le bon jour de la semaine
    regle = calendar[(calendar.start_date <= date) & (date <= calendar.end_date)
                     & (calendar[JOURS[jour.dayofweek]] == "1")]
    actifs = set(regle.service_id)
    # Exceptions (calendar_dates.txt) : 1 = service ajouté ce jour-là, 2 = service retiré
    exceptions = calendar_dates[calendar_dates.date == date]
    actifs |= set(exceptions[exceptions.exception_type == "1"].service_id)
    actifs -= set(exceptions[exceptions.exception_type == "2"].service_id)
    return actifs


def trains_du_jour(jour):
    """Trains HdF qui circulent le jour donné, avec départ et arrivée en vraies dates (heure de Paris)."""
    du_jour = trips[trips.service_id.isin(services_actifs(jour))].copy()
    # Les heures GTFS comptent depuis le début de la journée de service et peuvent dépasser
    # 24:00 (25:10:00 = 1 h 10 le lendemain) : on les ajoute à minuit comme des durées.
    # Approximation : décalage d'1 h possible les jours de changement d'heure (25/10/2026).
    minuit = jour.tz_localize("Europe/Paris")
    du_jour["depart"] = minuit + pd.to_timedelta(du_jour["depart"])
    du_jour["arrivee"] = minuit + pd.to_timedelta(du_jour["arrivee"])
    du_jour["date"] = jour.strftime("%Y%m%d")  # date de circulation, au format du flux (start_date)
    return du_jour[["num", "date", "route_short_name", "depart", "arrivee"]]


def numero_train(trip_id):
    """Extrait le numéro de train du trip_id du flux : 'OCESN5789F1187_F:...' -> '5789'."""
    m = re.search(r"OCESN(\d+)", trip_id)
    return m.group(1) if m else None


Statut = gtfs_realtime_pb2.TripDescriptor.ScheduleRelationship
resume = []

for fichier in sorted(SNAPSHOTS_DIR.glob("*.pb")):
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(fichier.read_bytes())
    t_photo = pd.to_datetime(feed.header.timestamp, unit="s", utc=True).tz_convert("Europe/Paris")
    jour = t_photo.normalize().tz_localize(None)  # date de la photo, à minuit, sans fuseau

    # -----------------------------------------------------------------------
    # 2. Dénominateur : trains prévus selon D3 (départ <= photo + 60 min ET arrivée >= photo)
    # -----------------------------------------------------------------------
    # On inclut la veille : un train parti avant minuit peut encore rouler (heures > 24:00)
    prevus_jour = pd.concat([trains_du_jour(jour - pd.Timedelta(days=1)), trains_du_jour(jour)])
    prevus = prevus_jour[(prevus_jour.depart <= t_photo + FENETRE) & (prevus_jour.arrivee >= t_photo)]
    # Un même numéro + date décrit deux fois dans le GTFS ne doit compter qu'une fois
    doublons = prevus.duplicated(["num", "date"]).sum()
    prevus = prevus.drop_duplicates(["num", "date"])

    # -----------------------------------------------------------------------
    # 3. Trains présents dans la photo : dictionnaire (numéro, date) -> statut
    # -----------------------------------------------------------------------
    presents = {}
    for entite in feed.entity:
        if entite.HasField("trip_update"):
            trip = entite.trip_update.trip
            num = numero_train(trip.trip_id)
            if num is not None:
                presents[(num, trip.start_date)] = Statut.Name(trip.schedule_relationship)

    # -----------------------------------------------------------------------
    # 4. Numérateur : trains prévus retrouvés dans la photo (jointure D2 : numéro + date)
    # -----------------------------------------------------------------------
    cles = list(zip(prevus.num, prevus.date))
    prevus = prevus.assign(statut=[presents.get(cle) for cle in cles])  # None si absent
    couverts = prevus[prevus.statut.notna()]
    absents = prevus[prevus.statut.isna()]
    # Contrôle de D3 : trains HdF du jour présents dans la photo mais hors de la fenêtre
    cles_du_jour = set(zip(prevus_jour.num, prevus_jour.date))
    cles_prevues = set(cles)
    hors_fenetre = sum(1 for cle in presents if cle in cles_du_jour and cle not in cles_prevues)

    couverture = len(couverts) / len(prevus) if len(prevus) else float("nan")
    print(f"\n=== Photo du {t_photo:%d/%m à %H:%M} (heure de Paris) ===")
    print(f"Trains HdF prévus (D3)         : {len(prevus)}")
    print(f"  dont présents dans le flux   : {len(couverts)}  -> couverture {couverture:.0%}")
    print(f"     statuts : {couverts.statut.value_counts().to_dict()}")
    print(f"  dont absents du flux         : {len(absents)}")
    print(f"     lignes les plus touchées : {absents.route_short_name.value_counts().head(5).to_dict()}")
    print(f"Trains HdF du flux hors fenêtre D3 : {hors_fenetre}")
    print(f"Doublons numéro + date écartés     : {doublons}")
    resume.append({"photo": f"{t_photo:%d/%m %H:%M}", "prevus": len(prevus),
                   "presents": len(couverts), "couverture": f"{couverture:.0%}"})

print("\n=== Résumé ===")
print(pd.DataFrame(resume).to_string(index=False))
