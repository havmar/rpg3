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
