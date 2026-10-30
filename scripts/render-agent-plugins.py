#!/usr/bin/env python3
"""Synchronize the canonical plugin manifests with the release version."""

import argparse

from agent_release import sync_manifests

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    sync_manifests(check=args.check)
