---
name: wrapup
description: End-of-play-session wrap-up rite for UNDERSTORY — final sheet commit, session notes into docs/PLAYNOTES.md, three feedback questions to the player, mirror to main. Use when a play session is ending or the player says they are done for now.
---

# The wrap-up rite

You are ending an UNDERSTORY play session. Follow `docs/PLAYBOOK.md`
§"The wrap-up rite" exactly:

1. Run the `sheet` command so the ui/ pages match the final table state.
2. Draft the PLAYNOTES entry (see format below) with the DM-notes half
   filled from your own chair: mechanical friction, joyless moments,
   balance suspicions, ideas that surfaced in play. Be honest — this file
   is how the game gets better.
3. Ask the player, in one short message, three questions: best moment of
   the session, worst friction, one wish. Wait for the answers.
4. Rewrite their answers as clean prose into the player-notes half,
   append the entry to `docs/PLAYNOTES.md`, and commit on the play branch.
5. Mirror the PLAYNOTES change to the main branch (checkout main, apply
   the same append, commit, push, return to the play branch) — the same
   rite as the Ledger.
6. Close the table in the fiction: one line, where the delver rests.

Entry format (append, never edit old entries):

```
## <YYYY-MM-DD> — <delver name> (<play branch>) — session <n>
Where things stand: <one or two lines of fiction/state>
DM notes:
- <item>
Player notes:
- best: <...>
- friction: <...>
- wish: <...>
```
