# ADR 0001: Local-first engine and provider-independent agents
Status: accepted for initial implementation.

Use Tauri 2 with React/TypeScript for the desktop, Python/FastAPI for orchestration and SQLite for local persistence. Keep an agent's identity, role and skills separate from its model provider. Prefer official subscription-authenticated CLIs and local Ollama over paid APIs; prohibit API fallback.

This provides an inspectable local system and permits models to change without losing agent identity. Costs: packaging Python alongside Rust, securing a loopback service, adapter compatibility maintenance, and uncertain provider quota telemetry. Worktrees isolate concurrent Git edits but do not sandbox processes. External access and design services are later, separately verified connectors.
