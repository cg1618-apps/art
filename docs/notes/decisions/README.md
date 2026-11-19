# Decisions

Why art is the way it is. **One decision per file**, named
`YYYY-MM-DD-<topic>.md` after the day it was made: a `# Title`, then the
reasoning and the alternatives that were rejected, so nobody proposes them
again unaware. A deliberate divergence from `media`, the platform's reference
implementation, is recorded here too.

- **No index.** The date-prefixed file names are the index; a list here would
  be one more file every pull request appends to, and the merge conflicts the
  one-file-per-decision rule exists to prevent would come back.
- **A decision file holds the *why*, not the *what*.** What the app does now —
  behaviour, rules, schema — belongs on the matching page in `docs/`
  (`api.md`, `data-model.md`, `frontend.md`, …).
- **Delete a decision when it stops binding.** A reversal gets a new file, and
  the file it overturns is deleted in the same commit; git keeps the history.

The rule is the platform's (`CLAUDE.md`, "Decisions are one file each").
