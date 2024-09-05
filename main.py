import sys
from PyQt5 import QtWidgets, QtCore, QtWebEngineWidgets


class PyBrowse(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyBrowse - Advanced Web Browser")
        self.setGeometry(100, 100, 1024, 768)
        self.browser = QtWebEngineWidgets.QWebEngineView()
        self.browser.setUrl(QtCore.QUrl("https://www.example.com"))
        self.setCentralWidget(self.browser)
        self.create_navigation_bar()
        self.create_menu_bar()

    def create_navigation_bar(self):
        """Create the navigation bar with URL entry, back, reload, and go buttons."""
        navigation_bar = QtWidgets.QToolBar("Navigation")
        self.addToolBar(navigation_bar)
        back_button = QtWidgets.QAction("Back", self)
        back_button.triggered.connect(self.browser.back)
        navigation_bar.addAction(back_button)
        reload_button = QtWidgets.QAction("Reload", self)
        reload_button.triggered.connect(self.browser.reload)
        navigation_bar.addAction(reload_button)
        self.url_bar = QtWidgets.QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        navigation_bar.addWidget(self.url_bar)
        go_button = QtWidgets.QAction("Go", self)
        go_button.triggered.connect(self.navigate_to_url)
        navigation_bar.addAction(go_button)
        self.browser.urlChanged.connect(self.update_url_bar)

    def navigate_to_url(self):
        """Load the URL entered in the URL bar."""
        url = self.url_bar.text()
        if not url.startswith("http"):
            url = "http://" + url
        self.browser.setUrl(QtCore.QUrl(url))

    def update_url_bar(self, q):
        """Update the URL bar when the user navigates to a different page."""
        self.url_bar.setText(q.toString())

    def create_menu_bar(self):
        """Create the menu bar with a Help section and About dialog."""
        menu_bar = self.menuBar()
        help_menu = menu_bar.addMenu("Help")
        about_action = QtWidgets.QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def show_about_dialog(self):
        """Show an About dialog with browser information."""
        QtWidgets.QMessageBox.information(self, "About PyBrowse", "PyBrowse - Version 0.0.2")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = PyBrowse()
    window.show()
    sys.exit(app.exec_())
