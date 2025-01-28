#!/bin/bash

# Platform checks
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Error: Linux not supported for Visio integration"
    exit 1
fi

# Component verification
declare -A DEPENDENCIES=(
    ["python"]="3.8" 
    ["node"]="14"
    ["npm"]="6"
    ["docker"]="20.10"
)

check_dependency() {
    command -v $1 >/dev/null 2>&1 || {
        echo >&2 "Error: $1 required"
        exit 1
    }
    
    if [ $1 == "python" ]; then
        version=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    elif [ $1 == "node" ]; then
        version=$(node -v | cut -d'v' -f2)
    else
        version=$($1 --version | head -n1 | grep -oE '[0-9]+\.[0-9]+')
    fi
    
    if (( $(echo "$version < ${DEPENDENCIES[$1]}" | bc -l) )); then
        echo >&2 "Error: $1 v$version < required v${DEPENDENCIES[$1]}"
        exit 1
    fi
}

# Verify core dependencies
for dep in python node npm docker; do
    check_dependency $dep
done

# Frontend dependencies
echo "Validating frontend packages..."
cd src/frontend
npm list --depth=0 | awk -F@ '{print $1}' | grep -qE 'react@18|next@14' || {
    echo "Frontend dependencies mismatch"
    exit 1
}

# Python requirements
echo "Validating Python packages..."
pip freeze | grep -qE 'win32com|python-dotenv' || {
    echo "Python requirements not met"
    exit 1
} 