"""opencode + DeepSeek runner adapter. Entry point: psf-agent-opencode."""
import sys

from .common import main


def main_cli(argv=None):
    main("opencode", argv)


if __name__ == "__main__":
    main_cli(sys.argv[1:])
