#!/bin/bash
set -e

TASK_ROOT="$PWD"
if [ -d "/app/src" ]; then
    TASK_ROOT="/app"
elif [ -d "/src" ]; then
    TASK_ROOT="/"
fi

cd "$TASK_ROOT" || exit 1
export TASK_ROOT

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/solve.py"
