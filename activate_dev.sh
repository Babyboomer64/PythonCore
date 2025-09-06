#!/bin/bash
# Activate dev environment for PythonCore

# Projekt-Root herausfinden
ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Falls kein venv existiert: anlegen
if [ ! -d "$ROOT/.venv" ]; then
  echo "Creating virtual environment in $ROOT/.venv ..."
  python3 -m venv "$ROOT/.venv"
fi

# venv aktivieren
source "$ROOT/.venv/bin/activate"

# PYTHONPATH setzen (src-Ordner)
export PYTHONPATH="$ROOT/src"

echo "✅ Development environment activated"
echo "   Python: $(python --version)"
echo "   PYTHONPATH: $PYTHONPATH"
echo "   Use 'deactivate' to exit the venv."