#!/bin/zsh

project_dir="${0:A:h}"
cd -- "$project_dir" || exit 1

if [[ -x ".venv/bin/python" ]]; then
    python=".venv/bin/python"
else
    python="$(command -v python3 || true)"
fi

if [[ -z "$python" ]]; then
    echo "Python 3 not found. Install Python 3 or create .venv first."
    read -r "reply?Press Enter to close..."
    exit 1
fi

"$python" wechat.py
exit_code=$?

echo
if (( exit_code == 0 )); then
    echo "Completed."
else
    echo "Exited with status $exit_code."
fi
read -r "reply?Press Enter to close..."
exit "$exit_code"
