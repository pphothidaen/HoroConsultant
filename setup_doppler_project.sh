#!/usr/bin/env bash
# Root wrapper for scripts/setup_doppler_project.sh
exec bash "$(dirname "$0")/scripts/setup_doppler_project.sh" "$@"
