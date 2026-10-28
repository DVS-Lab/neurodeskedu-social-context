#!/usr/bin/env bash
# Create an isolated environment and open the public-data notebook in JupyterLab.
set -euo pipefail
tutorial_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$tutorial_root"
tutorial_python="${TUTORIAL_PYTHON:-}"
if [[ -z "$tutorial_python" ]]; then
  for candidate in python3 "$HOME/anaconda3/bin/python3" "$HOME/miniforge3/bin/python3" \
      "$HOME/miniconda3/bin/python3" python3.13 python3.12 python3.11 python3.10; do
    if command -v "$candidate" >/dev/null 2>&1 && \
        "$candidate" -c 'import sys; sys.exit(not ((3, 10) <= sys.version_info[:2] <= (3, 13)))' 2>/dev/null; then
      tutorial_python="$(command -v "$candidate")"
      break
    fi
  done
fi
if [[ -z "$tutorial_python" ]]; then
  printf '%s\n' 'Python 3.10–3.13 is required. Set TUTORIAL_PYTHON to a compatible interpreter.' >&2
  exit 1
fi
"$tutorial_python" -c 'import sys; assert (3, 10) <= sys.version_info[:2] <= (3, 13), "Use Python 3.10–3.13 for this pinned environment."'
if [[ "${1:-}" == '--check' ]]; then
  printf 'Selected Python: %s\n' "$tutorial_python"
  "$tutorial_python" --version
  exit 0
fi
"$tutorial_python" -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
if [[ "${1:-}" == '--setup-play' ]]; then
  .venv/bin/python -m ipykernel install --user --name social-context --display-name 'Social context (pinned)'
  printf '%s\n' 'Open Cross_task_decoding.ipynb in the existing JupyterLab and select Social context (pinned).'
  exit 0
fi
export PATH="$tutorial_root/.venv/bin:$PATH"
exec .venv/bin/python -m jupyterlab "$tutorial_root/Cross_task_decoding.ipynb"
