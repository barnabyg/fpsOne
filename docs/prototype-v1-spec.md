## Problem Statement

The user needs a minimal first-person interactive testbed that demonstrates high-quality real-time environments, humanoid NPCs, reusable world interaction, and short dialogue without the scope of a complete game. The current repository contains no engine project or gameplay implementation, so there is no playable way to evaluate what a focused Unreal Engine prototype can achieve.

The testbed must remain small enough to build and understand, yet visually compare favourably with unmodded Skyrim Special Edition and Fallout 4 at PC Ultra settings from normal gameplay distances. It must also remain reproducible from a public repository with a zero monetary budget, which excludes raw assets whose licenses prohibit public redistribution.

## Solution

Create a Blueprint-only Unreal Engine 5.8 testbed for Windows 11. The player explores two highly dressed rooms in a modern apartment using keyboard and mouse. A closed animated door connects the rooms, and each Room contains one realistic humanoid NPC. Looking directly at a nearby Door or NPC reveals an Interaction Prompt; E performs the contextual Interaction through one generic Interactable contract.

NPC Interaction begins a short, repeatable, non-branching Dialogue Interaction. The implementation deliberately excludes unrelated game systems and accepts later refactoring if future versions demand more complex behaviour.

Deliver both the editable project and a locally generated packaged Windows ZIP. Use publicly redistributable, zero-cost environment, character, and animation sources with documented provenance. Validate behaviour through headless Blueprint functional tests, packaging checks, strict diagnostics, and an agent-mediated multimodal review of current gameplay screenshots.

## User Stories

