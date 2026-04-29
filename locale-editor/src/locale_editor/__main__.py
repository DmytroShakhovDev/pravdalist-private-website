"""Entry point: python -m locale_editor"""
import sys

from PyQt6.QtWidgets import QApplication

from locale_editor.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Locale Editor")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
