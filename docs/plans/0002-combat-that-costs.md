# Plan 0002 — Combat that costs: tempo, armor, surge, beats, marks

Status: READY

## Sources

PLAYNOTES session 2 (ward dominance; damage-floor grind; surge dud; dead
`armored` trait) and session-2 chat feedback (engine should generate
words/labels, not only numbers, because a full fight is too long to narrate;
a wounds-like layer is wanted but quirky, not gory).

## Design arguments (settled here; do not reopen)

- Ward dominated because time in a fight was free: soak pays per incoming
  hit and nothing punished a long fight but hp — which is what ward
  minimises. The fix is not nerfing ward's numbers; it is making rounds
  cost light, so tempo is a real currency and every stance choice is a
  trade again.
- Twelve rounds of `max(1, ...)` chip damage against soak 4 was a wait, not
  a threat. Armor should be an obstacle with an arc: the `armored` trait now
  means armor that *cracks* as you work it, so anti-armor fights accelerate
  instead of flatlining.
- Surge is the game's marquee spend; it must never feel like a wasted
  button. It now ignores soak entirely (minimum result 2).
- The engine narrates through the DM; giving the log deterministic beat
  labels gives the DM honest hooks and permission to compress everything
  unlabeled.
- Marks replace a gore-forward wounds system with small, named, mechanical
  conditions — texture beside the hp number, tuned quirky not grisly
  (Charter §9: no lingering on suffering).

## Mechanics

### Stances (engine.STANCES becomes 4-tuples: atk, guard, soak, dmg)

- measure `(0, 0, 0, 0)`
- press `(+2, -2, 0, +2)` — was `(+3, -2, 0)`. Press now converts risk into
  flat damage, which is what actually beats soak.
- ward `(-2, +3, +1, 0)` — numbers unchanged; the light clock is its nerf.
- skirmish `(-1, +1, 0, 0)` — unchanged.

The delver combatant gains `dmg_bonus`; `_switch_stance` adjusts it. Stance
`dmg_bonus` applies to delver attacks only, added with the brittle bonus
before soak: `dmg = max(1, roll + flat_bonus - soak)`.

### The light clock

- The delver combatant carries `light` (copied from the delver at fight
  start). At the end of every 4th round (4, 8, 12, …) that ends with
  enemies still up, `light -= 1` (floor 0), event: importance 1, beat
  `lamp-low`, text states light remaining.
- If light reaches 0 mid-fight and the fight did not start dark: set
  `state["darkness"] = True`, delver `atk -= 2`, event beat `lamp-out`
  ("The lamp dies. This ends in the dark."). Enemy `+2 atk` already keys
  off `state["darkness"]` each strike; dread is not re-tested mid-fight.
- `result` gains `"light"`; `apply_fight_result` writes it back to the
  delver. A fight that started in darkness burns nothing (already 0).

### Cracking armor (the `armored` trait finally does something)

- When the delver lands a hit on an enemy with `armored` in traits and
  `soak > 0`: after damage is applied, `soak -= 1` (a crit strips 2),
  floor 0. Event beat `crack`; text names the new soak.
- Enemies do not crack the delver's armor (asymmetry on purpose: player
  gear durability is bookkeeping misery).
- Catalog unchanged — `cullet crab`, `vitrified watchman`, `custodian
  stray` already carry the trait.

### Surge pierces

- A surge attack treats target soak as 0 (still `2 × dmg` dice, still
  cannot miss). Minimum result is therefore 2. Surge does not crack armor —
  it goes through it, not into it. Beat `surge`.

### Beats — the engine generates words

`_ev(state, importance, text, beat=None)`; events serialize as
`[importance, text, beat]` (all readers updated; no backcompat).
`fight_summary` returns lines with `importance >= 1 OR beat`. Beat
vocabulary (deterministic, assigned by the resolver from mechanical
context; first match wins where several could apply):

- `first-blood` — the first landed hit of the fight, either side.
- `finisher` — the hit that drops an enemy or the delver.
- `crack` — armored soak stripped (above).
- `stagger` — a landed hit dealing ≥ half the target's `hp_max` in one blow.
- `turned` — a landed delver hit floored to 1 by soak (armor turned it).
- `overreach` — a delver miss by 5+ while in press stance.
- `close-call` — an enemy hit halved by the grit auto-spend.
- `surge`, `crit`, `lamp-low`, `lamp-out` — as above / existing flags.

`ui/fight.txt` and `fight_full.txt` print the beat as a `[tag]` suffix.
PLAYBOOK gains a narration rule (checklist): every beat in the short log
earns a clause of narration; unlabeled lines may compress freely.

### Marks (the quirky wound layer)

- New catalog `catalogs/marks.json` (`"version": 1`, section `marks`,
  census **10**, fields `{name, effect, text}`; validator: effects from
  `engine.MARK_EFFECTS`, names unique, locality rule applies).
