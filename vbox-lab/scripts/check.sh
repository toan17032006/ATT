#!/usr/bin/env bash
# Static checks for the lab scripts and cloud-init YAML.
set -uo pipefail
cd "$(dirname "$0")/.."

fail=0
for f in config.sh scripts/*.sh; do
    if bash -n "$f"; then
        echo "OK   $f"
    else
        echo "FAIL $f"
        fail=1
    fi
done

echo ""
if command -v python3 >/dev/null && python3 -c 'import yaml' 2>/dev/null; then
    for f in cloud-init/*/user-data; do
        if python3 -c "import yaml,sys; yaml.safe_load(open(sys.argv[1]))" "$f" 2>/dev/null; then
            echo "YAML OK   $f"
        else
            echo "YAML FAIL $f"
            fail=1
        fi
    done
else
    echo "PyYAML not available in WSL python3; skipping YAML validation"
fi

exit "$fail"
