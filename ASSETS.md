# Asset manifest

T04 uses the seven Poly Haven CC0 sources below. Poly Haven explicitly permits sharing and raw redistribution under [CC0](https://polyhaven.com/license). Attribution is not required by CC0; the artists are credited here. Asset discovery was powered by Poly Haven's public API; the game has no live API dependency.

[SourceArt/asset-manifest.json](SourceArt/asset-manifest.json) is the authoritative per-file manifest: it records the source URL, author, upstream `files_hash` version, license evidence, attribution, exact download URLs, upstream MD5, SHA-256 for every retained source and imported Unreal file, and explicit project-authored file coverage. The table's version identifies the exact upstream source set; byte-level pins are in the JSON.

| Asset | Author | Upstream version | Covered source directory |
| --- | --- | --- | --- |
| [Modern Arm Chair 01](https://polyhaven.com/a/modern_arm_chair_01) | Vibrant Nordic | `6893f36e58dddba95bd0ae1f1ef38537c1852a0b` | `SourceArt/PolyHaven/modern_arm_chair_01/` |
| [Modern Coffee Table 01](https://polyhaven.com/a/modern_coffee_table_01) | Amin | `31772c0aab6f930a18de82606146c0a97f08b7d0` | `SourceArt/PolyHaven/modern_coffee_table_01/` |
| [Potted Plant 02](https://polyhaven.com/a/potted_plant_02) | Rico Cilliers | `155661c96a28b9eb143e866daeb41f5a076d6677` | `SourceArt/PolyHaven/potted_plant_02/` |
| [Ceramic Vase 03](https://polyhaven.com/a/ceramic_vase_03) | James Ray Cock | `df64b230fb44e0aceff07e3dc0aa97b7ebcb1143` | `SourceArt/PolyHaven/ceramic_vase_03/` |
| [Wood Floor](https://polyhaven.com/a/wood_floor) | Dimitrios Savva | `a44e6375a09ab98780b876e709f2629e7ed30409` | `SourceArt/PolyHaven/wood_floor/` |
| [Fabric Pattern 07](https://polyhaven.com/a/fabric_pattern_07) | Rob Tuytel | `af042f95980f6ccc87285c3bc23e11671a5fecde` | `SourceArt/PolyHaven/fabric_pattern_07/` |
| [White Plaster 02](https://polyhaven.com/a/white_plaster_02) | Rob Tuytel | `508068441dd24eb06ef6d269a43f6ea7c8bade6b` | `SourceArt/PolyHaven/white_plaster_02/` |

All retained texture maps are 2048 pixels on their largest axis. No 4K exception is needed. The source glTF files, geometry buffers, and referenced textures are editable in Blender; no redundant downloads, source archives, previews, or caches are committed. Imported content lives under `Content/Environment/RoomA`. The fabric and plaster materials retain normal/roughness detail but deliberately mute the original colour patterns to match the apartment palette.

The shell, sofa, sideboard, floor lamp, rug, framed geometric art, books, trim, and fixtures are project-authored. `scripts/create_room_a_furniture.py` is the editable deterministic Blender 4.5.3 source for the four authored meshes; their GLB exports are the Unreal import sources. Gameplay Blueprints, proxy NPCs, and dialogue text remain project-authored. Unreal's engine primitives are referenced from the installed engine, not redistributed as source files.

Git LFS tracks the art binaries and furnished map. `scripts/test-asset-manifest.ps1` rejects missing, modified, uncovered, or unapproved art and enforces the 2K texture profile and retained 8 GiB ceiling. `scripts/update-asset-manifest.ps1` refreshes and validates staged output hashes before transactional publication; it refuses changed pinned source files. See [Room A preparation and acceptance](docs/room-a.md) for reproduction and visual review.
