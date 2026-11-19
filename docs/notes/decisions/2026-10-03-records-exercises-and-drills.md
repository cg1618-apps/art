# Records, exercises and drills

Agreed with the owner before the design. The schema is in `data-model.md`.

- **An exercise is `food`'s dish and a drill its recipe.** The exercise
  (練習項目) is what is practised and sits on a stage; a drill (練法) is one
  prescribed way of doing it, from a course or the owner's own notes.
  "Exercise type" was rejected as a name: the owner found it awkward.
- **One record per exercise practised.** A ten-minute session of warm-up then
  stage work is two records, because progress is read per exercise.
- **A record names a drill, an exercise, or neither, never both**, so the two
  cannot disagree: through a drill the exercise is derived. `food`'s recipe
  lines name an ingredient or a dish on the same reasoning.
- **A test record names exactly one stage or one level**, held as
  `num_nonnulls(stage_id, goal_id) = CASE WHEN kind = 'test' THEN 1 ELSE 0
  END`. Rejected: `(kind = 'test') = (count = 1)`, which lets a practice
  record carry both.
- **Records RESTRICT what they name.** A record is history; a deleted drill
  that silently orphaned a month of records would be the worst kind of loss.
- **Location is kept** from the owner's old spreadsheet. Proposed and
  declined: "finished one unit", and a "what looked weird" tag. The old log is
  not migrated.
- **No visibility on exercises or records.** They are the practice log, never
  shared; a finished piece is shared as a Work.
- **The seed comes from what the owner already has**: their 細節指示 and the
  assignments of the three Udemy courses they finished without practising. The
  courses' own frequency wording is kept as written rather than normalised.
- **A drill's counts are only the records naming it**, while an exercise's
  take in records made through its drills too. They add up differently on
  purpose: a record naming only the exercise belongs to no drill.
