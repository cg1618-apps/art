# Open items

Known defects and unmade decisions that nobody is working on. An item is
deleted in the same change that settles it.

## Where uploaded images live

References, works and records all want images, and `food` needs them too, so
this is a platform question rather than an app one: a bind-mounted directory
outside the container image, and backup coverage, are things `media` has and
the platform has not generalised. Nothing here invents its own answer.

- **An uploaded image is the one kind of data that cannot be re-fetched.**
  `media` distinguishes covers, which its APIs can supply again, from
  `static/library`, which nothing can. Whatever storage is chosen has to back
  up the second kind.
- **For records, the owner may keep images in Google Drive or Google Photos**
  instead of uploading them here; that is part of the same open design.
- An image reference's shape — a column on `reference`, a sibling table, or a
  child of it — is decided with the storage, not before.

## `deploy/migrations downgrade` does not refuse an irreversible revision

The platform's hook contract (`docs/registry.md` in the platform repository)
requires `downgrade` to refuse any revision that declares itself
irreversible. art's hook passes the target straight to Alembic. That holds
only because no revision carries the marker yet. The first revision that
needs one should adopt `media`'s `irreversible = True` marker and the check
in its hook in the same change.