- `delver["marks"]` — list of mark names, always present (new save shape).
- **Gaining:** when a fight ends `victory` or `retreated` and (the largest
  single blow the delver took ≥ 6, or final hp ≤ ⅓ `hp_max`): exactly one
  mark, drawn via `rng_for(world_seed, "mark", counter)` (counter bumped),
  excluding marks already held. At 3 marks held, no new mark. Parting
  blows on withdraw count toward the trigger.
- **Healing:** `camp` also removes the most recently gained mark
  ("dressed and splinted"). `surface` clears all marks. No mark survives
  a rest day in Wake.
- **Effects** (`engine.MARK_EFFECTS`, applied inside the derived-stat
  readers; one effect per mark; stacking allowed across different marks):
  `atk-1`, `guard-1`, `soak-1` (floor 0), `nerve-2`, `grit_max-1`
  (floor 1), `hp_max-3` (current hp capped down), `camp_heal_half`
  (round down), `light_leak` (each delve costs 1 extra light),
  `breather_numb` (breather sites grant no grit), `flee_late` (skirmish
  auto-withdraw triggers at 25% hp, not 40%).
- **Catalog content** (name → effect; blurbs written at implementation in
  SETTING tone — wry, strange, bloodless):
  glass-stung hand → `atk-1`; ringing ear → `nerve-2`; cracked rib →
  `hp_max-3`; wrenched knee → `guard-1`; split coat-seam → `soak-1`;
  lamp-shy → `light_leak`; shard in the boot → `flee_late`; cold sweat →
  `grit_max-1`; bad night's blood → `camp_heal_half`; thousand-yard glaze
  → `breather_numb`.
- `ui/delver.txt` lists marks with their text; `status` prints them.

### Save

`SAVE_VERSION` → 2. No migration (constitutional).

## Files

- `engine.py` — STANCES 4-tuples + `dmg_bonus`; light clock + mid-fight
  darkness; cracking; surge pierce; `_ev` beats; mark effects in derived
  readers; `MARK_EFFECTS`; result `light`.
- `content.py` — marks catalog load/validation (census pin `marks: 10`);
  mark gain in `apply_fight_result`; mark heal in `do_camp`/`do_surface`;
  `light_leak`/`breather_numb`/`flee_late` hooks where they live.
- `catalogs/marks.json` — new.
- `session.py` — `status` shows marks; no new commands.
- `pages.py` — beats as `[tag]` suffixes; marks on the delver sheet.
- `test_engine.py`, `test_content.py` — see expectations.
- `bench_combat.py`, `docs/BENCHLOG.md` — see bench targets.
- `docs/PLAYBOOK.md` — narrate-from-beats rule (one short paragraph under
  "Running the table").

## Test expectations (contract suites)

- Surge damage is never < 2, and ignores soak (pin a seeded fight).
- Cracking: seeded fight vs an armored enemy shows strictly decreasing
  soak on landed delver hits; crit strips 2; floor 0; non-armored soak
  never moves.
- Light clock: a seeded long fight burns light at rounds 4 and 8; a fight
  started in darkness burns none; mid-fight lamp-out flips enemy/delver
  attack modifiers from that point (pin the event sequence).
- Beats: pinned seeded fight produces the expected beat sequence;
  `fight_summary` includes every beat-carrying line.
- Marks: one broken world per validator clause (bad effect id, duplicate
  name, census off); gain trigger fires on the big-blow case and the
  low-hp case and not otherwise; cap 3; camp removes newest; surface
  clears; each effect id measurably changes its derived reading.
- Pause/resume determinism still holds (`fight_on` replay identical), now
  including beats and light.

## Bench targets (tune toward; record actuals in BENCHLOG)

- Mean rounds for a stock delver (plan-0001 test delver, salvage axe) to
  kill a vitrified watchman: **≤ 7** in press (was ~12-round territory).
- Stance diversity: across the matchup grid (each enemy × each stance,
  1000 seeds), no single stance is the best-survival choice in **> 60%**
  of matchups.
- Surge EV vs soak-4 targets ≥ 9 damage; minimum 2 in all samples.
- Expedition death rate (tune.py) within ±10% of the pre-change baseline —
  this plan re-shapes fights, plan 0003 re-shapes survival incentives.

## Checklist

- [ ] engine.py: stances, light clock, cracking, surge pierce, beats, mark effects
- [ ] catalogs/marks.json + content.py validation, gain/heal wiring
- [ ] session.py status + pages.py (beats, marks, no stale readers of 2-tuple events)
- [ ] SAVE_VERSION 2; fresh save plays clean end-to-end
- [ ] contract suites green (`python -m unittest`)
- [ ] benches re-run; BENCHLOG entry appended with the targets above
- [ ] PLAYBOOK narrate-from-beats paragraph added
- [ ] CLAUDE.md status updated
