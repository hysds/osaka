"""Test packaging configuration and metadata."""
import sys
from importlib.metadata import version, requires

import pytest


def test_version_starts_with_7():
    """Verify package version starts with 7."""
    v = version("hysds-osaka")
    assert v.startswith("7."), f"Expected version 7.x, got {v}"


def test_future_not_a_dependency():
    """Verify 'future' package is not a dependency."""
    deps = requires("hysds-osaka")
    assert deps is not None
    
    for dep in deps:
        dep_name = dep.split()[0].split(";")[0].split(">=")[0].split("~=")[0].split("<")[0]
        assert dep_name != "future", "'future' should not be a dependency on Python 3.12+"


def test_moto_mock_in_test_extra():
    """Verify moto and mock are in test extra, not main dependencies."""
    deps = requires("hysds-osaka")
    assert deps is not None
    
    main_dep_names = {dep.split()[0].split(";")[0].split(">=")[0].split("~=")[0].split("<")[0]
                      for dep in deps if "extra ==" not in dep}
    
    assert "moto" not in main_dep_names, "moto should be in test extra, not main dependencies"
    assert "mock" not in main_dep_names, "mock should be in test extra, not main dependencies"


def test_core_modules_importable():
    """Verify core osaka modules can be imported."""
    import osaka
    assert hasattr(osaka, "__version__")
    assert hasattr(osaka, "__url__")
    assert hasattr(osaka, "__description__")


def test_python_version_requirement():
    """Verify running on Python 3.12+."""
    assert sys.version_info >= (3, 12), "Requires Python 3.12+"


def test_package_name_is_hysds_osaka():
    """Verify package is published as hysds-osaka."""
    v = version("hysds-osaka")
    assert v is not None, "Package 'hysds-osaka' not found"


def test_import_name_is_osaka():
    """Verify import name remains 'osaka' (not hysds_osaka)."""
    import osaka
    assert osaka.__name__ == "osaka"


def test_console_script_defined():
    """Verify osaka console script is defined."""
    from importlib.metadata import entry_points
    
    scripts = entry_points()
    if hasattr(scripts, 'select'):
        # Python 3.10+
        console_scripts = scripts.select(group='console_scripts')
    else:
        # Python 3.9
        console_scripts = scripts.get('console_scripts', [])
    
    script_names = [ep.name for ep in console_scripts]
    assert "osaka" in script_names, "osaka console script not found"
