#!/usr/bin/env bash
#
# generate_header.sh
# -------------------
# Wrapper script to run the binary security header generator as a
# build step. Intended to be invoked from a Makefile, IDE post-build
# command, or CI pipeline.
#
# Usage:
#   ./generate_header.sh
#
# Assumes generate_header.py and header_config.json are in the same
# directory as this script (adjust SCRIPT_DIR usage below if your
# build layout differs).

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/generate_header.py"
#!/bin/bash

if [ -z "$1" ]; then
    CONFIG_FILE="${SCRIPT_DIR}/config.json"
else
    CONFIG_FILE="$1"
fi
python "${PYTHON_SCRIPT}" --config "${CONFIG_FILE}"
echo "Generated the File"