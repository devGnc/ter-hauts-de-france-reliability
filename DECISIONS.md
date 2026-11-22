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
- **Status:** **validated** (22/11/2026), with the pattern `OCE[A-Z]{2}(\d+)`. Evidence from phase 0: exact `trip_id` match gives 0 matches on every snapshot (static and real-time formats differ); train number + service date finds 404 of 404 scheduled HdF trains in round 1, and 62 of 62 and 61 of 61 on the current timetable (22/11), where the pattern extracts a number from every `trip_id` in the feed. See `docs/phase0_feasibility.md`, sections 1 and 2.

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

## D5 — Collection interval

- **Chosen:** one snapshot of the feed every **2 minutes** during phase 2 (720 per day).
- **Rejected:** 3 or 4 min (enough in theory, but a single late or skipped run can lose the post-arrival state of the trains in that window); 5 min and more (only 80% of trains caught after arrival at 5 min if they stay visible 4 min, 40–50% at 10 min); under 2 min (the feed is refreshed every 2 min according to its documentation, so nothing new).
- **Reason:** trains leave the feed 4 to 5 min after their arrival (−4 to −5 min on all phase 0 snapshots). At 2 min, each train is seen about twice after arriving, which leaves a margin for one missed run. See `docs/phase0_feasibility.md`, section 7.1.
- **Consequences:** the host, still to be chosen (section 7.2), must actually hold this interval. Raw volume is about 37.7 GiB over 8 weeks (section 4): the storage reduction strategy is still open.

## D6 — Christmas holidays and data freeze for version 1

- **Chosen:** collection runs without a break from 13/12/2026. Each day is labelled: normal period, school holidays (19/12/2026 to 04/01/2027, dates to be confirmed against the official calendar) or public holiday (25/12, 01/01). Headline figures and the 3 recommendations are computed on normal days; the holidays are shown as a separate segment. Data for version 1 is frozen on 17/01/2027 (5 weeks, about 3 of them normal); collection continues to 8 weeks for a version 2 in February.
- **Rejected:** stopping collection during the holidays (data not collected is lost for good); mixing the holidays into the headline figures (lighter, less commuter-heavy traffic would blur the picture for the Region's daily users); freezing on 24/01 (one more normal week, but too little time to deliver by the end of January).
- **Reason:** the deliverable must be ready by the end of January 2027, when "summer 2027" internship offers are published. Excluding the holidays is only a filter in the SQL views, so it stays reversible.
- **Limitation:** about 15 normal weekdays in version 1: enough for the main lines, thin for little-served lines split by time slot. Version 2 addresses this. The exact filtering rule is written in phase 3.

## D7 — Collector host

- **Chosen:** a Google Cloud e2-micro virtual machine (free tier), zone `us-east1-b`, Debian 13, 30 GB standard persistent disk, no service account (the machine has no rights on the Google Cloud account). Created on 22/11/2026, inside the 90-day free trial ($300 of credits, until about 20/02/2027), with a budget alert at €1, €5 and €10 per month, counted before credits.
- **Rejected:** Oracle Always Free (idle instances can be reclaimed, and a light collector looks idle: risk of a gap mid-collection); a small paid VPS (about €12–15 for the collection, for no gain in reliability); GitHub Actions (5-min minimum interval or 6-hour jobs, best-effort scheduling, incompatible with D5); Supabase Cron (TypeScript instead of Python, same 500 MB quota). See `docs/phase0_feasibility.md`, section 7.2.
- **Reason:** a dedicated machine that holds a 2-min schedule (D5) at no cost, with enough disk for HdF-filtered raw snapshots. A US zone is required for the free tier; the feed downloads in under a second from there (tested: 814 KB in 0.9 s).
- **Limitations:** 30 GB of disk cannot hold 8 weeks of complete raw snapshots (about 38 GB); 1 GB of free outbound traffic per month. The account is **never upgraded to a paid account**, so the card cannot be charged: collection ends around 07/02/2027, before the end of the trial (about 20/02/2027); the data is copied off the machine and the machine deleted before then. If the trial ends first, Google stops the machine without charging. Server administration (updates, security) is on the owner.
