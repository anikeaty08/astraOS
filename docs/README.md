# AstraOS design index

This directory holds the product and engineering design in small, reviewable parts.
The documents describe a target, not a claim that every capability already exists.

1. [Vision and success criteria](vision.md) — who the OS serves and what “usable” means.
2. [System architecture](architecture.md) — boundaries, contracts, data flow, and failure handling.
3. [Technology decisions and research](decisions.md) — choices, alternatives, and primary sources.
4. [Feature inventory and delivery plan](roadmap.md) — ordered slices with acceptance gates.
5. [First feature: persistent text workflow](features/persistent-text.md) — implementation contract.
6. [Repository layout](repository-layout.md) — current ownership and incremental folder migration.
7. [Standalone text editor](features/text-editor.md) — next userspace application contract.
8. [Default userspace session](features/userspace-session.md) — supervised shell and recovery behavior.

The current implementation evidence lives in [the feature tracker](../.agent-state/feature-list.json).
Update the relevant document when a decision or contract changes; keep the README short.
