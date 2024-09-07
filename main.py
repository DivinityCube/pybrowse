import sys
import json
import os
from PyQt5 import QtWidgets, QtCore, QtWebEngineWidgets, QtGui
from PyQt5.QtWebEngineWidgets import QWebEngineProfile
from PyQt5.QtCore import QUrl

# TODO: This new tab overhaul is very sloppy. I don't feel like this code is super polished and there are probably some gaping holes I'm too tired to fix, or even spot. Maybe in some future version I'll go over this code again
class ScrollableTabBar(QtWidgets.QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDrawBase(False)
        self.setElideMode(QtCore.Qt.ElideRight)
        self.setUsesScrollButtons(True)
        self.setMovable(True)
        self.setExpanding(False)

    def tabSizeHint(self, index):
        size = super().tabSizeHint(index)
        if self.count() > 0:
            available_width = self.width()
            total_width = sum(self.tabRect(i).width() for i in range(self.count()))
            if total_width > available_width:
                return size
            else:
                extra_width = (available_width - total_width) // self.count()
                return QtCore.QSize(size.width() + extra_width, size.height())
        return size
    
    def minimumTabSizeHint(self, index):
        return QtCore.QSize(50, super().minimumTabSizeHint(index).height())

class TabWidget(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabBar(ScrollableTabBar(self))
        self.setMovable(True)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)
        self.overflow_menu = QtWidgets.QMenu(self)

    def close_tab(self, index):
        if self.count() > 1:
            self.removeTab(index)

    def show_overflow_menu(self, position):
        self.overflow_menu.clear()
        for i in range(self.count()):
            action = self.overflow_menu.addAction(self.tabText(i))
            action.setData(i)
        action = self.overflow_menu.exec_(self.tab_bar().mapToGlobal(position))
        if action:
            self.setCurrentIndex(action.data())

class CustomWebEnginePage(QtWebEngineWidgets.QWebEnginePage):
    console_message = QtCore.pyqtSignal(str)

    def javaScriptConsoleMessage(self, level, message, line, source):
        self.console_message.emit(f"Console: {message} (line: {line}, source: {source})")

class DebugConsole(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.console_output = QtWidgets.QTextEdit(self)
        self.console_output.setReadOnly(True)
        self.layout.addWidget(self.console_output)
        input_layout = QtWidgets.QHBoxLayout()
        self.input_line = QtWidgets.QLineEdit(self)
        self.execute_button = QtWidgets.QPushButton("Execute", self)
        input_layout.addWidget(self.input_line)
        input_layout.addWidget(self.execute_button)
        self.layout.addLayout(input_layout)
        self.input_line.returnPressed.connect(self.execute_command)
        self.execute_button.clicked.connect(self.execute_command)
        actions_layout = QtWidgets.QHBoxLayout()
        self.clear_button = QtWidgets.QPushButton("Clear Console", self)
        self.get_dom_button = QtWidgets.QPushButton("Get DOM", self)
        self.get_cookies_button = QtWidgets.QPushButton("Get Cookies", self)
        actions_layout.addWidget(self.clear_button)
        actions_layout.addWidget(self.get_dom_button)
        actions_layout.addWidget(self.get_cookies_button)
        self.layout.addLayout(actions_layout)
        self.clear_button.clicked.connect(self.clear_console)
        self.get_dom_button.clicked.connect(lambda: self.execute_command("document.documentElement.outerHTML"))
        self.get_cookies_button.clicked.connect(lambda: self.execute_command("document.cookie"))
        
    def log(self, message):
        self.console_output.append(message)
        
    def execute_command(self, command=None):
        if command is None:
            command = self.input_line.text()
            self.input_line.clear()
        self.log(f"> {command}")
        
        main_window = self.get_main_window()
        if main_window and hasattr(main_window, 'tabs'):
            current_tab = main_window.tabs.currentWidget()
            if isinstance(current_tab, BrowserTab):
                current_tab.page().runJavaScript(command, self.handle_result)
        else:
            self.log("Error: Unable to find the current browser tab.")
        
    def handle_result(self, result):
        if result is not None:
            self.log(str(result))
        
    def clear_console(self):
        self.console_output.clear()
        
    def get_main_window(self):
        parent = self.parent()
        while parent is not None:
            if isinstance(parent, PyBrowse):
                return parent
            parent = parent.parent()
        return None


class BrowserTab(QtWebEngineWidgets.QWebEngineView):
    """A single browser tab, which extends QWebEngineView."""
    def __init__(self, url="https://www.google.com", parent=None):
        super().__init__(parent)
        self.custom_page = CustomWebEnginePage(self)
        self.setPage(self.custom_page)
        self.setUrl(QtCore.QUrl(url))
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.custom_page.console_message.connect(self.handle_console_message)
        self.source_window = None
    
    def build_context_menu(self, menu, position, link_url):
        if link_url:
            menu.addAction("Open Link in New Tab", lambda: self.open_link_in_new_tab(QtCore.QUrl(link_url)))
            menu.addAction("Copy Link Address", lambda: QtWidgets.QApplication.clipboard().setText(link_url))
        menu.addSeparator()
        menu.addAction("Back", self.back)
        menu.addAction("Forward", self.forward)
        menu.addAction("Reload", self.reload)
        menu.addSeparator()
        menu.addAction("View Page Source", self.view_page_source)
        menu.addAction("Save Page", self.save_page)
        menu.exec_(self.mapToGlobal(position))
    
    def show_context_menu(self, position):
        menu = QtWidgets.QMenu(self)
        js_code = """
            var element = document.elementFromPoint(%d, %d);
            var link = element ? element.closest('a') : null;
            link ? link.href : null;
            """ % (position.x(), position.y())
        self.page().runJavaScript(js_code, lambda link_url: self.build_context_menu(menu, position, link_url))
    
    def open_link_in_new_tab(self, url):
        main_window = self.window()
        if hasattr(main_window, 'add_new_tab'):
            main_window.add_new_tab(url.toString())
    
    def view_page_source(self):
        self.page().toHtml(self.show_source_window)
    
    def show_source_window(self, html):
        if self.source_window is None:
            self.source_window = QtWidgets.QTextEdit(None)
            self.source_window.setWindowTitle("Page Source")
            self.source_window.setReadOnly(True)
            self.source_window.resize(800, 600)
            font = QtGui.QFont("Courier", 10)
            self.source_window.setFont(font)
            self.source_window.closeEvent = lambda event: self.reset_source_window(event)
        
        self.source_window.setPlainText(html)
        self.source_window.show()
        self.source_window.raise_()
    
    def reset_source_window(self, event):
        self.source_window = None
        event.accept()
    
    def save_page(self):
        dialog = QtWidgets.QFileDialog(self)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        dialog.setNameFilter("Web Page, Complete (*.html)")
        if dialog.exec_() == QtWidgets.QFileDialog.Accepted:
            path = dialog.selectedFiles()[0]
            self.page().save(path, QtWebEngineWidgets.QWebEngineDownloadItem.CompleteHtmlSaveFormat)
        
    def handle_console_message(self, message):
        main_window = self.window()
        if main_window:
            for i in range(main_window.tabs.count()):
                if isinstance(main_window.tabs.widget(i), DebugConsole):
                    debug_console = main_window.tabs.widget(i)
                    debug_console.log(message)
                    break

class PrivateBrowserTab(BrowserTab):
    def __init__(self, url="https://www.google.com", parent=None):
        super().__init__(url, parent)
        self.private_profile = QWebEngineProfile()
        self.private_profile.setOffTheRecord(True)
        self.private_page = CustomWebEnginePage(self.private_profile, self)
        self.setPage(self.private_page)
        self.setUrl(QUrl(url))
    
    def closeEvent(self, event):
        self.private_profile.clearAllVisitedLinks()
        self.private_profile.clearHttpCache()
        self.private_profile.cookieStore().deleteAllCookies()
        super().closeEvent(event)

class HistoryPage(QtWidgets.QWidget):
    """A page to display browsing history."""
    def __init__(self, history):
        super().__init__()
        layout = QtWidgets.QVBoxLayout()
        self.history_label = QtWidgets.QLabel("Browsing History")
        self.history_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.history_label)
        self.history_list = QtWidgets.QListWidget()
        self.load_history(history)
        layout.addWidget(self.history_list)

        self.setLayout(layout)

    def load_history(self, history):
        """Load the history into the list widget."""
        for url in history:
            item = QtWidgets.QListWidgetItem(url)
            self.history_list.addItem(item)


class PyBrowse(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyBrowse")
        self.setGeometry(100, 100, 1024, 768)
        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.central_widget = central_widget
        self.tabs = TabWidget(self)
        layout.addWidget(self.tabs)
        self.create_navigation_bar()
        layout.addWidget(self.navigation_bar)
        self.bookmarks_file = "bookmarks.json"
        self.history_file = "history.json"
        self.bookmarks = []
        self.history = []
        self.is_fullscreen = False
        self.create_fullscreen_toggle()
        self.load_bookmarks()
        self.load_history()
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_url_bar)
        self.create_menu_bar()
        self.is_private_mode = False
        self.create_private_mode_toggle()
        self.add_new_tab("https://www.google.com")
    
    def update_frame(self):
        self.repaint()
    
    def create_private_mode_toggle(self):
        private_mode_action = QtWidgets.QAction("Private Mode", self)
        private_mode_action.setCheckable(True)
        private_mode_action.toggled.connect(self.toggle_private_mode)
        self.navigation_bar.addAction(private_mode_action)

    def toggle_private_mode(self, enabled):
        self.is_private_mode = enabled
        if enabled:
            self.setWindowTitle("PyBrowse (Private Mode)")
        else:
            self.setWindowTitle("PyBrowse")

    def create_navigation_bar(self):
        """Create the navigation bar with URL entry, back, reload, go buttons, and new tab button."""
        self.navigation_bar = QtWidgets.QToolBar("Navigation")
        self.navigation_bar.setMovable(False)
        back_button = QtWidgets.QAction("Back", self)
        back_button.triggered.connect(self.go_back)
        self.navigation_bar.addAction(back_button)
        reload_button = QtWidgets.QAction("Reload", self)
        reload_button.triggered.connect(self.reload_page)
        self.navigation_bar.addAction(reload_button)
        self.url_bar = QtWidgets.QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.navigation_bar.addWidget(self.url_bar)
        go_button = QtWidgets.QAction("Go", self)
        go_button.triggered.connect(self.navigate_to_url)
        self.navigation_bar.addAction(go_button)
        new_tab_button = QtWidgets.QAction("New Tab", self)
        new_tab_button.triggered.connect(lambda: self.add_new_tab())
        self.navigation_bar.addAction(new_tab_button)
        dev_tools_button = QtWidgets.QAction("Debug Menu", self)
        dev_tools_button.triggered.connect(self.open_dev_tools)
        self.navigation_bar.addAction(dev_tools_button)
        history_button = QtWidgets.QAction("History", self)
        history_button.triggered.connect(self.open_history_page)
        self.navigation_bar.addAction(history_button)
        fullscreen_button = QtWidgets.QAction("Fullscreen", self)
        fullscreen_button.triggered.connect(self.toggle_fullscreen)
        self.navigation_bar.addAction(fullscreen_button)

    def create_fullscreen_toggle(self):
        self.fullscreen_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("F11"), self)
        self.fullscreen_shortcut.activated.connect(self.toggle_fullscreen)

    def toggle_fullscreen(self):
        if not self.is_fullscreen:
            self.showFullScreen()
            self.is_fullscreen = True
        else:
            self.showNormal()
            self.is_fullscreen = False
        self.central_widget.setGeometry(self.rect())

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
        QtWidgets.QMessageBox.information(self, "About PyBrowse", "PyBrowse - Version 0.1.2")

    def add_new_tab(self, url="https://www.google.com"):
        self.setUpdatesEnabled(False)
        if self.is_private_mode:
            new_tab = PrivateBrowserTab(url)
        else:
            new_tab = BrowserTab(url)
        
        index = self.tabs.addTab(new_tab, "New Tab")
        self.tabs.setCurrentIndex(index)
        new_tab.titleChanged.connect(lambda title, tab=new_tab: self.update_tab_title(tab, title))
        new_tab.urlChanged.connect(self.update_url_bar)
        
        if not self.is_private_mode:
            new_tab.urlChanged.connect(self.add_to_history)
        self.setUpdatesEnabled(True)
    
    def update_tab_title(self, tab, title):
        index = self.tabs.indexOf(tab)
        if index != -1:
            self.tabs.setTabText(index, title)

    def close_tab(self, index):
        """Close the tab at the given index."""
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)

    def navigate_to_url(self):
        """Load the URL entered in the URL bar into the current tab."""
        url = self.url_bar.text()
        if not url.startswith("http"):
            url = "http://" + url

        current_tab = self.tabs.currentWidget()
        if isinstance(current_tab, BrowserTab):
            current_tab.setUrl(QtCore.QUrl(url))

    def update_url_bar(self):
        """Update the URL bar when the user navigates to a different page."""
        if self.tabs.count() > 0:
            current_tab = self.tabs.currentWidget()
            if isinstance(current_tab, BrowserTab):
                self.url_bar.setText(current_tab.url().toString())
            else:
                self.url_bar.clear()

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

    def open_history_page(self):
        """Open a new tab with the browsing history."""
        history_tab = HistoryPage(self.history)
        i = self.tabs.addTab(history_tab, "History")
        self.tabs.setCurrentIndex(i)

    def add_to_history(self, url):
        if not self.is_private_mode:
            url_str = url.toString()
            if url_str not in self.history:
                self.history.append(url_str)
                self.save_history()

    # FIXME: The debug menu is known internally as open_dev_tools (or just DevTools in general), but it should really be something like open_debug_menu. I'll change this soon.
    def open_dev_tools(self):
        """Open an enhanced debug console in a new tab."""
        debug_console = DebugConsole(self)
        i = self.tabs.addTab(debug_console, "Debug Console")
        self.tabs.setCurrentIndex(i)
        current_tab = self.tabs.widget(self.tabs.currentIndex() - 1)
        if isinstance(current_tab, BrowserTab):
            url = current_tab.url().toString()
            debug_console.log(f"Current page: {url}")
            current_tab.page().runJavaScript("navigator.userAgent", debug_console.log)
            current_tab.page().runJavaScript("window.location.href", lambda result: debug_console.log(f"Full URL: {result}"))
            current_tab.page().runJavaScript("document.title", lambda result: debug_console.log(f"Page Title: {result}"))
            current_tab.page().runJavaScript("document.readyState", lambda result: debug_console.log(f"Document Ready State: {result}"))

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

    def save_history(self):
        """Save the history to a JSON file."""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f)

    def load_history(self):
        """Load history from a JSON file if it exists."""
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                self.history = json.load(f)
        else:
            self.history = []

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape and self.is_fullscreen:
            self.toggle_fullscreen()
        else:
            super().keyPressEvent(event)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.central_widget.setGeometry(self.rect())

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = PyBrowse()
    window.show()
    sys.exit(app.exec_())
