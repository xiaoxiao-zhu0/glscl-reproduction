# Continual-learning visual checks

Load only for continual/incremental-learning projects. These are questions and common traps, not a universal method specification. Resolve every answer against the current project; store its exact contract in the workspace.

- Establish the protocol: class/task/domain incremental, task-ID availability at inference, experience boundaries, passes/epochs, memory budget and compute accounting. Do not label a multi-epoch staged experiment strictly single-pass online because a cited baseline is online.
- Distinguish sample selection, replay retrieval, representation learning and prediction calibration. A frozen selection encoder may coexist with a trainable backbone; never fuse them because both encode images.
- Trace incoming samples, persistent memory, candidate pool, retrieved batch and insertion timing separately. Parallel memory contributors must converge independently; sequential arrows assert a different algorithm. Fixed capacity and fixed replay-batch size are separate invariants.
- Establish what a replay score observes and when. Historical same-item deterioration, predicted interference from a virtual update, gradient diversity and Shapley valuation are different mechanisms. A reference's attractive diagram does not authorize importing its mechanism.
- Draw temporal causality explicitly. Information first observed during the current update cannot guide an earlier choice unless the method actually performs an authorized look-ahead. Show abstention and replacement limits if they affect behavior.
- For multiple heads, identify their feature inputs, losses and inference combination. Mark detach/stop-gradient at the correct edge and distinguish forward information from backward gradients. Shared features do not imply every loss updates the shared backbone.
- Embeddings and loss traces are schematic unless generated from actual project data. Keep original experiment figures and verified axes/numbers as evidence; do not ask a generator to invent plausible improvements.

Useful literature visual roles include iCaRL for stage/memory context, MIR for stream-memory-replay grouping, ASER/GSS for visually distinguished candidates, SCR for feature-space comparisons, BiC/LUCIR for classifier/calibration grouping and prompt methods for module boundaries. Inspect actual figures and specify forbidden transfers. None of these papers automatically defines the current project's algorithm.

Prefer an overview for interface relationships, a close-up for sample selection, and a temporal strip for delayed evidence. Use native arrows/labels and real data plots for scientific authority; bitmap artwork can supply recognizable sample instances and visual hierarchy. Respect the user's disclosure level: expose the intended functional relationships without adding private scores or solver details.
