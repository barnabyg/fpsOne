---
status: accepted
---

# Keep the project public and assets redistributable

Keep `barnabyg/fpsOne` public and commit only project content whose license permits source redistribution from a public repository. This preserves the requirement that a clean clone can reproduce the editable project without relying on private marketplace entitlements, even though it excludes many convenient free Fab, Megascans, and MetaHuman assets.

## Consequences

The project has a zero monetary budget. Every external asset requires recorded provenance and a redistribution-compatible license; CC0 is preferred and attribution-compatible open content is acceptable. Raw Fab Standard, Megascans, MetaHuman, and other marketplace-only assets must not enter the repository. Large redistributable binaries use Git LFS, and the initial asset set must remain deliberately small enough for GitHub Free limits.
