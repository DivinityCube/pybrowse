import sys
import json
import os
from PyQt5 import QtWidgets, QtCore, QtWebEngineWidgets


class BrowserTab(QtWebEngineWidgets.QWebEngineView):
    """A single browser tab, which extends QWebEngineView."""
    def __init__(self, url="https://www.example.com"):
        super().__init__()
        self.setUrl(QtCore.QUrl(url))


class PyBrowse(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyBrowse")
        self.setGeometry(100, 100, 1024, 768)
        self.bookmarks_file = "bookmarks.json"
        self.bookmarks = []
        self.load_bookmarks()
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_url_bar)
        self.tabs.setStyleSheet("QTabBar::tab { width: 150px; }")
        self.setCentralWidget(self.tabs)
        self.create_navigation_bar()
        self.create_menu_bar()
        self.add_new_tab("https://www.example.com")

    def create_navigation_bar(self):
        """Create the navigation bar with URL entry, back, reload, go buttons, and new tab button."""
        navigation_bar = QtWidgets.QToolBar("Navigation")
        self.addToolBar(navigation_bar)
        back_button = QtWidgets.QAction("Back", self)
        back_button.triggered.connect(self.go_back)
        navigation_bar.addAction(back_button)
        reload_button = QtWidgets.QAction("Reload", self)
        reload_button.triggered.connect(self.reload_page)
        navigation_bar.addAction(reload_button)
        self.url_bar = QtWidgets.QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        navigation_bar.addWidget(self.url_bar)
        go_button = QtWidgets.QAction("Go", self)
        go_button.triggered.connect(self.navigate_to_url)
        navigation_bar.addAction(go_button)
        new_tab_button = QtWidgets.QAction("New Tab", self)
        new_tab_button.triggered.connect(lambda: self.add_new_tab())
        navigation_bar.addAction(new_tab_button)

    def create_menu_bar(self):
        """Create the menu bar with Help and Bookmarks sections."""
        menu_bar = self.menuBar()
        help_menu = menu_bar.addMenu("Help")
        about_action = QtWidgets.QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        self.bookmarks_menu = menu_bar.addMenu("Bookmarks")
        add_bookmark_action = QtWidgets.QAction("Add Bookmark", self)
        add_bookmark_action.triggered.connect(self.add_bookmark)
        self.bookmarks_menu.addAction(add_bookmark_action)
        self.bookmarks_menu.addSeparator()
        self.load_bookmarks_menu()

    def show_about_dialog(self):
        """Show an About dialog with browser information."""
        QtWidgets.QMessageBox.information(self, "About PyBrowse", "PyBrowse - Version 0.0.6")

    def add_new_tab(self, url="https://www.example.com"):
        """Add a new tab with the given URL."""
        new_tab = BrowserTab(url)
        i = self.tabs.addTab(new_tab, "New Tab")
        self.tabs.setCurrentIndex(i)
        new_tab.urlChanged.connect(self.update_url_bar)

    def close_tab(self, index):
        """Close the tab at the given index."""
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)

    def navigate_to_url(self):
        """Load the URL entered in the URL bar into the current tab."""
        url = self.url_bar.text()
        if not url.startswith("http"):
            url = "http://" + url
        self.tabs.currentWidget().setUrl(QtCore.QUrl(url))

    def update_url_bar(self):
        """Update the URL bar when the user navigates to a different page."""
        if self.tabs.count() > 0:
            current_tab = self.tabs.currentWidget()
            if current_tab:
                self.url_bar.setText(current_tab.url().toString())

    def go_back(self):
        """Go back in the history of the current tab."""
        if self.tabs.count() > 0:
            self.tabs.currentWidget().back()

    def reload_page(self):
        """Reload the current page in the active tab."""
        if self.tabs.count() > 0:
            self.tabs.currentWidget().reload()

    def add_bookmark(self):
        """Add the current URL to the bookmarks and update the Bookmarks menu."""
        current_url = self.tabs.currentWidget().url().toString()
        if current_url not in self.bookmarks:
            self.bookmarks.append(current_url)
            self.save_bookmarks()
            self.load_bookmarks_menu()

    def load_bookmarks_menu(self):
        """Load the saved bookmarks into the Bookmarks menu."""
        actions = self.bookmarks_menu.actions()[2:]
        for action in actions:
            self.bookmarks_menu.removeAction(action)
        for bookmark in self.bookmarks:
            bookmark_action = QtWidgets.QAction(bookmark, self)
            bookmark_action.triggered.connect(lambda checked, url=bookmark: self.tabs.currentWidget().setUrl(QtCore.QUrl(url)))
            self.bookmarks_menu.addAction(bookmark_action)

    def save_bookmarks(self):
        """Save the bookmarks to a JSON file."""
        with open(self.bookmarks_file, 'w') as f:
            json.dump(self.bookmarks, f)

    def load_bookmarks(self):
        """Load bookmarks from a JSON file if it exists."""
        if os.path.exists(self.bookmarks_file):
            with open(self.bookmarks_file, 'r') as f:
                self.bookmarks = json.load(f)
        else:
            self.bookmarks = []


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = PyBrowse()
    window.show()
    sys.exit(app.exec_())