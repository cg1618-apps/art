# Options follow `media`'s tiers, with four divergences

Tags and every other open vocabulary are `system_option` rows — `media`'s
Tier 2 — decided by `media`'s question: does code branch on the exact value?
The tiers themselves are in `options.md`.

Rejected: `travel`'s lighter `label_option`, suggested values stored as text,
because a rename there has to rewrite every row that copied the text. The
owner also asked for system options by name.

Where art departs from `media`, deliberately:

- **Integer ids**, not a UUID `system_id`. art's skeleton is `travel`'s, and
  every table in `travel` and `food` uses integers.
- **`description` beside `remark`.** `media`'s `remark` is an admin note shown
  read-only on one page. A description is written for the moment a value is
  picked, and every picker shows it: two audiences, two columns.
- **Categories are registered in code** (`OPTION_CATEGORIES`), not free text on
  the API. Every category is read by some field, so an unregistered one is a
  typo, and each needs a label and a description of its own for the Options
  page.
- **A delete in use states its cost and is checked.** `media` deletes silently
  and cascades the tags away. Here the page shows the count, the request
  echoes it, and a stale count is a 409 — `food`'s `StaleCountError`.

No scope, usage or alias tables: they answer questions `media` has (which media
type, which source field, which external API string) that art does not.
