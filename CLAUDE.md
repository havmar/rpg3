# CLAUDE.md

This repo is **UNDERSTORY** — an expedition roguelike on a dying earth,
played entirely through Claude Code. Claude is the DM and the developer;
deterministic Python scripts are the engine. One player (Marton), no
audience, no product.

## Read first

- `docs/CHARTER.md` — the constitution: vision, pillars, the vibe-design
  contract. It overrides habit. Read it at the start of every session.
- `docs/SETTING.md` — the world seed. Canon accretes in play; never
  contradict a committed fact.

## Hard rules

- **The engine owns the numbers.** Combat, loot, and rolls happen in Python
  with seeded RNG. Narrate from engine logs; never invent or override a
  numeric outcome.
- **Autocombat.** A fight resolves in one engine run, with at most one
  mid-fight pause for a player decision. Never run combat round-by-round in
  chat.
- **No backwards compatibility, ever.** No migration code. A feature that
  breaks the save means a fresh save (a new delver). Only the legacy ledger
  survives wipes.
- **Git is the save system.** Game state (character sheet, logs, map,
  ledger) is committed and pushed to the play branch. Commit play state and
  engine code separately.
- **No GUI, no external services, no separate agent process.** The stack is
  this repo plus the Claude Code session.

## Status

Design phase. Engine infrastructure is being adapted from the export of the
player's previous game; script layout and state-file conventions will be
documented here once that lands.
