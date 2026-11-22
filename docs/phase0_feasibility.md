# Phase 0 — Feasibility test

**Question:** does the SNCF GTFS-RT Trip Updates feed contain enough TER Hauts-de-France trains, in a usable form, to rebuild line-by-line reliability?

**Measurement rounds**

| Round | Dates | Status |
| --- | --- | --- |
| 1 | 23–26 September 2026, 5 snapshots | Done |
| 2 | November–December 2026, on the current timetable | **In progress:** weekend done (Sun 22/11, 2 snapshots), weekday slots to do (see [section 6](#6-measurements-still-to-do)) |

The weekend measurement planned for 21 November 2026 could not be run from the cloud session (no network access to the data sources). It was run locally on Sunday 22 November.

**Regional GTFS versions used for coverage**

| Round | `feed_version` | Valid | Downloaded | Archive (local, not committed) |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-25 | 25/09/2026 to 24/12/2026 | 26/09/2026 | `data/gtfs_archive/gtfs_region_20260926.zip` |
| 2 | 2026-11-21 | 21/11/2026 to 19/02/2027 | 22/11/2026 | `data/gtfs_archive/gtfs_region_20261122.zip` |

For round 1, the first version, downloaded on 23/09, was overwritten, so the 23/09 and 24/09 snapshots cannot be re-evaluated with the final method (see [section 5](#5-pitfalls-found-during-phase-0)). With the round 2 GTFS in `data/gtfs_region/`, the round 1 snapshots fall outside its window and `phase0_couverture.py` skips them.

**Scripts**

| Script | Role |
| --- | --- |
| `src/phase0_lire_flux.py` | Downloads one snapshot of the feed, decodes it, checks the `trip_id` / train number match and the delay fields |
| `src/phase0_fenetre_flux.py` | Measures which trains the feed shows, relative to the snapshot time (decision D3) |
| `src/phase0_couverture.py` | Compares HdF trains scheduled at the snapshot time with those present in the feed |
| `src/phase0_mesure.sh` | Round 2: runs the three scripts above in one command and saves their outputs in `data/mesures/` |

---

## 1. Coverage: scheduled HdF trains vs trains present in the feed

**Method.** For each snapshot taken at time T:

- **Denominator:** HdF trains scheduled at T (D3: running, or departing within the next 60 min), coaches excluded (D4).
- **Numerator:** those present in the snapshot, whatever their status (a `CANCELED` train present in the feed counts as covered).
- **Join:** train number + service date (D2).

**Round 1 results (GTFS 2026-09-25, final method)**

| Snapshot (Paris time) | Time slot | Coaches excluded (D4) | Scheduled trains | Present | Coverage | HdF trains in feed outside the D3 window |
| --- | --- | --- | --- | --- | --- | --- |
| Fri 25/09, 09:39 | End of morning peak | 2 | 103 | 103 | **100%** | 19 |
| Fri 25/09, 18:01 | Evening peak | 2 | 238 | 238 | **100%** | 9 |
| Sat 26/09, 15:56 | Weekend | 9 | 63 | 63 | **100%** | 5 |
| **Total** | | 13 | 404 | 404 | **100%** | |

**How coverage went from about 80% to 100%.**

1. **First run** (GTFS of 23/09, train number pattern `OCESN(\d+)`, coaches included): coverage of 79% to 88% over the 5 snapshots, with 9 lines at 0% (P10, P20, P21, P22, P23, P24, P30, P32, K20).
2. **Absent trains examined one by one:** almost all of them were in the feed, under a `trip_id` starting with `OCEEA` (agency 5235, Picardy lines) instead of `OCESN`. Pattern changed to `OCE[A-Z]{2}(\d+)`; coverage went to 98%, 99% and 89%.
3. **The 12 remaining absentees were all coaches** (`Car TER`), with no trace in the feed. Excluding coaches (D4) gives 100%.

**"Outside the D3 window" column.** These are HdF trains present in the feed but not counted as scheduled at T. They are most likely trains running late, whose *scheduled* arrival has already passed. They do not affect coverage. The 26/09 figure also includes the one coach seen in the feed.

**Round 2 results (GTFS 2026-11-21, same method)**

| Snapshot (Paris time) | Time slot | Coaches excluded (D4) | Scheduled trains | Present | Coverage | HdF trains in feed outside the D3 window |
| --- | --- | --- | --- | --- | --- | --- |
| Sun 22/11, 15:58 | Weekend | 5 | 62 | 62 | **100%** | 5 |
| Sun 22/11, 16:00 | Weekend | 5 | 61 | 61 | **100%** | 4 |
| Weekday morning peak | | | | | To do | |
| Weekday off-peak | | | | | To do | |
| Weekday evening peak | | | | | To do | |

The two weekend snapshots are 2 minutes apart (the second one comes from the first run of `phase0_mesure.sh`): they show almost the same trains and count as one time slot. All 61–62 present trains were `SCHEDULED`.

**Feed window, round 2 (`phase0_fenetre_flux.py`).** 43.6% and 43.8% of the trains in the feed (all of France) had not departed yet, within the 33–44% range of round 1 (D3). 2 trains on each snapshot had a forecast departure more than 1 h later (furthest: +144 min). Round 1 also had a few (0, 0, 1, 6 and 0; furthest +81 min). They are outside the D3 window, so they do not change the denominator.

**Finding.** Every scheduled HdF train was present in the feed: 404 of 404 in round 1 (3 snapshots), 62 of 62 and 61 of 61 on the current timetable (weekend). Weekday morning peak (07:30–08:30), weekday off-peak and evening peak have not yet been measured on the current timetable.

## 2. `trip_id` / train number match (validation of D2)

**Round 1, outputs of `phase0_lire_flux.py`**

| Snapshot (Paris time) | Trains in feed (all of France) | `trip_id` with no extractable number* | Exact `trip_id` match | Train number match* |
| --- | --- | --- | --- | --- |
| Wed 23/09, 12:35 | 1,435 | 58 | 0 | 119 |
| Thu 24/09, 10:10 | 1,192 | 41 | 0 | 84 |
| Fri 25/09, 09:39 | 1,309 | 51 | 0 | 110 |
| Fri 25/09, 18:01 | 2,349 | 96 | 0 | 205 |
| Sat 26/09, 15:56 | 1,029 | 50 | 0 | 60 |
| Sun 22/11, 15:58 (round 2) | 1,105 | 0 | 0 | 67 |
| Sun 22/11, 16:00 (round 2) | 1,114 | 0 | 0 | 65 |

\* Round 1: measured with the first pattern `OCESN(\d+)`, before the `OCEEA` fix. These columns undercount HdF trains. Round 2: current pattern `OCE[A-Z]{2}(\d+)`, which extracts a number from every `trip_id` in the feed. In both rounds the last column matches on train number only (no date check). In round 2 it gives the same count as the number + date match of `phase0_couverture.py` (62 + 5 = 67 and 61 + 4 = 65 trains, inside and outside the D3 window).

**The two formats are different.**

| Source | `trip_id` format |
| --- | --- |
| Static GTFS | `OCESN16350F8784835:2026-09-22T17:41:41Z` (export timestamp) |
| Real-time feed | `OCESN5789F1187_F:ICN:FR:Line::5648ced8-…::87547000:87763607:8:3519:20260923` |
| Real-time feed, Picardy lines | `OCEEA847505F5235_F:TER:FR:Line::6a7e9883-…::87313510:87313759:8:946:20261211` |

**Conclusion on D2.** Exact `trip_id` matching gives 0 matches on every snapshot. Train number + service date, with the pattern `OCE[A-Z]{2}(\d+)`, finds every scheduled train (section 1: 404 of 404 in round 1, confirmed on the current timetable). **D2 is marked as validated in `DECISIONS.md` (22/11/2026).**

## 3. Delay fields: `delay` vs `time`

In GTFS-RT, a `StopTimeEvent` can carry a `delay` (in seconds), a `time` (absolute Unix timestamp), or both.

| Indicator (arrival at last stop) | Round 1 | Round 2, Sun 22/11 15:58 | Round 2, Sun 22/11 16:00 | Round 2, weekdays |
| --- | --- | --- | --- | --- |
| **All trains in the feed** | | 1,105 trains | 1,114 trains | |
| Share with `delay` | ≥ 99.5% on all 5 snapshots (printed as 1.0, rounded to 2 decimals) | 100% (1,105) | 100% (1,114) | To do |
| Share with `time` | Not measured (the script did not count it then) | 100% (1,105) | 100% (1,114) | To do |
| Share with neither | Not measured | 0% | 0% | To do |
| Share of `delay` exactly 0 | Not measured | 84.7% (936 of 1,105) | 84.9% (946 of 1,114) | To do |
| **HdF trains only*** | Not measured | 67 trains | 65 trains | |
| Share with `delay` | Not measured | 100% (67) | 100% (65) | To do |
| Share with `time` | Not measured | 100% (67) | 100% (65) | To do |
| Share with neither | Not measured | 0% | 0% | To do |
| Share of `delay` exactly 0 | Not measured | 95.5% (64 of 67) | 95.4% (62 of 65) | To do |

\* HdF trains recognised by train number (see note under the table of section 2).

On a Sunday afternoon, every train carries both fields at its last stop, and almost all HdF trains show a delay of exactly 0 at the terminus. Whether this 0 means "on time" or "no information" remains open (see below); the weekday slots, especially the peaks, will show whether the share of zeros drops when there is more traffic.

**Statuses observed (trip level)**

| Snapshot (Paris time) | `SCHEDULED` | `ADDED` | `CANCELED` |
| --- | --- | --- | --- |
| Wed 23/09, 12:35 | 1,273 | 135 | 27 |
| Thu 24/09, 10:10 | 1,052 | 129 | 11 |
| Fri 25/09, 09:39 | 1,153 | 130 | 26 |
| Fri 25/09, 18:01 | 2,089 | 221 | 39 |
| Sat 26/09, 15:56 | 901 | 122 | 6 |
| Sun 22/11, 15:58 (round 2) | 961 | 132 | 12 |
| Sun 22/11, 16:00 (round 2) | 968 | 134 | 12 |

`SKIPPED` also appears at stop level (a stop the train does not serve).

**What the examples show (qualitative, not systematic).**

- In every example decoded by hand, stops carried both `delay` and `time`.
- **A delay is a forecast, sometimes an old one.** Each train has its own `timestamp` (last update):
  - On 26/09, a TGV shown in the 15:56 snapshot had last been updated at 13:08. Its "0 delay" at the terminus was a forecast almost 3 hours old.
  - On 25/09, an `ADDED` train in the 09:39 snapshot had last been updated at 02:40. It showed 5 to 20 min of delay at earlier stops, then 0 at the terminus.
- **Stop order can be inconsistent.** In the feed's forecast times, a `SKIPPED` stop came at 18:30, after a stop forecast at 18:55.

**Consequence for delay calculation (questions for phase 3, not decided here).**

- Which observation of a train counts?
- How should a forecast that has not been updated for hours be treated?
- Does a `delay` of 0 mean "on time" or "no information"?
- How should `SKIPPED` stops count?

## 4. Storage volume

**Snapshot size, round 1:** 947, 766, 852, 1,620 and 717 KiB (mean **980.4 KiB**). The evening peak snapshot is twice as large as the others. Night snapshots were not measured; they are probably smaller, so the mean below likely overestimates a full day.

**Snapshot size, round 2:** 741 and 745 KiB (758,789 and 762,998 bytes) on Sunday 22/11, close to the round 1 Saturday snapshot (717 KiB). The table below still uses the round 1 mean; weekday sizes on the current timetable are **to do**.

**Raw volume** (mean size × snapshots per day × number of days), compared with the Supabase free plan (500 MB per project):

| Interval | Snapshots per day | 4 weeks | 8 weeks | 8 weeks vs 500 MB |
| --- | --- | --- | --- | --- |
| 2 min | 720 | 18.8 GiB | 37.7 GiB | ×77 |
| 3 min | 480 | 12.6 GiB | 25.1 GiB | ×51 |
| 4 min | 360 | 9.4 GiB | 18.8 GiB | ×39 |
| 5 min | 288 | 7.5 GiB | 15.1 GiB | ×31 |
| 10 min | 144 | 3.8 GiB | 7.5 GiB | ×15 |
| 15 min | 96 | 2.5 GiB | 5.0 GiB | ×10 |

**After keeping HdF trains only.** HdF trains made up 9.3%, 10.5% and 6.6% of the entities in the 3 snapshots of section 1. This is a share of *entities*, not of *bytes*. With 10.5% as an upper bound on entities, 8 weeks at a 2-min interval would still be about 4.0 GiB (×8 the quota).

The share of *bytes* is measured by `phase0_couverture.py` (encoded size of the HdF entities divided by the file size). Round 2, Sunday 22/11: **6.0%** (45 of 741 KiB) and **5.8%** (43 of 745 KiB). Applied to the round 1 mean size, 8 weeks at a 2-min interval would be about 2.3 GiB (980.4 KiB × 6.0% × 720 × 56 days), about ×5 the quota. This rests on weekend snapshots only: weekday byte shares are **to do**. The volume once stored as table rows depends on the schema, which will be designed in phase 1.

**Conclusion.** Raw snapshots cannot be stored in the 500 MB database at any interval, and keeping only HdF trains is not enough either. Phase 2 needs a reduction strategy: for example, which fields to keep, whether to store only changes, and where raw files are archived outside the database. That strategy is not decided here.

## 5. Pitfalls found during phase 0

- **The regional GTFS is a rolling window** of about 90 days from its publication date: past days drop out. Every version must be archived.
- **Later GTFS versions remove cancelled trains.** For the 25/09 18:01 snapshot, the 23/09 GTFS gave 247 scheduled trains including 8 `CANCELED`; the 25/09 GTFS gave 240 including 1 `CANCELED`. A GTFS published after the fact underestimates cancellations. Which version counts for a given day is a decision for phase 1.
- **Two `trip_id` prefixes** (`OCESN`, `OCEEA`): a pattern limited to the first silently dropped 9 lines (section 1).
- **Two `stop_id` formats in the same feed:** `StopPoint:OCETGV INOUI-87192039` and `StopArea:OCE87756056`. The 8-digit station code is the common part.
- **Annual timetable change:** expected on the night of 12 to 13 December 2026 (European timetable change), i.e. during the planned collection. The reference data will have to be reloaded, and train numbers and lines checked again.

## 6. Measurements still to do

Round 2, on the current GTFS (download and archive it first):

| Slot | Day | Status |
| --- | --- | --- |
| Morning peak, 07:30–08:30 | Weekday | To do |
| Off-peak, 10:00–15:00 | Weekday | To do |
| Evening peak, 17:00–19:00 | Weekday | To do |
| Weekend, any time | Saturday or Sunday | **Done:** Sun 22/11, 15:58 and 16:00 |
| Night, 23:00–05:00 (for the storage mean) | Any | To do, optional |

For each slot, record: coverage, `delay` / `time` indicators (all trains and HdF), share of `delay` exactly 0, snapshot size, HdF byte share, `trip_id` with no extractable number.

**How to run a slot.** The round 2 GTFS (2026-11-21) is already in `data/gtfs_region/`; keep it for the whole round, so that every slot is measured against the same timetable. At each slot, from the repository folder:

```bash
./src/phase0_mesure.sh
```

The command takes one snapshot, then prints coverage, delay fields and feed window. Outputs are saved in `data/mesures/` with the date and time in their names. Coverage is recalculated on every saved snapshot, so the summary at the end of the `couverture_*.txt` output grows with each slot. Round 2 must be finished before the timetable change of 12–13 December.

## 7. Collection interval and hosting — **decided: 2 min (D5), Google Cloud e2-micro (D7)**

### 7.1 Why the interval matters

Trains disappear from the feed **4 to 5 minutes after their arrival**. The oldest arrival still visible was −5, −5, −5, −5 and −4 min on the 5 round 1 snapshots, and −5 and −4 min on the 2 round 2 snapshots (Sunday 22/11). To see each train once *after* it has arrived at the terminus, there must be a snapshot inside that window.

With snapshots every Δ minutes, perfectly on time, the share of trains caught after arrival is min(1, W/Δ), where W is the visibility window:

| Interval Δ | W = 4 min | W = 5 min |
| --- | --- | --- |
| 2 min | 100% | 100% |
| 3 min | 100% | 100% |
| 4 min | 100% | 100% |
| 5 min | 80% | 100% |
| 10 min | 40% | 50% |
| 15 min | 27% | 33% |

Three caveats:
- **Late or skipped runs** lower these shares further. This matters for schedulers that are best-effort (see 7.2).
- **The feed is refreshed every 2 min** according to its documentation (not measured here), so an interval under 2 min brings nothing new.
- **Seeing a train after arrival does not guarantee an up-to-date delay** (section 3: forecasts can be hours old). With a longer interval, the last observation is a forecast made up to Δ minutes before arrival. Which observation counts is a phase 3 decision, but the interval decides what will be available.

**Implication:** an interval of **4 minutes or less**, actually respected, is needed to keep the post-arrival state for every train.

**Decision (owner, 22/11/2026): 2 min** (D5 in `DECISIONS.md`). The host is still to be chosen (7.2) and must actually hold this interval.

### 7.2 Hosting options for a collector running 24/7 for 4 to 8 weeks

The owner's laptop is ruled out. Figures below come from the providers' pages or, where marked, from third-party sources, as of November 2026. **Check them on the official pages before choosing.**

| Option | Shortest interval | Reliability | Storage for raw files | Cost | Main risks |
| --- | --- | --- | --- | --- | --- |
| **A. GitHub Actions, one run per schedule** | 5 min (documented minimum) | Best-effort: runs can be delayed, especially around the top of the hour, or dropped under load (documented) | None on the runner; data goes to Supabase (500 MB) | Free for standard runners on a public repository | Interval above 4 min, so post-arrival states are missed even when on time. Scheduled workflows are disabled after 60 days without repository activity (public repositories) |
| **B. GitHub Actions, long-running job** (a scheduled job loops every 2 min for up to 6 h, the hosted-job limit) | 2 min inside a job | Gaps only when a scheduled job starts late or is dropped (can be reduced with overlapping jobs and deduplication) | Same as A | Free on a public repository | Same 60-day rule. Keeps a shared runner busy around the clock: read the GitHub Actions terms on acceptable use before choosing |
| **C. Supabase Cron + Edge Function** | Supabase documents schedules down to every second; 1–2 min is realistic | Runs inside the database platform; jobs should finish in under 10 min | Same 500 MB quota | Free plan; invocation quota reported at 500k per month by a third-party source (2-min interval ≈ 21,600 per month) | Edge Functions run TypeScript (Deno), not Python, which departs from the project's "Python collects" rule. Decoding a 1–1.6 MB protobuf within function limits must be tested. Frequent runs keep the project from pausing (free projects pause after 1 week of inactivity) |
| **D. Free cloud VM** (Google Cloud e2-micro; Oracle Always Free) | 1 min (system cron) | Good: dedicated machine | Local disk: 30 GB standard disk (Google), enough for HdF-filtered raw files | Free within limits, but needs a billing account | Google: free only in us-west1, us-central1 and us-east1, 1 GB of free outbound traffic per month. Oracle: idle instances (under 20% CPU, network and memory over 7 days, third-party sources) can be reclaimed, and a light collector looks idle. Server administration (updates, security) is on the owner |
| **E. Small paid VPS** (e.g. Hetzner CX23) | 1 min (system cron) | Good: dedicated machine | 40 GB local disk | About €5.49–5.99 per month excl. VAT after the June 2026 price change (third-party sources); about €12–15 for two months | Availability of the cheapest plan varies by location. Server administration is on the owner |

**Constraints common to all options:**
- the 500 MB Supabase quota (section 4) applies whatever the host;
- options D and E are the only ones that can also keep raw files outside the database;
- collection will run over the 12–13 December timetable change (section 5).

**Decided by the owner on 22/11/2026:** interval of 2 min (D5) and option D, a Google Cloud e2-micro (D7). The machine was created the same day; the collector is not installed yet.

## 8. Decision

- [ ] **Go**
- [ ] **No-go:** alternatives are the SIRI ET Lite feed, a regional real-time feed, or a comparison of regions based on monthly figures.

**Proposed: Go, on conditions.**

**Justification.** On round 1, 404 of 404 scheduled HdF trains were present in the feed (3 snapshots: morning, evening peak, weekend). On the current timetable, 62 of 62 and 61 of 61 (weekend, round 2). The trip key D2 works once both `trip_id` prefixes are handled. Delays are available, although they are forecasts that must be handled with care.

**Conditions before starting collection:**
1. confirm coverage on the current timetable (round 2, section 6), including the morning peak: weekend done, weekday slots to do;
2. choose an interval of 4 min or less (done: D5, 2 min) and a host that respects it (done: D7, Google Cloud e2-micro);
3. define a storage strategy that fits within 500 MB (section 4).

**Decisions to record in `DECISIONS.md`.**

| Status | Decisions |
| --- | --- |
| Already recorded | D1, D2 (validated, corrected pattern), D3, D4, D5 (2-min collection interval), D6 (Christmas holidays, version 1 freeze), D7 (host) |
| To come | Which GTFS version counts for a given day (section 5); storage reduction strategy (section 4) |
