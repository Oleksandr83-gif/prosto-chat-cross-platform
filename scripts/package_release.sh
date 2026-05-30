#!/usr/bin/env bash
set -euo pipefail

OUTPUT_DIR="${1:-dist}"
RELEASE_NAME="${2:-prosto-chat-release}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$ROOT_DIR/$OUTPUT_DIR"
STAGING_DIR="$DIST_DIR/$RELEASE_NAME"
ARCHIVE="$DIST_DIR/$RELEASE_NAME.tar.gz"

rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"

rsync -a "$ROOT_DIR/" "$STAGING_DIR/" \
  --exclude ".venv" \
  --exclude "dist" \
  --exclude ".git" \
  --exclude "__pycache__" \
  --exclude ".pytest_cache" \
  --exclude "*.pyc" \
  --exclude "*.pyo" \
  --exclude "*.db" \
  --exclude ".env"

rm -f "$ARCHIVE"
tar -C "$DIST_DIR" -czf "$ARCHIVE" "$RELEASE_NAME"
echo "Release archive created: $ARCHIVE"

