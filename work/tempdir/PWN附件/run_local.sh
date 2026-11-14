#!/bin/sh
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec "$base/ld-linux-x86-64.so.2" --library-path "$base" "$base/tide_qjs"
