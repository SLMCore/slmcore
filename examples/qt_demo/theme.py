"""Application-level styling for the standalone Qt demo.

The reusable :mod:`slmcore.qt` widgets deliberately do not own an application
style.  The demo applies one here so the same widgets can be viewed in a
compact dark host similar to their ImSwitch presentation while remaining
fully host-themeable.
"""

from __future__ import annotations

from qtpy import QtGui, QtWidgets


_DEMO_STYLESHEET = """
QWidget {
    color: #e8e8e8;
    background-color: #242629;
}

QMainWindow,
QDialog {
    background-color: #242629;
}

QGroupBox {
    border: 1px solid #4a4d51;
    border-radius: 3px;
    margin-top: 8px;
    padding-top: 5px;
    background-color: #292b2f;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 7px;
    padding: 0 3px;
    color: #ededed;
}

QPushButton,
QToolButton {
    background-color: #36393d;
    border: 1px solid #55595e;
    border-radius: 2px;
    padding: 3px 7px;
    min-height: 16px;
}

QPushButton:hover,
QToolButton:hover {
    background-color: #41454a;
    border-color: #6a6f75;
}

QPushButton:pressed,
QToolButton:pressed {
    background-color: #2f3236;
}

QPushButton:checked,
QToolButton:checked {
    background-color: #365d7d;
    border-color: #4d86b4;
}

QPushButton:disabled,
QToolButton:disabled {
    color: #777b80;
    background-color: #2b2d30;
    border-color: #3c3f43;
}

QLineEdit,
QSpinBox,
QDoubleSpinBox,
QComboBox,
QPlainTextEdit,
QTextEdit,
QListView,
QListWidget,
QTreeView,
QTableView {
    background-color: #303236;
    border: 1px solid #50545a;
    border-radius: 2px;
    padding: 2px 4px;
    selection-background-color: #3f6f96;
    selection-color: #ffffff;
}

QLineEdit:focus,
QSpinBox:focus,
QDoubleSpinBox:focus,
QComboBox:focus,
QPlainTextEdit:focus,
QTextEdit:focus {
    border-color: #5b8db7;
}

QComboBox::drop-down {
    border: none;
    width: 18px;
}

QComboBox QAbstractItemView {
    background-color: #303236;
    border: 1px solid #50545a;
    selection-background-color: #3f6f96;
}

QTabWidget::pane {
    border: 1px solid #45484d;
    background-color: #242629;
    top: -1px;
}

QTabBar::tab {
    background-color: #2d3034;
    border: 1px solid #45484d;
    border-bottom: none;
    padding: 5px 10px;
    margin-right: 1px;
}

QTabBar::tab:selected {
    background-color: #3a3d42;
    color: #ffffff;
}

QTabBar::tab:hover:!selected {
    background-color: #34373b;
}

QMenu {
    background-color: #303236;
    border: 1px solid #50545a;
}

QMenu::item {
    padding: 4px 24px 4px 8px;
}

QMenu::item:selected {
    background-color: #3f6f96;
}

QMenu::separator {
    height: 1px;
    background-color: #4a4d51;
    margin: 4px 6px;
}

QScrollArea {
    border: none;
}

QScrollBar:vertical {
    background: #282a2d;
    width: 11px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #55595e;
    min-height: 24px;
    border-radius: 4px;
    margin: 1px 2px;
}

QScrollBar::handle:vertical:hover {
    background: #656a70;
}

QScrollBar:horizontal {
    background: #282a2d;
    height: 11px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #55595e;
    min-width: 24px;
    border-radius: 4px;
    margin: 2px 1px;
}

QScrollBar::handle:horizontal:hover {
    background: #656a70;
}

QScrollBar::add-line,
QScrollBar::sub-line,
QScrollBar::add-page,
QScrollBar::sub-page {
    background: none;
    border: none;
}

QSplitter::handle {
    background-color: #414449;
}

QSplitter::handle:horizontal {
    width: 3px;
}

QSplitter::handle:vertical {
    height: 3px;
}

QToolTip {
    color: #f0f0f0;
    background-color: #35383c;
    border: 1px solid #5a5e63;
    padding: 3px;
}

QStatusBar {
    background-color: #2b2d30;
    border-top: 1px solid #414449;
}
"""


def apply_demo_theme(app: QtWidgets.QApplication) -> None:
    """Apply the standalone demo's compact dark host theme."""
    app.setStyle("Fusion")

    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor(36, 38, 41))
    palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(232, 232, 232))
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor(42, 44, 47))
    palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(48, 50, 54))
    palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(53, 56, 60))
    palette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor(240, 240, 240))
    palette.setColor(QtGui.QPalette.Text, QtGui.QColor(232, 232, 232))
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor(54, 57, 61))
    palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(232, 232, 232))
    palette.setColor(QtGui.QPalette.BrightText, QtGui.QColor(255, 255, 255))
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(63, 111, 150))
    palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(255, 255, 255))
    palette.setColor(QtGui.QPalette.Link, QtGui.QColor(91, 141, 183))

    palette.setColor(
        QtGui.QPalette.Disabled,
        QtGui.QPalette.WindowText,
        QtGui.QColor(120, 124, 128),
    )
    palette.setColor(
        QtGui.QPalette.Disabled,
        QtGui.QPalette.Text,
        QtGui.QColor(120, 124, 128),
    )
    palette.setColor(
        QtGui.QPalette.Disabled,
        QtGui.QPalette.ButtonText,
        QtGui.QColor(120, 124, 128),
    )

    app.setPalette(palette)
    app.setStyleSheet(_DEMO_STYLESHEET)
