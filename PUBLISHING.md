# Publishing Guide

## Prerequisites

1. **PyPI Account**: Create accounts on both [PyPI](https://pypi.org) and [TestPyPI](https://test.pypi.org)
2. **GitHub Repository**: Ensure your code is pushed to GitHub
3. **Trusted Publishing**: Configure trusted publishing for secure authentication

## Setup Trusted Publishing (Recommended)

### 1. Configure PyPI Trusted Publishing
1. Go to [PyPI Account Settings](https://pypi.org/manage/account/publishing/)
2. Add a new "pending publisher":
   - **PyPI project name**: `agentman`
   - **Owner**: `yeahdongcn`
   - **Repository name**: `agentman`
   - **Workflow filename**: `publish-to-pypi.yml`
   - **Environment name**: `pypi`

### 2. Configure TestPyPI Trusted Publishing
1. Go to [TestPyPI Account Settings](https://test.pypi.org/manage/account/publishing/)
2. Add a new "pending publisher" with the same details but environment name: `testpypi`

### 3. Configure GitHub Environments
1. Go to your GitHub repository → Settings → Environments
2. Create two environments:
   - `pypi` (for production releases)
   - `testpypi` (for testing)
3. Add protection rules as needed (e.g., require reviews for `pypi`)

## Publishing Methods

### Method 1: Automated Publishing via GitHub Actions

#### Test Release to TestPyPI
1. Go to Actions tab in your GitHub repository
2. Select "Publish to PyPI" workflow
3. Click "Run workflow"
4. Select `testpypi` environment
5. Click "Run workflow"

#### Production Release to PyPI
1. Create a new release on GitHub:
   - Go to Releases → "Create a new release"
   - Create a new tag (e.g., `v0.1.0`)
   - Add release title and description
   - Click "Publish release"
2. The workflow will automatically trigger and publish to PyPI

### Method 2: Manual Publishing

#### Install Publishing Dependencies
```bash
uv sync --extra publish
```

#### Build the Package
```bash
uv run python -m build
```

#### Check the Package
```bash
uv run python -m twine check dist/*
```

#### Upload to TestPyPI (Testing)
```bash
uv run python -m twine upload --repository testpypi dist/*
```

#### Upload to PyPI (Production)
```bash
uv run python -m twine upload dist/*
```

## Version Management

Before publishing, update the version in `pyproject.toml`:

```toml
[project]
name = "agentman"
version = "0.1.1"  # Update this
```

## Installation Testing

After publishing to TestPyPI, test the installation:

```bash
# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ agentman

# Install from PyPI (after production release)
pip install agentman
```

## Troubleshooting

### Common Issues

1. **Package name already exists**: Choose a different name in `pyproject.toml`
2. **Version already exists**: Increment version number
3. **Authentication failed**: Ensure trusted publishing is configured correctly
4. **Missing files**: Check that all necessary files are included in the build

### File Inclusion

The package automatically includes:
- All Python files in `src/agentman/`
- `README.md`
- `LICENSE`
- Files specified in `MANIFEST.in` (if present)

## Security Notes

- Never commit API tokens to the repository
- Use trusted publishing instead of API tokens when possible
- Keep your PyPI account secure with 2FA enabled
- Review all changes before publishing to production
