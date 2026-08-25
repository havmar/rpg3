# BENCHLOG

*Dated bench entries. After every change that could move numbers, re-run
(`python tune.py`) and append — including "nothing moved" entries; they are
the proof a change is bench-neutral.*

## 2026-08-23 — v0.1 baseline (plan 0001)

First numbers ever. `tune.py --runs 300 --careers 300`.

Combat (fresh stock delver, pauses answered fight_on — floor numbers):

- d1: ~96–99% victory, ~4% death in measure. Near-safe, not free.
- d2: ~82% victory measure, 18% death. First real risk.
- d3: ~67% victory measure, 33% death; skirmish flees out at 64%.
- d4: ~52% victory measure — a coinflip for a fresh delver.
- d5–d6: 27% → 17% victory. Deadly without training/gear; skirmish
  still escapes 76% of the time.
- Ward consistently trades ~1–2 extra rounds for the best survival;
  press ends fights fastest; skirmish converts deaths into retreats.
  Stance choice is live at every depth. Pause fires in 33–96% of fights,
  scaling with depth.

Careers (crude ramping policy, 10-expedition cap):

- 77% die before expedition 10; mean 3.9 expeditions before death;
  death depths center on d2–d4. A delver's life ≈ 4 sittings — genre-fit.
- Mean 103 chits banked per career (~26/expedition after the scrap
  doubling): about two upgrades per lifetime; survivors compound.

Tuning applied during this pass: encounter menace budget cut from
`2+2*depth` to `1+depth±1` (fresh-delver d1 death was 31%, d2 86% — far
too hot); scrap value doubled to `2*menace` (economy starved the haven
decisions at ~81 chits/career). Per the tuning principle these sim rates
run below played rates; leaving them harsh on purpose.

Watch next: whether played d5–d6 needs a mid-stratum gear tier, and
whether training cost (15*new value) lets NERVE/VIM matter fast enough.

## 2026-08-25 — plan 0002 (combat that costs)

`python tune.py --runs 300 --careers 300`, against the 2026-08-23 baseline
above. Everything in this entry moved on purpose.

Plan targets, actuals:

- **Watchman in press: 4.30 mean rounds on a win** (target ≤ 7; the
  pre-change reference delver took 5.82 rounds and won only 46% of the
  time — now 81% at 4.30). Cracking armor plus press's flat +2 turned the
  soak-4 grind into a fight with an arc.
- **Surge vs soak 4: mean 10.91, minimum 2** over 2000 samples (target EV
  ≥ 9, minimum 2). Before the pierce this attack averaged ~5 through soak 4.
- **Stance diversity: skirmish is the best-survival choice in 60% of
  matchups** (target: no stance > 60%; it was 80%). See the caveat below.
- **Career death rate 69%, from 77%.** Just outside the ±10% band if read
  as a relative move (-10.4%), inside it read as points. Fights got kinder
  because press and cracking both cut rounds; the light clock's cost is an
  expedition-level tax that a single-fight bench cannot price. Left as is:
  plan 0003 re-shapes survival incentives and will move this number again.

Combat grid, notable deltas (fresh stock delver, pauses answered fight_on):
press d2 89%→96%, d3 73%→85%, d4 52%→74%, d5 27%→46%, d6 14%→30% victory,
and press's mean rounds fell at every depth (d4 4.8→4.0). measure gained a
few points at every depth from cracking alone. ward barely moved in a
single fight, which is the point — its cost is now light, not hp.

Careers: mean max depth 3.9→4.1, mean chits banked 103→117, mean
expeditions before death 3.9→4.0.

**Caveat on the stance-diversity metric, for the next design session.** The
metric as written counts a retreat as surviving, so skirmish wins every
hard matchup by declining it — that is a property of the auto-withdraw, not
of the stance numbers, and no tuning of atk/guard/soak/dmg will move it.
The bench now also reports the useful half: which stance is best among the
three that actually stay and fight. There, **press is best in 80% of
matchups** (measure 20%, ward 0%). That is the real diversity problem this
plan created: press converts risk into damage, and damage is what beats
both soak and the light clock. Ward's compensation — long fights are now
expensive across the expedition — is invisible to a single-fight bench.
Flagging rather than tuning: the honest instrument is a career bench that
prices light, and building one is a design decision, not an implementation
one.

## 2026-08-25 — plan 0003 (a reason to surface)

`python tune.py --runs 300 --careers 300`. Combat numbers are byte-identical
to the plan 0002 entry — nothing in this plan touches a fight — so only the
career bench is reproduced. The career bench now runs two policies: **ramp**
(the plan-0001 policy, kept as the baseline) and **satchel** (new: climb out
when the bag is full or hp drops under 40%).

Plan targets, actuals:

- **Median chits per expedition under the satchel policy: 23** (target
  > 0). Median career: 66, against an upgrade bar of 20 chits — **72% of
  satchel careers bank at least one gear upgrade**, so the haven layer is
  reachable by a crude policy, which was the point.
- **Day-1 career deaths: 18%** under satchel, 2% under ramp (target
  < 50%). Both playtest delvers died on day 1 with full coats and empty
  accounts; the carry limit plus a payday at the top now gets most crude
  runs out of the ground at least once.
- **Commission uptake: 25%** of surfacings carrying 3+ items filled the
  standing order, under both policies (target ≥ 20%). The draw is not
  unfillable.

Policy comparison, for the record: ramp died in 67% of careers over 4.3
expeditions and banked a median 108 chits; satchel died in 78% over 2.7
expeditions and banked a median 66. The satchel policy is *greedier*, not
safer — "bag full" arrives later than "depth target reached", so it pushes
to d5–d6 (death histogram d5:68 d6:50 against ramp's d5:44 d6:23) and dies
richer and sooner. That is the crude-policy artifact, not the mechanic: a
player reads hp and light and turns back before the bag fills. Recorded so
the next tuning pass does not mistake it for the satchel being lethal.

Mean max depth reached rose (3.9 → 4.3 ramp, 4.5 satchel) and mean chits
per career rose (103 → 131 ramp), both from the commission and from
expeditions running longer under a carry limit than under a depth target.
