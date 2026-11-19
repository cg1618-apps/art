# The timer is server-held state, on the same stack

The platform's `CLAUDE.md` names the stopwatch as the one feature that might
want a different shape from the rest. It got one deliberately, on the same
stack: **the server holds the running timer and the browser only ticks.** This
is art's recorded divergence from `media`'s shape. The API is in `api.md`,
"Timer"; the page in `frontend.md`, "The timer".

- **A refresh, a closed tab or a sleeping laptop loses nothing**, and the timer
  shows on any device. Rejected: browser-only state — simpler, and lost the
  first time a tab closes. A lost session is a reason to stop logging.
- **Times come from the database clock**, and each response carries `now`, so
  a skewed laptop clock skews nothing.
- **One timer, one row**, enforced by a unique index on a constant: there is
  one person here.
- **Stopping does not create the record.** It opens the record form prefilled,
  and the timer waits, stopped, until that form is saved; saving creates the
  record and removes the timer in one transaction. The owner adds a method or
  notes, and a refused save loses nothing.
- **A countdown runs into overtime** rather than stopping, with one tone at
  zero: Clip Studio Paint is in front, and the stroke in progress is finished.
- **No interval mode and no chaining.** Line of Action already times 30s × 20,
  and the owner chose one timer per record over a "next item" button.
- **The default countdown** — 10 minutes on weekdays, 30 at the weekend — is
  the owner's schedule, held as a constant until the Schedule module owns it.
