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

For linting the codebase using GitHub Actions we use both [pre-commit](https://pre-commit.com/) and [super-linter](https://github.com/super-linter/super-linter). The scripts below assume you are in the root directory of the project.

- Lint the code locally (runs both pre-commit and super-linter)

  ```sh
  ./script/lint
  ```

- Lint only using pre-commit

  ```sh
  ./script/lint-precommit
  ```

- Lint only using super-linter

  ```sh
  ./script/lint-superlinter
  ```
