"""Claude Code runner adapter. Entry point: psf-agent-claude."""
import sys

from .common import main


def main_cli(argv=None):
    main("claude", argv)


if __name__ == "__main__":
    main_cli(sys.argv[1:])
