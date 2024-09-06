import sys
import json
import os
from PyQt5 import QtWidgets, QtCore, QtWebEngineWidgets


class PyBrowse(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.bookmarks_file = "bookmarks.json"
        self.bookmarks = []
        self.load_bookmarks()
        self.setWindowTitle("PyBrowse")
        self.setGeometry(100, 100, 1024, 768)
        self.browser = QtWebEngineWidgets.QWebEngineView()
        self.browser.setUrl(QtCore.QUrl("https://www.example.com"))
        self.setCentralWidget(self.browser)
        self.history = []
        self.create_navigation_bar()
        self.create_menu_bar()
        self.browser.urlChanged.connect(self.add_to_history)

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
        self.url_bar.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.url_bar.customContextMenuRequested.connect(self.show_context_menu)
        go_button = QtWidgets.QAction("Go", self)
        go_button.triggered.connect(self.navigate_to_url)
        navigation_bar.addAction(go_button)
        self.browser.urlChanged.connect(self.update_url_bar)

    def show_context_menu(self, position):
        """Display the context menu with Copy, Cut, and Paste actions."""
        context_menu = QtWidgets.QMenu()
        copy_action = context_menu.addAction("Copy")
        cut_action = context_menu.addAction("Cut")
        paste_action = context_menu.addAction("Paste")
        select_all_action = context_menu.addAction("Select All")
        undo_action = context_menu.addAction("Undo")
        redo_action = context_menu.addAction("Redo")
        clear_action = context_menu.addAction("Clear")
        copy_action.triggered.connect(self.url_bar.copy)
        cut_action.triggered.connect(self.url_bar.cut)
        paste_action.triggered.connect(self.url_bar.paste)
        select_all_action.triggered.connect(self.url_bar.selectAll)
        undo_action.triggered.connect(self.url_bar.undo)
        redo_action.triggered.connect(self.url_bar.redo)
        clear_action.triggered.connect(self.url_bar.clear)
        context_menu.exec_(self.url_bar.mapToGlobal(position))

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
        self.history_menu = menu_bar.addMenu("History")
        self.bookmarks_menu = menu_bar.addMenu("Bookmarks")
        add_bookmark_action = QtWidgets.QAction("Add Bookmark", self)
        add_bookmark_action.triggered.connect(self.add_bookmark)
        self.bookmarks_menu.addAction(add_bookmark_action)

    def show_about_dialog(self):
        """Show an About dialog with browser information."""
        QtWidgets.QMessageBox.information(self, "About PyBrowse", "PyBrowse - Version 0.0.3")
    
    def add_to_history(self, url):
        """Add the current URL to the history and update the History menu."""
        url_str = url.toString()
        if url_str not in self.history:
            self.history.append(url_str)
            history_action = QtWidgets.QAction(url_str, self)
            history_action.triggered.connect(lambda checked, url=url_str: self.browser.setUrl(QtCore.QUrl(url)))
            self.history_menu.addAction(history_action)
    
    def add_bookmark(self):
        """Add the current URL to the bookmarks and update the Bookmarks menu."""
        current_url = self.browser.url().toString()
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
            bookmark_action.triggered.connect(lambda checked, url=bookmark: self.browser.setUrl(QtCore.QUrl(url)))
            self.bookmarks_menu.addAction(bookmark_action)
    
    def save_bookmarks(self):
        """Save the bookmarks to a JSON file."""
        with open(self.bookmarks_file, 'w') as f:
            json.dump(self.bookmarks, f)
    
    def load_bookmarks(self):
        """Load bookmarks from a JSON file if it exists, or create it if not."""
        if os.path.exists(self.bookmarks_file):
            with open(self.bookmarks_file, 'r') as f:
                self.bookmarks = json.load(f)
        else:
            self.bookmarks = []
            self.save_bookmarks()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = PyBrowse()
    window.show()
    sys.exit(app.exec_())
