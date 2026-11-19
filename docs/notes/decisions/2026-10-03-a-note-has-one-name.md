# A note has one name

The owner's words: "for a note, we just need one name. we don't need 4 fields
for name." A note is the owner's own writing, looked up by the word they gave
it. The three name slots and the aliases are `food`'s dish shape, which goals,
stages and exercises keep; notes inherited them by default, and nobody filled
more than one.

- **`name`, required, trimmed, not blank, not unique.** Two notes may share a
  name.
- **No aliases**, not even for search: the one name is what is searched.
  References carry one `name` on the same reasoning. This is a decision about
  notes and references, not a new house rule.
- **Search covers the body.** With no aliases, the body is the only place a
  second name for a thing can live, and a note that cannot be found by a word
  it contains is the worse failure for the one person who wrote it. Rejected:
  leaving the body out so that a word inside a long note does not bury the
  note you meant — the list is ordered by name, so a name match is not
  outranked; it is only no longer the only way in.
