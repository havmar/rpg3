# UNDERSTORY — Dispatcher

This repo is **UNDERSTORY** — an expedition roguelike on a dying earth,
played entirely through a coding-agent session. The agent is the DM and the
developer; deterministic Python scripts are the engine. One player (Marton),
no audience, no product.

This file is the dispatcher: it routes a session, it does not govern one.
(Body kept agent-name-free so it can be copied to another agent's
instruction filename unchanged.)

## Session start — always

1. `git status --short --branch`. Clean tree → `git pull --ff-only`.
   Dirty tree → preserve and understand the local work before pulling.
   Never assume the checkout is current.
2. Read `docs/CHARTER.md` — the constitution. It overrides habit.
3. Settle the session MODE before doing anything else:

- **Play mode** (running or testing a game): load `docs/PLAYBOOK.md`,
  `docs/SETTING.md`, the `ui/` pages, `LEDGER.md`, and the save. Nothing
  in the dev docs governs the table.
- **Dev mode** (changing the game): load `docs/ENGINE.md` first — never
  start a dev task from this dispatcher alone.

## The document system

- `docs/CHARTER.md` — vision, pillars, the vibe-design contract. Changes
  rarely and deliberately.
- `docs/SETTING.md` — the world seed and tone. Canon accretes in play;
  never contradict a committed fact.
- `docs/PLAYBOOK.md` — how the table is run: session flow, the ui/ pages
  and message protocol, settled non-numeric rules of play.
- `docs/ENGINE.md` — how the game is built: architecture, save model,
  testing/bench infrastructure, code conventions, dev process.
- `docs/BENCHLOG.md` — dated bench entries (created with the first bench).
- `docs/archive/` — provenance (RPG2 infrastructure export). Historical;
  the live docs win.
- `LEDGER.md` — the legacy ledger. The only file that survives everything.

## Hard rules (full versions in the charter)

- **The engine owns the numbers.** All rolls happen in Python with seeded
  RNG. Narrate from engine logs; never invent or override a numeric
  outcome.
- **Autocombat.** A fight resolves in one engine run, at most one
  mid-fight pause. Never round-by-round in chat.
- **No backwards compatibility, ever.** No migration code. A feature that
  breaks the save means a fresh save (a new delver). Only `LEDGER.md`
  survives wipes.
- **Git is the save system.** One playthrough per `play/<delver>` branch;
  ui/ pages committed, `save.json` untracked. Engine code and play state
  are always separate commits, on separate branches.
- **No GUI, no external services, no separate agent process.** The stack
  is this repo plus the agent session.

## Status

v0.1 playable (plan 0001, benched 2026-08-23): full expedition loop —
creation, delve, autocombat with one pause, camp, surface, bank, train,
buy — through `session.py`, with contract suites (`python -m unittest`)
and benches (`python tune.py`). The Vitric Age runs 6 depths and has a
sealed floor. Next milestone: first real playthrough on a `play/<delver>`
branch, then harvest PLAYNOTES. Update this status as milestones land.
