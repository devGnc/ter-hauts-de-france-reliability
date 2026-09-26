"""
Phase 0 — Mesurer la couverture du flux GTFS-RT pour les TER Hauts-de-France.

Pour chaque photo déjà enregistrée dans data/snapshots/ :
  - dénominateur : trains HdF prévus à l'heure de la photo, selon D3
    (en circulation, ou départ dans l'heure qui suit), cars de remplacement exclus (D4) ;
  - numérateur : parmi eux, ceux qui apparaissent dans la photo, quel que soit
    leur statut (un train CANCELED présent dans le flux compte comme couvert) ;
  - les deux sources sont reliées par numéro de train + date de circulation (D2).

La liste des trains prévus mais absents est enregistrée dans data/phase0_absents.csv.

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
                         usecols=["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"])
stop_times = stop_times[stop_times.trip_id.isin(trips.trip_id)]
stop_times["stop_sequence"] = stop_times["stop_sequence"].astype(int)  # pour trier 10 après 9
extremites = (stop_times.sort_values(["trip_id", "stop_sequence"])
              .groupby("trip_id")
              .agg(depart=("departure_time", "first"), arrivee=("arrival_time", "last"),
                   premier_arret=("stop_id", "first"))
              .reset_index())
trips = trips.merge(extremites, on="trip_id")
# Mode de transport, lu dans l'identifiant d'arrêt : 'StopPoint:OCETrain TER-87...' -> 'Train TER'
# (un car de remplacement apparaîtrait comme 'Car TER' même s'il est rangé sous une ligne ferroviaire)
trips["mode"] = trips["premier_arret"].str.extract(r"OCE(.*?)-", expand=False)

calendar = pd.read_csv(GTFS_DIR / "calendar.txt", dtype=str)
calendar_dates = pd.read_csv(GTFS_DIR / "calendar_dates.txt", dtype=str)

# Le GTFS est une fenêtre glissante (~90 jours) : on affiche la version utilisée
feed_info = pd.read_csv(GTFS_DIR / "feed_info.txt", dtype=str)
print("Version du GTFS régional :", feed_info.iloc[0].to_dict())


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
    return du_jour[["num", "date", "route_short_name", "mode", "depart", "arrivee"]]


def numero_train(trip_id):
    """Extrait le numéro de train du trip_id du flux : 'OCESN5789F1187_F:...' -> '5789'.

    Le préfixe varie selon l'agence : OCESN (agence 1187) ou OCEEA (agence 5235, lignes
    picardes). [A-Z]{2} accepte n'importe quelles deux lettres majuscules après 'OCE'.
    """
    m = re.search(r"OCE[A-Z]{2}(\d+)", trip_id)
    return m.group(1) if m else None


def trace(num, dates_par_num, ids_du_flux):
    """Cherche si un train absent apparaît quand même dans la photo, sous une autre forme."""
    if num in dates_par_num:  # même numéro, mais avec une autre date de circulation
        return "autre date : " + ", ".join(sorted(dates_par_num[num]))
    # Le numéro écrit seul (pas au milieu d'un nombre plus long) dans un trip_id d'un autre format
    motif = re.compile(rf"(?<!\d){num}(?!\d)")
    trouves = [tid for tid in ids_du_flux if motif.search(tid)]
    return "trip_id : " + trouves[0] if trouves else ""


Statut = gtfs_realtime_pb2.TripDescriptor.ScheduleRelationship
resume = []
tous_absents = []  # trains absents de chaque photo, rassemblés pour le fichier CSV final
tous_prevus = []   # trains prévus de chaque photo, pour la couverture par ligne

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
    if prevus_jour.empty:
        print(f"\n=== Photo du {t_photo:%d/%m à %H:%M} (heure de Paris) ===")
        print("Aucun train HdF prévu dans le GTFS pour cette date : la version du GTFS"
              " ne la couvre pas (fenêtre glissante). Photo ignorée.")
        continue
    prevus =prevus_jour[(prevus_jour.depart <= t_photo + FENETRE) & (prevus_jour.arrivee >= t_photo)]
    # D4 : les cars de remplacement ne sont pas des trains, et le flux ne les suit pas.
    # On les retire du dénominateur, mais on les compte pour le signaler.
    est_car = prevus["mode"].str.startswith("Car", na=False)
    cars_exclus = est_car.sum()
    prevus = prevus[~est_car]
    # Un même numéro + date décrit deux fois dans le GTFS ne doit compter qu'une fois
    doublons = prevus.duplicated(["num", "date"]).sum()
    prevus = prevus.drop_duplicates(["num", "date"])

    # -----------------------------------------------------------------------
    # 3. Trains présents dans la photo : dictionnaire (numéro, date) -> statut
    # -----------------------------------------------------------------------
    presents = {}
    ids_du_flux = []  # tous les trip_id de la photo, pour chercher la trace des absents
    for entite in feed.entity:
        if entite.HasField("trip_update"):
            trip = entite.trip_update.trip
            ids_du_flux.append(trip.trip_id)
            num = numero_train(trip.trip_id)
            if num is not None:
                presents[(num, trip.start_date)] = Statut.Name(trip.schedule_relationship)
    # Pour chaque numéro vu dans la photo, les dates de circulation sous lesquelles il apparaît
    dates_par_num = {}
    for num, date in presents:
        dates_par_num.setdefault(num, set()).add(date)

    # -----------------------------------------------------------------------
    # 4. Numérateur : trains prévus retrouvés dans la photo (jointure D2 : numéro + date)
    # -----------------------------------------------------------------------
    cles = list(zip(prevus.num, prevus.date))
    prevus = prevus.assign(statut=[presents.get(cle) for cle in cles])  # None si absent
    couverts = prevus[prevus.statut.notna()]
    absents = prevus[prevus.statut.isna()]
    absents = absents.assign(trace_dans_flux=[trace(num, dates_par_num, ids_du_flux) for num in absents.num])
    tous_prevus.append(prevus)
    # Contrôle de D3 : trains HdF du jour présents dans la photo mais hors de la fenêtre
    cles_du_jour = set(zip(prevus_jour.num, prevus_jour.date))
    cles_prevues = set(cles)
    hors_fenetre = sum(1 for cle in presents if cle in cles_du_jour and cle not in cles_prevues)

    couverture = len(couverts) / len(prevus) if len(prevus) else float("nan")
    print(f"\n=== Photo du {t_photo:%d/%m à %H:%M} (heure de Paris) ===")
    print(f"Cars de remplacement exclus (D4) : {cars_exclus}")
    print(f"Trains HdF prévus (D3)         : {len(prevus)}")
    print(f"  dont présents dans le flux   : {len(couverts)}  -> couverture {couverture:.0%}")
    print(f"     statuts : {couverts.statut.value_counts().to_dict()}")
    print(f"  dont absents du flux         : {len(absents)}")
    print(f"     lignes les plus touchées : {absents.route_short_name.value_counts().head(5).to_dict()}")
    print(f"     mode (train ou car)      : {absents['mode'].value_counts().to_dict()}")
    print(f"     trace dans le flux       : {(absents.trace_dans_flux != '').sum()} sur {len(absents)}")
    print(f"Trains HdF du flux hors fenêtre D3 : {hors_fenetre}")
    print(f"Doublons numéro + date écartés     : {doublons}")
    resume.append({"photo": f"{t_photo:%d/%m %H:%M}", "prevus": len(prevus),
                   "presents": len(couverts), "couverture": f"{couverture:.0%}"})
    # Heures converties en texte lisible (sinon le CSV contiendrait « 2026-09-23 12:35:00+02:00 »)
    tous_absents.append(absents.assign(photo=f"{t_photo:%d/%m %H:%M}",
                                       depart=absents.depart.dt.strftime("%d/%m %H:%M"),
                                       arrivee=absents.arrivee.dt.strftime("%d/%m %H:%M")))

print("\n=== Résumé ===")
print(pd.DataFrame(resume).to_string(index=False))

# Couverture par ligne, toutes photos confondues : une ligne absente en bloc du flux
# (couverture proche de 0 %) ne s'interprète pas comme une ligne à moitié couverte
if tous_prevus:
    par_ligne = (pd.concat(tous_prevus)
                 .groupby("route_short_name")
                 .agg(prevus=("num", "size"), presents=("statut", "count")))  # count ignore les vides
    par_ligne["taux"] = par_ligne.presents / par_ligne.prevus
    par_ligne["couverture"] = par_ligne.taux.map("{:.0%}".format)  # 0.8 -> '80%'
    print("\n=== Couverture par ligne (les 15 plus faibles) ===")
    print(par_ligne.sort_values("taux").drop(columns="taux").head(15).to_string())

# Liste détaillée des absents, à ouvrir dans un tableur pour les examiner un par un
if tous_absents:
    fichier_absents = RACINE / "data" / "phase0_absents.csv"
    colonnes = ["photo", "route_short_name", "mode", "num", "date", "depart", "arrivee", "trace_dans_flux"]
    pd.concat(tous_absents)[colonnes].to_csv(fichier_absents, index=False)
    print(f"\nTrains absents enregistrés dans {fichier_absents}")
