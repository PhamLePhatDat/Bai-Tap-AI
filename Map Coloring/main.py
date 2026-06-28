import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from ui.map_coloring_ui import launch_ui


def main():
    launch_ui()


if __name__ == "__main__":
    main()