1. As the player, I want to launch a packaged Windows prototype, so that I can evaluate the experience without opening the editor.
2. As a developer, I want to open the complete editable Unreal project, so that I can inspect and extend the testbed.
3. As the player, I want to start inside Room A, so that the prototype immediately presents its playable environment.
4. As the player, I want to move forward, backward, left, and right, so that I can explore both Rooms naturally.
5. As the player, I want mouse movement to control my viewing direction, so that navigation feels like a conventional first-person experience.
6. As the player, I want a small centre dot during free movement, so that I can understand where Interaction Focus is evaluated.
7. As the player, I want movement to exclude sprinting, jumping, and crouching, so that the control surface remains deliberately narrow.
8. As the player, I want Room A to look like a furnished modern living room, so that the prototype demonstrates a convincing residential interior.
9. As the player, I want Room B to look like a furnished home office and guest room, so that the second space feels distinct but coherent.
10. As the player, I want late-afternoon daylight and warm practical lighting, so that materials, furniture, and characters are presented attractively.
11. As the player, I want the closed Door to be clearly visible from the starting composition, so that I understand how the Rooms relate.
12. As the player, I want NPC A visible from the starting composition without already being focused, so that discovery remains under my control.
13. As the player, I want an entity to become the Interaction Focus only when it is nearby, centred in view, and unobstructed, so that prompts feel intentional.
14. As the player, I want only one Interactable focused at a time, so that E always has an unambiguous result.
15. As the player, I want the Interaction Prompt to describe the available action, so that I know whether E will talk, open, or close.
16. As the player, I want prompts presented without outlines or glowing objects, so that interaction feedback does not undermine visual realism.
17. As the player, I want E to open the focused closed Door, so that I can enter Room B.
18. As the player, I want E to close the focused open Door, so that the same interaction remains reversible.
19. As the player, I want the Door to swing smoothly inward through 90 degrees, so that it behaves like a plausible apartment Door.
20. As the player, I want the closed Door to block passage, so that opening it has a real spatial purpose.
21. As the player, I want the Door to avoid colliding with the player or NPCs while it moves, so that the simple animation cannot trap or shove them.
22. As the player, I want each NPC to occupy physical space, so that I cannot walk through them.
23. As the player, I want each NPC to look like a distinct casually dressed adult, so that the two residents are visually differentiable.
24. As the player, I want NPCs to idle naturally and acknowledge my presence subtly, so that they do not look like static props.
25. As the player, I want E to begin a Dialogue Interaction with the focused NPC, so that NPCs demonstrate the same generic Interaction mechanism as the Door.
26. As the player, I want a speaker-labelled dialogue panel, so that I can follow the short exchange without voice acting.
27. As the player, I want E to advance each dialogue line, so that I control the pace of the exchange.
28. As the player, I want movement paused but limited mouse look retained during dialogue, so that the Interaction is focused without becoming a rigid cutscene.
29. As the player, I want the centre dot and Interaction scanning hidden or paused during dialogue, so that competing affordances do not distract from the exchange.
30. As the player, I want normal control restored after the final line, so that dialogue ends cleanly.
31. As the player, I want either Dialogue Interaction to remain repeatable, so that I can exercise the testbed repeatedly without restarting.
32. As the player, I want the Door and dialogue state reset whenever the application launches, so that every session begins from a predictable state.
33. As the player, I want Escape to exit the packaged prototype immediately, so that no menu system is required.
34. As the user, I want visual quality comparable to or better than the stated reference games at ordinary viewing distances, so that the prototype tests modern presentation rather than placeholder art.
35. As the user, I want the environment and NPCs assessed from repeatable screenshots, so that the visual-quality claim has inspectable evidence.
36. As the user, I want the packaged experience to target 2560 × 1440 on the RTX 4090-class host, so that its rendering profile matches the available hardware.
37. As the user, I want performance treated as observational rather than a major optimisation project, so that proof-of-concept effort stays focused on functionality and visual quality.
38. As a developer, I want the player to interact through one shared Interactable contract, so that adding different world entities does not require type-specific player branches.
39. As a developer, I want one player-owned component to manage tracing, focus, prompts, and E input, so that the primary interaction seam is cohesive and testable.
40. As a developer, I want each NPC to own a small editable set of dialogue lines, so that simple content changes do not require a dialogue framework.
41. As a developer, I want one reusable dialogue presentation, so that both NPCs share behaviour without duplicated UI logic.
42. As a developer, I want every third-party asset documented with provenance and licensing, so that the public repository contains only legally redistributable content.
43. As a developer, I want editable character and art sources retained, so that the project can be reproduced and revised from a clean clone.
44. As a developer, I want large source and Unreal assets tracked through Git LFS within a disciplined storage budget, so that the public repository remains usable.
45. As a developer, I want automated interaction tests at the player-facing seam, so that generic focus, Door, dialogue, and input behaviour can be changed confidently.
46. As a developer, I want one canonical validation command, so that local verification is consistent and repeatable.
47. As a developer, I want validation to fail on project-controlled warnings and errors, so that diagnostics do not silently accumulate.
48. As a developer, I want the Win64 cook and package exercised by validation, so that editor success is not mistaken for a deliverable build.
49. As an agent, I want validation to capture the accepted gameplay views and require a current multimodal review, so that visible defects are tested rather than inferred from code.
50. As a human developer, I want local validation to skip the agent-only visual judgement explicitly, so that it can pass without an external AI service or credential.
51. As a developer, I want a local verification dashboard tied to the current working tree, so that test, package, diagnostic, and visual evidence can be inspected together.
52. As a future maintainer, I want the initial design to acknowledge likely refactoring instead of predicting unrequested systems, so that version 1 remains a deep, narrow seed rather than a speculative framework.

## Implementation Decisions

