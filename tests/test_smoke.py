# tests/test_smoke.py
import subprocess
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def run_example(script: str, *args: str):
    """Run an example script with optional args and assert it exits cleanly."""
    script_path = EXAMPLES / script
    cmd = [sys.executable, str(script_path), *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    assert result.returncode == 0, f"{script} failed"


def test_language_catalog():
    run_example("test_language_catalog.py")


def test_csv_reporter_all_customers(tmp_path):
    out = tmp_path / "all_customers.csv"
    run_example("test_csv_reporter.py", "ALL_CUSTOMERS", "NDL_STRICT", str(out))
    assert out.exists()


def test_csv_reporter_by_city(tmp_path):
    out = tmp_path / "cologne.csv"
    run_example("test_csv_reporter.py", "CUSTOMERS_BY_CITY", "NDL_STRICT", str(out), "city=Cologne")
    assert out.exists()