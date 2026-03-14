#!/bin/zsh

cd "$(dirname "$0")" || exit 1

python3 start.py
status=$?

if [ "$status" -ne 0 ]; then
  echo
  echo "Startup failed. Press any key to close..."
  read -k 1
fi

exit "$status"
