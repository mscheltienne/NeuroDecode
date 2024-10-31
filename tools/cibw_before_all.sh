#!/bin/bash

# Build and install (locally) liblsl

set -eo pipefail
ROOT=$(dirname $(dirname $(realpath "$0")))
cd $ROOT
echo "Using project root \"${ROOT}\" on RUNNER_OS=\"${RUNNER_OS}\""

if [[ "$RUNNER_OS" == 'Linux' ]]; then
    echo "Compiling on Linux"
elif [[ "$RUNNER_OS" == 'macOS' ]]; then
    echo "Compiling on macOS"
    # On arm64, we need to set the install path to /opt/local/lib
    if [[ "$(uname -m)" == "arm64" ]]; then
        export CMAKE_INSTALL_PREFIX=/opt/local
    fi
elif [[ "$RUNNER_OS" == 'Windows' ]]; then
    echo "Compiling on Windows"
    export CMAKE_INSTALL_PREFIX="C:/Program Files/liblsl"
else
    echo "Unknown RUNNER_OS: ${RUNNER_OS}"
    exit 1
fi

cd liblsl
# https://labstreaminglayer.readthedocs.io/dev/lib_dev.html#configuring-the-liblsl-project
set -x
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --target install --target package --config release
set +x
echo "Done building liblsl!"
cd ..
