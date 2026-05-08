import sys

from app.ui.menus import GuigoApp


def main() -> None:
    try:
        app = GuigoApp()
        app.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Bye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
