"""Codex CLI runner adapter. Entry point: psf-agent-codex."""
import sys

from .common import main


def main_cli(argv=None):
    main("codex", argv)


if __name__ == "__main__":
    main_cli(sys.argv[1:])
