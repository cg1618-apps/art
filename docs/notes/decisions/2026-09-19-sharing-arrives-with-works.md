# Sharing arrives with Works, and is designed in from the start

Nothing is shareable until there are finished pieces to share, so the `/s/...`
prefix and the `visibility` field stay reserved and unread until the Works
module. They exist anyway — `note` has carried `visibility` from its first
migration — because adding a column later is trivial and retrofitting
visibility checks across every read path is the expensive half.

**Visibility belongs on the entity, not on a section of the app**: a piece may
be public while the practice notes attached to it stay private.

What is deliberately **not** shareable: exercises and records are the practice
log, and references are other people's pages, so none of them carries the
field. A finished piece is shared as a Work.

The mechanics — `/s/...`, the three values, share tokens rather than accounts,
and the refusal tests the flip to `public` needs — are in `CLAUDE.md`, "Who
can see it".
