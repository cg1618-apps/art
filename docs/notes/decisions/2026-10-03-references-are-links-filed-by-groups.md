# References are links, filed by groups

The owner's words: "It is essentially some links and notes. For each link, we
can add multiple group tags to it. There will be more things beyond just
links, but we'll deal with those later." The schema is in `data-model.md`.

- **One table, `reference`: name, link, notes.** One required name, as a note
  has. The link is validated as a resource's is, by the same `normalise_link`.
- **No `kind` column.** The other kinds of reference are not designed, and a
  kind with one value is a column every row pays for and nothing reads. An
  image reference needs storage the platform has not decided
  (`docs/open-items.md`), so its shape — a column, a sibling table, or a child
  of this one — is decided then, with the real thing in hand.
- **No `visibility`.** A reference is someone else's page; sharing shares the
  owner's own work.
- **Groups are a Tier 2 option category, `reference_group` (參考分組)**, seeded
  empty: the owner creates the groups. 表情 and 配件 are groups, not
  libraries.
- **The link table is `reference_group`**, `<owner>_<tag>` as `note_topic` and
  `exercise_topic` are. Rejected: `reference_group_link` — in this schema a
  `_link` table holds URLs (`drill_source_link`), and a tag table named like
  one would read as a list of links.
- **A library row carries `notes_excerpt`, not the notes**, as a note's row
  carries its summary and not its body. A reference has no summary of its own;
  the excerpt is enough to recognise one in a list without paying for every
  note in full.
- **A card holds two links**: the name opens the reference itself in a new
  tab — the reason it was kept — and 詳細 opens its page here. Nested anchors
  are invalid, so the card is an article with both inside.
