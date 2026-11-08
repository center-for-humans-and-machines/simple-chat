# Repository checks

`ci.yml` runs lint, Docker builds, backend and frontend tests, and a production
Compose smoke test on pull requests, `main`, and `v*` release tags.

`dependabot.yml` proposes weekly updates for actions, hooks, Python, npm, and
Docker dependencies. CODEOWNERS names the two maintainers.
