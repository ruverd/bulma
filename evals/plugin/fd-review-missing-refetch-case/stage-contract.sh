#!/usr/bin/env bash
set -euo pipefail

skill="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../skills/bulma-feature-delivery" && pwd)"
cp "$skill/nodes/reviewer.md" "$skill/LESSONS.md" .
