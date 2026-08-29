# Verification Dashboard

Create or update the dashboard whenever the automated verification workflow changes. The verifier owns the machine-readable results; the renderer turns the latest results into one local static HTML page.

The dashboard is complete when it shows:

- the tested Git revision and dirty-tree fingerprint;
- the validation mode, distinguishing complete agent validation from deterministic human-local validation;
- pinned Unreal and supporting-tool versions;
- every required gate from `verification.md`, with status and duration;
- direct links to retained logs and reports;
- the current visual-acceptance screenshot and multimodal review when that gate is active, or the ticket-scoped activation condition when it is not yet applicable;
- the packaged-build artifact path;
- all warning exceptions; and
- a conspicuous stale marker when results do not match the current working tree.

Use red for any failed, missing, skipped, or stale gate required by the active mode. Show the visual gate as not applicable, rather than passed, in human-local mode. Use green only when a required gate produced current evidence. Keep generated results and the rendered dashboard out of Git; check in the verifier, dashboard renderer, and empty output-directory placeholders needed for a clean clone.

During incremental implementation, the verifier may also show a future-feature gate as not applicable under the narrowly documented profile in `verification.md`. The dashboard must state which ticket activates it; a bare or permanent exemption is invalid.

Open the dashboard after the complete verifier finishes so the agent can inspect the same evidence presented to the user.