- Use Unreal Engine 5.8 under its zero-cost personal, non-commercial terms. Installation uses Epic Games Launcher and requires the user's Epic sign-in and EULA acceptance.
- Use a Blueprint-only project. Begin from a blank game rather than a feature template so no weapon, combat, arena, or other example behaviour is inherited.
- Use the internal project name `FPSOne` and display the product name as `fpsOne`.
- Target Windows 11 with keyboard and mouse only. Movement supports four horizontal directions and mouse look. Escape exits immediately.
- Keep all installed tools, caches, repository data, sources, and generated output on C:. The user will provide additional space if the installation requires it.
- Use a player-owned Interaction component as the single high-level seam for view-centre tracing, focus transitions, Interaction Prompt state, and E input.
- Define one Interactable Blueprint interface that supplies availability, contextual prompt text, and Interaction behaviour. Door and NPC implementations share this contract; the player contains no type-specific Door or NPC branches.
- Trace from the view centre to 250 cm. Focus requires a direct unobstructed hit and is limited to exactly one entity.
- Display a low-contrast centre dot during free movement and restrained lower-centre Interaction Prompt text on a translucent charcoal backing. Use no outline or glow effect.
- Build Room A as a 6 × 5 m living room and Room B as a 4 × 4 m home office/guest room, both with 2.7 m ceilings and no connecting corridor.
- Spawn the player in Room A facing the furnished space. Compose NPC A off-centre and make the closed Door legible without placing either under initial Interaction Focus.
- Implement the Door as a deterministic toggle. It swings 90 degrees inward into Room B over 0.75 seconds with easing. Closed collision blocks passage; leaf collision is disabled while moving and open, then restored after closing.
- Give each NPC a blocking capsule, natural idle, subtle glance or upper-body attention, eye blinks, and conversational body gestures. Do not implement navigation or syllable-accurate lip-sync.
- Store a short, neutral, non-branching line array on each NPC. Reuse one speaker-labelled bottom dialogue panel. Pause movement and interaction scanning, retain limited mouse look, advance with E, then restore control after the final line.
- Reset Door and dialogue state on every launch. Dialogue remains replayable.
- Build the apartment shell in Unreal and curate a small coherent set of photographic-quality Poly Haven CC0 furnishings, PBR materials, and lighting references.
- Create two visibly distinct CC0 characters with portable Blender, MPFB, and MakeHuman core assets. Use redistributable CC0 idle and conversational animation sources, with skeletal retargeting and cleanup as required.
- The repository stays public with a zero monetary budget. Commit only content licensed for raw public redistribution. Prefer CC0; compatible attribution licenses are permitted when notices are retained. Exclude raw Fab Standard, Megascans, MetaHuman, marketplace-only, non-commercial, no-derivatives, and share-alike assets.
- Maintain an asset manifest containing source URL, author, asset/version identity, license, attribution, content hash, and covered local files.
- Retain editable art and character sources plus deterministic export instructions. Exclude downloaded archives, redundant intermediates, engine derived data, caches, and packaged output.
- Track large public-redistribution-compatible binaries through Git LFS. Use 2K textures generally and reserve 4K for prominent skin, flooring, and close-view furniture. Keep retained LFS storage below 8 GiB.
- Use Deferred Rendering, DirectX 12, Shader Model 6, Lumen GI and reflections with hardware ray tracing, Virtual Shadow Maps, Nanite on supported opaque environment meshes, and TSR. Keep deforming NPC meshes off Nanite.
- Render at 2560 × 1440, initially from 75 percent internal resolution through TSR. Preserve the Lumen, Nanite, Virtual Shadow Maps, and TSR stack; reduce optional expensive reflection, shadow, resolution, and decorative-light settings first if interactivity suffers.
- Performance is observational and low priority. Record readily available timing with visual evidence but do not build an extensive performance harness or hard FPS gate.
- Produce a Development build for profiling and a Shipping Win64 build for delivery. Package the final output as a versioned local ZIP under the project's Git-ignored `Saved` directory.
- Provide setup, asset preparation, controls, editor startup, testing, packaging, clean-clone, and manual acceptance documentation.
- Work on `codex/minimal-fps-prototype`, create one cohesive verified implementation commit, and leave the branch unpushed for review.

## Testing Decisions

