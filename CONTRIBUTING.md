## Contributing to `subwinder`

If you want to help with the development of `subwinder` then feel free to pick up on any of the issues listed. If you would like to contribute a new feature or modify existing behavior then please raise an issue first to discuss the changes.

### Style Guidelines

This library uses both `black` and `flake8` to lint and format code and for this reason these are both listed under the `tool.poetry.dev-dependencies` in the `pyproject.toml`. Please ensure any code contributed follows both of these (there are some incompatible rules between the two that are ignored in either the `.flake8` file or under `tool.black` in the `pyproject.toml`).

### Tests

Unit testing is done with the help of `pytest` (also one of the `dev-dependencies`). Make sure any changes you contribute pass the test suite, or fix the issue if the test suite is inaccurate. Preferably any new features should include tests to ensure the behavior is correct.
