import sys

from app.ui.tui.app import GuigoTUI


def main() -> None:
    try:
        GuigoTUI().run()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