- Test externally observable behaviour at the highest available seam. The primary seam is the player-owned Interaction component acting through the shared Interactable contract; tests should not assert Blueprint graph layout, node choice, private variables, or incidental animation implementation.
- Add a purpose-built Blueprint Functional Test map because the repository has no existing executable code or testing precedent to reuse.
- Verify that an unobstructed Interactable within 250 cm gains Interaction Focus and exposes its contextual Interaction Prompt.
- Verify that focus is lost when the player looks away, moves out of range, or places occluding geometry between the view and the entity.
- Verify that focus remains singular when multiple Interactables are nearby.
- Verify Door Interaction through the shared contract: open request, eased state transition, collision disabled while moving/open, close request, and collision restored when closed.
- Verify NPC Interaction through the same shared contract: dialogue start, correct initial line, E advancement, final dismissal, and replay.
- Verify that movement and interaction scanning pause during dialogue, the centre dot is hidden, limited look remains available, and normal input returns after dismissal.
- Verify that application startup resets the Door to closed and leaves both Dialogue Interactions replayable.
- Validate the configured default map, project content references, and every project Blueprint with zero compile errors or warnings.
- Validate every external asset file against the asset manifest, including public redistribution permission and required attribution.
- Cook and package Win64 during the canonical suite. A successful editor session alone is insufficient evidence.
- Scan project, functional-test, cook, and package logs. Project-originated warnings or errors fail validation. Any unavoidable external engine or driver diagnostic requires a narrow recorded exception with origin, evidence, and consequence.
- Agents run the complete canonical validator, including automatic capture of four accepted gameplay views and a multimodal review tied to the tested Git revision and image hashes.
- The four visual views are Room A overview, NPC A at dialogue distance, the open-Door transition, and Room B with NPC B. Review covers rendering defects, composition, lighting, materials, furnishing density, NPC presentation, UI obstruction, and plausible parity with the stated unmodded reference games at normal viewing distance.
- Human-local validation runs the deterministic suite without an AI dependency and reports the visual gate as not applicable rather than passed.
- Generate a local static verification dashboard showing validation mode, current revision and dirty-tree fingerprint, tool versions, gate status and duration, logs, visual evidence and review, warning exceptions, and packaged artifact location. Stale or missing evidence must be conspicuous.
- Record readily available frame timing with the visual run. Performance is informational and does not fail version 1 unless it prevents interaction or meaningful visual review.
- Manually walk the Shipping build through both Rooms, both Dialogue Interactions, Door open and close, restored input, and Escape exit. Confirm expected presentation at 2560 × 1440.

## Out of Scope

- Sprinting, jumping, crouching, gamepad input, rebinding, accessibility settings, or alternative locomotion.
- Combat, weapons, damage, health, inventory, equipment, crafting, loot, quests, objectives, progression, factions, reputation, or economy.
- Main menu, pause menu, settings menu, save/load, persistence, checkpoints, or profiles.
- Branching dialogue, dialogue graphs, choices, conditions, quest integration, recorded voices, accurate lip-sync, or cinematic facial close-ups.
- NPC navigation, pathfinding, schedules, systemic AI, combat behaviour, crowd behaviour, or dynamic obstruction avoidance.
- Environmental audio, footsteps, Door sounds, music, ambience, or a general audio system.
- Day/night cycles, weather, multiple levels, accessible corridors, additional Rooms, outdoor exploration, or procedural generation.
- Controller, console, macOS, Linux, mobile, VR, or lower-spec hardware support.
- Runtime scalability menus, extensive performance optimisation, a hard automated FPS threshold, or offline path-traced presentation.
- MetaHuman, raw Fab Standard content, Megascans, proprietary marketplace-only assets, paid assets, or any content that cannot be redistributed publicly in source form.
- A production-ready interaction framework, generalized dialogue engine, plugin architecture, or speculative support for future systems.
- Hosted Unreal CI, a self-hosted GitHub Actions runner, external multimodal API credentials, or an in-game verification dashboard.
- Publishing the packaged ZIP, pushing the implementation branch, opening a pull request, deployment, or commercial distribution.

## Further Notes

- The testbed is personal and non-commercial, but every third-party asset still requires a license that permits its actual use and public source redistribution.
- Unreal Engine was selected over Godot because the visual target outweighs use of an open-source engine. The public-asset boundary was selected over convenient marketplace content because clean-clone reproducibility and repository visibility are fixed requirements.
- Default MakeHuman output is the largest visual-quality risk. Character skin, hair, clothing, materials, lighting, rig export, retargeting, and presentation require deliberate refinement to approach the reference games.
- All tool and content storage remains on C:. Unreal installation, derived data, source art, Git LFS duplication, and package staging can consume hundreds of gigabytes; the user has accepted responsibility for freeing space when required.
- Epic account authentication and EULA acceptance are the only anticipated interactive installation handoff. Tool versions and reproducible setup steps must be recorded after installation.
- The implementation should favour the current narrow behaviour and permit future refactoring rather than introducing abstractions for hypothetical systems.
