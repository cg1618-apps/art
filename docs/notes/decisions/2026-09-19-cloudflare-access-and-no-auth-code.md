# Cloudflare Access over the whole hostname, and no auth code in the app

art has one user and no accounts. Cloudflare Access authenticates every
request before it reaches the box, so the app has no login page, no session,
no password and no route guard, and reads and writes share one prefix.

Rejected: an app-level password, for the same reasons `travel` rejected one.

Publishing later does not change this: a shared piece is an Access policy
exempting `/s/...` and a share token on the object, never a user table. See
`CLAUDE.md`, "Who can see it".
