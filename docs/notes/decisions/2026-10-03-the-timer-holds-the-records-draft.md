# The timer holds the record's draft

The owner writes the record while drawing, not only once the timer stops.

- **The draft is on the server**, as the timer is, so a refresh or another
  device finds it.
- **One JSONB column, not a record's worth of columns.** A draft is half-typed
  by design — a test with no target yet, a link not yet pasted — so its types
  are checked and nothing else. The record rules apply once, when it is saved,
  to the body that saves it; the server never merges the draft into that body.
- **Autosave, not a save button**, 800 ms after the typing stops. Saves go one
  at a time and before any action that moves the timer, because a late answer
  to an earlier PATCH could otherwise put a stale state back over a pause or a
  stop.
- **The stopwatch is the default** on the start form and on a drill's
  開始計時: the owner's call. The weekday and weekend minutes still fill the
  countdown when it is chosen.
