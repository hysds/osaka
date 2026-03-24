# HySDS Osaka Packaging Migration Summary

## Migration Completed: March 24, 2026

This document summarizes the migration of the `osaka` repository from legacy `setup.py` to modern `pyproject.toml` packaging.

---

## Changes Made

### ✅ Files Created

1. **`pyproject.toml`** - Modern packaging configuration
   - Package name: `hysds-osaka` (PyPI) / `osaka` (import)
   - Version: Dynamic from git tags via `hatch-vcs`
   - Dependencies: 8 third-party packages
   - Moved test dependencies: `moto>=4.1.0`, `mock>=5.1.0` to test extra

2. **`.github/workflows/publish.yml`** - PyPI publishing automation
   - Triggered on git tags (`v*`)
   - Uses PyPI Trusted Publishers (OIDC)

3. **`test/test_packaging.py`** - Packaging validation tests
   - Verifies version starts with 7.x
   - Validates no `future` dependency
   - Tests moto/mock in test extra (not main dependencies)
   - Tests console script defined

### ✅ Files Modified

1. **`osaka/__init__.py`**
   - Removed `__future__` imports (lines 1-4)
   - Changed from hardcoded version to `version("hysds-osaka")`
   - Fixed typo: "Arcitecture" → "Architecture"

2. **`setup.py`**
   - Replaced with minimal shim for backward compatibility
   - Delegates all configuration to `pyproject.toml`
   - Will be removed in v7.1.0+

---

## Key Dependency Changes

### Fixed Issues

| Issue | Before | After |
|-------|--------|-------|
| future dependency | `future>=1.0.0` | Removed |
| moto in main deps | `moto>=4.1.0` | Moved to test extra |
| mock in main deps | `mock>=5.1.0` | Moved to test extra |
| Python requirement | `>=3.10` | `>=3.12` |

### Dependencies Preserved Exactly

All 8 core dependencies maintained with exact pins from original `setup.py`:
- `requests>=2.31.0`
- `easywebdav>=1.2.0`
- `azure-storage-blob>=12.18.0`
- `azure-identity>=1.15.0`
- `awscli>=1.29.0`
- `boto3>=1.32.0`
- `google-cloud-storage>=2.13.0`
- `backoff>=2.2.1`

---

## Build Verification

```bash
$ python -m build
Successfully built hysds_osaka-1.3.1.post1.dev0+g7bb4899d6.d20260324.tar.gz
Successfully built hysds_osaka-1.3.1.post1.dev0+g7bb4899d6.d20260324-py3-none-any.whl
```

---

## ⚠️ Known Issue: Future Imports in 23 Files

The `osaka/__init__.py` has been updated to remove `__future__` imports, but **22 other Python files** still contain:

```python
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
```

### Files Affected
- `/osaka/*.py` (7 files: __main__, base, cooperator, lock, main, transfer, utils)
- `/osaka/storage/*.py` (7 files: az, example, file, ftp, gs, http, s3, sftp, webdav)
- `/osaka/tests/*.py` (8 files)

### Impact
- Package builds and installs successfully
- `future` is no longer a dependency
- These `__future__` imports are harmless on Python 3.12 (they're no-ops)
- Unlike `from future import`, these are standard library imports

### Recommended Action
These `__future__` imports can be safely removed in a follow-up cleanup task, but they don't cause runtime errors since they're built into Python 3.

---

## Next Steps

### Before Publishing to PyPI

1. **Tag version 7.0.0**
   ```bash
   git tag -a v7.0.0 -m "Release 7.0.0 - Modern packaging migration"
   git push origin v7.0.0
   ```

2. **Configure PyPI Trusted Publisher**
   - Go to https://pypi.org/manage/account/publishing/
   - Add GitHub Actions publisher for `hysds/osaka` repo
   - Workflow: `publish.yml`
   - Environment: `pypi`

### Installation Methods

#### Development (Local)
```bash
# Editable install
pip install -e .

# With test dependencies
pip install -e ".[test]"
```

#### Development (From Git Branch)
```bash
# Install from feature branch
pip install "git+https://github.com/hysds/osaka.git@feature-branch"
```

#### Production (After PyPI Publishing)
```bash
# Install from PyPI
pip install hysds-osaka

# Or as dependency of hysds-core
pip install hysds-core  # Includes hysds-osaka~=7.0
```

---

## Backward Compatibility

### Import Names (Unchanged)
```python
# All existing imports continue to work
import osaka
from osaka import main
from osaka.storage import S3Storage
```

### Package Name Change
- **PyPI package**: `osaka` → `hysds-osaka`
- **Import name**: `osaka` (unchanged)

### Console Script (Unchanged)
```bash
osaka --help  # Still works
```

### setup.py Shim
A minimal `setup.py` is included for backward compatibility:
```python
from setuptools import setup
setup()  # Delegates to pyproject.toml
```

This ensures existing deployment scripts that expect `setup.py` continue to work.

---

## Migration Checklist

- [x] Create `pyproject.toml` with all dependencies
- [x] Remove `future` from dependencies
- [x] Move moto and mock to test extra
- [x] Update Python requirement to >=3.12
- [x] Preserve all other dependency pins exactly
- [x] Update `osaka/__init__.py` to remove __future__ imports
- [x] Add `__version__` using `importlib.metadata`
- [x] Add GitHub Actions workflow for PyPI publishing
- [x] Add packaging validation tests
- [x] Keep minimal `setup.py` shim for backward compatibility
- [x] Verify `python -m build` succeeds
- [x] Verify console script preserved
- [ ] Remove __future__ imports from remaining 22 files (optional cleanup)
- [ ] Tag v7.0.0 release
- [ ] Configure PyPI Trusted Publisher
- [ ] Publish to PyPI
- [ ] Update documentation

---

## Contact

For questions about this migration, contact the HySDS team at hysds-help@jpl.nasa.gov
