# Setup verification — October 31, 2026

## Repository
- Independent local repository: `/Users/rosh/RoshProjects/Orbit`, branch `main`.
- Git 2.50.1 available; author identity configured.
- The owner subsequently authorized public `roshan-davis/orbit`; publication was prepared in a separate `setup/publish-public` worktree.
- GitHub authentication was verified as `roshan-davis` using Git's existing saved HTTPS credential; no credential was printed or written to the repository.
- Public visitors can read/clone and propose pull requests; write access is restricted to authorized collaborators.

## Verified
- Python API tests: **7 passed**, including authentication, validation, database persistence after restart, future-schema protection, CORS and disabled/unknown provider declarations.
- Reproducible Python dependency lock: `engine/uv.lock`; locked `uv sync` and `uv run ... pytest` passed.
- Frontend TypeScript check and Vite production build passed.
- npm lockfile generated; install audit reported zero vulnerabilities at setup time.
- Ignore rules cover environments, node modules, build output, local state and credentials. Git whitespace check passed.

## Environment limits
- System Python is 3.9.6. Homebrew Python 3.11.15 cannot bootstrap pip due to a native `pyexpat`/libexpat symbol mismatch; no system repair attempted.
- Tests used an isolated downloaded Python 3.12.13 under `/tmp/orbit-python` and ignored local virtual environments. That temporary runtime may be removed by the OS; use a working Python 3.11+ for future development.
- Tests emit one upstream Starlette/httpx deprecation warning; all pass. Reassess the test transport on a future dependency update.
- Rust, Cargo and rustup are absent. Tauri native compilation and packaged networking/lifecycle are unverified. Frontend build success does not verify the native shell.
- Original GitHub SSH probe failed DNS in the restricted environment; network-enabled probe failed host-key verification. No host trust records were changed.
- GitHub CLI was absent. An official CLI binary was downloaded under `/tmp/orbit-gh`. Its standalone auth check initially reported no sign-in; the later check using Git's existing saved HTTPS credential authenticated successfully. No new login flow was needed.

## Publication and ongoing workflow
GitHub repository creation succeeded with public visibility. The first push was rejected because the saved HTTPS token lacked `workflow` scope for `.github/workflows/checks.yml`; SSH authentication was also unavailable (`Permission denied (publickey)`). After the owner updated the credential in macOS Keychain, authentication as `roshan-davis` and the complete initial push to `origin/main` succeeded. The source, documentation and CI workflow are published without removing files or rewriting history.

Remote: https://github.com/roshan-davis/orbit. The owner authorized public visibility and the initial push. Future changes should be prepared and validated in a separate branch/worktree, preserving unrelated work. No license selected yet.
