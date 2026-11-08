# Contributing

The following instructions assume a macOS development environment. However, similar steps can be followed for other operating systems. Refer to `pre-commit`'s [installation instructions](https://pre-commit.com/#install).

## Requirements

- `brew`

## Getting Started

Install your development environment with the following instructions:

```sh
./script/bootstrap-mac
```

## Usage

The scripts below assume you are in the root directory of the project.

- Lint the code locally with pre-commit

  ```sh
  ./script/lint
  ```

CI runs `.github/workflows/ci.yml` on pull requests, `main`, and release tags.
Its four checks are Lint, Build, Smoke test, and Tests. The smoke test starts
the production Compose stack and checks the backend, frontend, and dashboard.
`.github/workflows/codeql.yml` scans Python and JavaScript weekly and on PRs.
`.github/dependabot.yml` proposes dependency updates each week.
