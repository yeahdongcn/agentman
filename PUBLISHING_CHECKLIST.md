# Quick Publishing Checklist

Before publishing your package to PyPI, make sure you've completed these steps:

## Pre-Publishing Checklist

### 1. Code Quality ✅
- [ ] All tests are passing (`make test`)
- [ ] Code is properly formatted (`make format`)
- [ ] No linting errors (`make lint`)
- [ ] Documentation is up to date

### 2. Version Management ✅
- [ ] Version number updated in `pyproject.toml`
- [ ] Version follows semantic versioning (MAJOR.MINOR.PATCH)
- [ ] CHANGELOG.md updated (if applicable)

### 3. Package Configuration ✅
- [ ] `pyproject.toml` metadata is complete and accurate
- [ ] README.md is comprehensive and helpful
- [ ] LICENSE file is present
- [ ] All necessary files are included in build

### 4. Build and Test ✅
- [ ] Package builds successfully (`./scripts/build.sh`)
- [ ] Built package passes validation (`twine check`)
- [ ] Package installs correctly from build
- [ ] CLI command works after installation

### 5. PyPI Account Setup
- [ ] PyPI account created at https://pypi.org
- [ ] TestPyPI account created at https://test.pypi.org
- [ ] Trusted publishing configured (recommended) OR API tokens generated

### 6. First Time Publishing
- [ ] Test upload to TestPyPI first (`./scripts/publish.sh testpypi`)
- [ ] Verify package on TestPyPI
- [ ] Install and test from TestPyPI
- [ ] If everything works, publish to PyPI (`./scripts/publish.sh pypi`)

## Publishing Methods

### Method 1: Automated (Recommended)
1. **Setup trusted publishing** on PyPI/TestPyPI
2. **Push to GitHub** and create a release
3. **GitHub Actions** will automatically build and publish

### Method 2: Manual
1. **Build**: `./scripts/build.sh`
2. **Test publish**: `./scripts/publish.sh testpypi`
3. **Production publish**: `./scripts/publish.sh pypi`

### Method 3: Make commands
1. **Build**: `make build`
2. **Test publish**: `make publish-test`
3. **Production publish**: `make publish-prod`

## Post-Publishing

### Verify Your Package
1. Check package page on PyPI: https://pypi.org/project/agentman/
2. Install in a clean environment: `pip install agentman`
3. Test the installed package works correctly
4. Update project documentation with installation instructions

### Announce Your Package
- [ ] Update README with PyPI installation instructions
- [ ] Share on relevant communities/forums
- [ ] Consider adding PyPI badge to README

## Troubleshooting

**Package name already exists**: Choose a different name in `pyproject.toml`
**Version already exists**: Increment version number
**Upload failed**: Check credentials and network connection
**Import errors**: Verify package structure and dependencies
