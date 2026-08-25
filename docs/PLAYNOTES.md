# PLAYNOTES — the play → design inbox

*Appended by the wrap-up rite at the end of every play session; mirrored to
the main branch. Design sessions read this first, mark each item
`[HARVESTED → plans/NNNN]` or `[DECLINED — reason]`, and never delete.*

---

## Session 1 — 2026-08-23 — Hallam Rasp (`play/hallam-rasp`)

Reconstructed from post-session chat feedback; the wrap-up rite did not run
at the table. (Next play session: end with `/wrapup`.)

**Where the fiction stands:** Hallam Rasp, surgeon's-runner, three deep in
the Vitric Age at the glass orchard — 9/17 hp, 13 chits carried, nothing
banked. The delve-or-surface choice is live.

**DM notes:**

- CRAFT is a dead stat: it appears in the stat list, background priorities,
  and training, but no formula reads it. Chits spent training it buy
  nothing. Needs a design decision — give it a job (salvage value? light or
  supply efficiency?) or drop it.
- The delver sheet lists the five stats without saying what they do; the
  player had to ask what VIM is. Add a short legend to `ui/delver.txt` or a
  stats note in the playbook.

**Player notes:**

- Best moment: wanting to go deeper — the tension between surfacing to
  restock and pressing on. Light as a resource works.
- First impulse was to explore the steppe around Wake instead of
  descending (played the descent to test the game). `[DECLINED for now —
  the surface is deliberately thin; depth is the game's axis (Charter §5).
  If the steppe ever matters it is overland travel between mouths, a later
  milestone, not a second exploration layer.]`
- Worst friction: narration length. The player reads for the object level;
  the poetry accumulated. `[HARVESTED → SETTING.md §Voice + playbook
  message-protocol cut pass, settled in the same commit as this entry.]`

---

## Session 2 — 2026-08-25 — Teodor Slake (`play/teodor-slake`)

**Where the fiction stands:** Teodor Slake, cutter, dead at depth 5 in the
annealing hall of the Vitric Age, killed by a vitrified watchman he had
ground down to 5 of 14. Twelve rounds, one pause, one surge that did 1
damage. Thirty-seven chits on him, none banked, day one. The Ledger now has
two pages — Hallam Rasp's was written at the top of this session, closing
his run, and Teodor's at the bottom. Wake has buried two men who never made
it to a second day.

**DM notes:**

- **Ward is a solved axis.** It was the arithmetic favourite in all four
  stance decisions this session. Soak applies *per incoming hit*, so +1 soak
  scales with the number of blows, while −2 attack only costs tempo — and
  tempo is free, because **a fight burns no light and no other resource**.
  Nothing in the game punishes a long fight except the hp it costs, which is
  exactly what ward minimises. Fix candidates: a per-round or per-fight light
  cost; a fatigue/round clock; press granting damage rather than only
  accuracy; capping stance soak.
- **The damage floor (`max(1, dmg - soak)`) makes high-soak enemies a wait,
  not a threat.** Against the watchman's soak 4, a 1d10 dealt **1** on any
  roll of 1–5 — half of all landed hits. The result was twelve rounds of
  chip damage. Slow is not the same as tense.
- **Surge can be a dud, and that is the worst bug of the session.** Two grit
  — the game's marquee spend, a swing that *cannot miss*, double dice — came
  up 2d10 = 2, minus soak 4, floored to **1 damage**. The one moment the
  player is promised certainty delivered the minimum. Surge should pierce
  soak, or floor well above 1, or roll damage twice and take the better. It
  must never be able to feel like a wasted button.
- **The haven layer has still never been played.** Two delvers, two deaths,
  both on day 1, both carrying a full coat and an empty account. Charter §3
  ("real decisions live between fights") describes a layer no session has
  reached. The cause is structural: salvage value scales with depth, the
  surface reset is only worth taking when you are already hurt, and every
  decision point therefore favours `delve`. Candidates: bank a fraction of
  carried salvage on death; a standing debt or commission that forces a
  return; diminishing returns on a single descent; supply that cannot be
  refilled without surfacing *and* fights that consume it.
- **Three dead traits and a dead stat.** `armored` (cullet crab, vitrified
  watchman) and `pack` (chorus pane, shardswarm) are in `ALLOWED_TRAITS` and
  the catalog and are read by no code in `engine.py`; only `brittle`,
  `lurker`, `relentless`, `swift` do anything. **CRAFT** is still dead,
  carried unharvested from session 1.
- **Site templates repeated inside one descent** — `watchman's rotunda` at
  depth 2 and again at depth 3. Covered diegetically (an epoch that built the
  same guard-round twice, one on top of the other) and it landed well, but by
  luck. Consider excluding a site name already used this expedition.
- **`ui/delver.txt` still has no stat legend** (session 1 note, unharvested).
  I hand-wrote one into the opening scene, which worked, but it should live
  on the sheet.
- **The Monte Carlo was the single best DM tool of the session.** Running the
  engine 4,000–6,000 times — first over the pending fight, then from the
  *actual paused state* with the real RNG swapped out — let me hand the
  player true odds at the decision that mattered. It made the pause feel
  real and kept me honest. This should be a first-class command
  (`session.py odds`, `session.py odds --resume`), not a scratch script the
  DM improvises. Note the integrity constraint: it must reseed, never peek
  at the live fight's RNG.
- **The one-pause rule works.** It fired exactly once, at exactly the right
  moment, and it was the high point of the session.

**Player notes:**

- Answers were given in brief; the three questions were not taken in detail.
- best: the game was enjoyable, and seeing more of the mechanics was part of
  the enjoyment — the visible machinery is a feature, not a leak.
- friction: not given this session.
- wish: not given this session.
