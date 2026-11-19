# The skeleton is travel's, copied and renamed

art's skeleton — the `create_app(dist)` factory, the revision-comparing health
probe, the `deploy/migrations` hook, the production compose file and the two
workflows — is `travel`'s. `travel` is the smallest app on the box and had
already been through a first deploy, so its shape is the one with the
production failures already taken out of it.

Rejected:

- **Starting from `media`**, which carries months of features this app has no
  use for. `media` stays the reference for conventions; this is about which
  repository to copy files from.
- **Starting from nothing.**
