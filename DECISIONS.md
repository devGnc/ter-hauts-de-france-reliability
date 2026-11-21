# Decision log

Every open choice in the project is recorded here: option chosen, alternatives rejected, reason.
This log feeds the *Method* section of the README.

---

## D1 — Hauts-de-France scope

- **Chosen:** scope defined by the GTFS published by the Region ("Trains régionaux Hauts-de-France mobilités", 71 lines, `route_id`s identical to the SNCF national GTFS). Excluded: coach lines (`route_type = 3`: P64 Laon–Hirson, K61 Charleville–Lille coach) and lines most likely run by TER Grand Est that serve the Aisne department (K1 Paris–Strasbourg, K2 Paris–Saint-Dizier, C73 Château-Thierry–Reims, C76 Reims–Laon). **Final scope: 65 rail lines.**
- **Rejected:** `agency_id` (agency 1187 covers all of France, agency 5235 only 10 Picardy lines); `route_short_name` (codes are not unique nationally: K12 = Paris–Lille and Nantes–Brest, K44 = Lille–Amiens and Lyon–Valence, P53 also exists in Grand Est).
- **Reason:** the Region is the transport authority and the fictional client: its own reference data is the most defensible definition of the scope.
- **To be confirmed:** whether K1, K2, C73 and C76 belong to Grand Est.

## D2 — Trip key

- **Chosen:** train number + service date. The train number is in `trip_headsign` (`trip_short_name` is empty) and is extracted from the `trip_id` with the pattern `OCE[A-Z]{2}(\d+)`: prefix `OCESN` for agency 1187, `OCEEA` for agency 5235 (Picardy lines). The first pattern, `OCESN(\d+)`, missed every line of agency 5235 (found in phase 0, 27/09).
- **Rejected:** `trip_id` alone. It contains an export timestamp (e.g. `OCESN16350F8784835:2026-09-22T17:41:41Z`, 25 distinct timestamps in a single file) and therefore changes from one GTFS version to the next.
- **Reason:** a join on an unstable identifier would lose trains without any visible error.
- **Status:** provisional, to be validated against the real-time feed in phase 0 (see `docs/phase0_feasibility.md`).

## D3 — Definition of a "scheduled train" at the time of an observation

- **Chosen:** a train is scheduled at time T if it is running (scheduled departure ≤ T ≤ scheduled arrival) or if its scheduled departure falls within the next hour (T < departure ≤ T + 60 min).
- **Rejected:** running trains only. Over 5 observations (23 to 26/09), 33 to 44% of the trains in the feed had not yet departed, all within 60 min: excluding them from the denominator would inflate coverage by about 60%.
- **Reason:** the denominator must match what the feed actually shows. Window measured with `src/phase0_fenetre_flux.py`; it confirms the documentation ("trains of the next 60 minutes").
- **Limitation:** trains remain visible 4 to 5 min after their arrival; negligible effect, not included. Measured on all trains in France, to be confirmed for HdF TER trains.

## D4 — Replacement coaches

- **Chosen:** services run by coach (mode `Car TER` in the GTFS stop identifier), even when filed under a rail line, are excluded from scheduled trains. Only trains are measured.
- **Rejected:** keeping them as scheduled trains missing from the feed. The real-time feed barely tracks coaches: over 3 observations (25 and 26/09), 13 coaches were scheduled and only 1 appeared in the feed. They would almost always be counted as missing data. After exclusion, 100% of scheduled trains are present in the feed (404 of 404).
- **Reason:** the project is about train reliability; a coach in the timetable is not a train.
- **Limitation:** coach services (engineering works) are not measured, to be stated in the limitations. Open question for phase 3: does a train replaced by a coach count as a cancellation from the passenger's point of view?
