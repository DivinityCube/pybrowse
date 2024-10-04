import sys
import re
import requests
from urllib.parse import quote
import json
import os
import icons_rc
import pyttsx3
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt5 import QtWidgets, QtCore, QtWebEngineWidgets, QtGui
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile
from PyQt5.QtCore import QUrl, QTimer, QFileInfo, QDir, pyqtSignal, QThread, Qt, QRunnable, QThreadPool
from PyQt5.QtWidgets import QWidget, QMainWindow, QTabWidget, QLabel, QAction, QFileDialog, QStyleFactory, QListWidgetItem, QProgressBar, QFileDialog, QMenu, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QGridLayout
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtGui import QIcon, QCursor
from datetime import datetime, timedelta
from functools import partial

class CustomNewTabPage(QWidget):
    def __init__(self, main_window, is_private=False):
        super().__init__(parent=main_window)
        self.main_window = main_window
        self.is_private = is_private
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        mode_label = QLabel("Private Browsing" if self.is_private else "Normal Browsing")
        mode_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(mode_label)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search or enter address")
        self.search_bar.returnPressed.connect(self.perform_search)
        layout.addWidget(self.search_bar)
        if not self.is_private:
            most_visited_layout = QGridLayout()
            for i in range(8):
                site_button = QPushButton(f"Site {i+1}")
                site_button.clicked.connect(partial(self.open_url, f"https://example{i+1}.com"))
                most_visited_layout.addWidget(site_button, i // 4, i % 4)
            layout.addLayout(most_visited_layout)
        quick_links_layout = QHBoxLayout()
        quick_links = [("Google", "https://www.google.com"),
                       ("YouTube", "https://www.youtube.com"),
                       ("GitHub", "https://www.github.com")]
        for name, url in quick_links:
            link_button = QPushButton(name)
            link_button.clicked.connect(partial(self.open_url, url))
            quick_links_layout.addWidget(link_button)
        layout.addLayout(quick_links_layout)
        if not self.is_private:
            weather_label = QLabel("Weather: Placeholder")
            layout.addWidget(weather_label)
            news_label = QLabel("Latest News: PyBrowse 0.2.2 Released!")
            layout.addWidget(news_label)

        self.setLayout(layout)

    def perform_search(self):
        query = self.search_bar.text()
        url = QUrl(f"https://www.google.com/search?q={query}")
        self.main_window.add_new_tab(url.toString(), is_private=self.is_private)

    def open_url(self, url):
        self.main_window.add_new_tab(url, is_private=self.is_private)

class TextToSpeechEngine(QRunnable):
    def __init__(self, text, finished_callback):
        super().__init__()
        self.engine = pyttsx3.init()
        self.text = text
        self.finished_callback = finished_callback

    def run(self):
        self.engine.say(self.text)
        self.engine.runAndWait()
        self.finished_callback()

class AccessibilityPage(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        title = QtWidgets.QLabel("Accessibility Features")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        self.high_contrast_checkbox = QtWidgets.QCheckBox("High Contrast Mode")
        self.high_contrast_checkbox.stateChanged.connect(self.toggle_high_contrast)
        layout.addWidget(self.high_contrast_checkbox)
        self.tts_checkbox = QtWidgets.QCheckBox("Enable Text-to-Speech")
        self.tts_checkbox.stateChanged.connect(self.toggle_tts)
        layout.addWidget(self.tts_checkbox)
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_widget)
        self.add_section(scroll_layout, "Keyboard Shortcuts", [
            ("Ctrl + T", "Open new tab"),
            ("Ctrl + W", "Close current tab"),
            ("Ctrl + L", "Focus address bar"),
            ("F11", "Toggle fullscreen"),
            ("Esc", "Exit fullscreen"),
        ])

        self.add_section(scroll_layout, "Text Zoom", [
            ("To increase or decrease the text size:"),
            ("1. Press Ctrl and scroll the mouse wheel"),
            ("2. Or use Ctrl + Plus (+) to zoom in"),
            ("3. Use Ctrl + Minus (-) to zoom out"),
            ("4. Use Ctrl + 0 to reset zoom"),
        ])

        self.add_section(scroll_layout, "Reader Mode", [
            ("1. Click the 'Reader Mode' button in the toolbar"),
            ("2. This simplifies the page layout for easier reading"),
        ])

        self.add_section(scroll_layout, "Private Browsing", [
            ("1. Toggle 'Private Mode' in the navigation bar"),
            ("2. Your browsing history and cookies won't be saved in this mode"),
        ])

        self.add_section(scroll_layout, "Screen Reader Compatibility", [
            "PyBrowse is compatible with most screen readers.",
            "Please ensure your screen reader is up to date for the best experience.",
        ])

        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
    
    def toggle_high_contrast(self, state):
        if state == QtCore.Qt.Checked:
            self.window().setStyleSheet("""
                QWidget { background-color: black; color: white; }
                QLineEdit { background-color: white; color: black; }
                QPushButton { background-color: white; color: black; }
            """)
        else:
            self.window().setStyleSheet("")
    
    def toggle_tts(self, state):
        print("Text-to-speech toggled:", state == QtCore.Qt.Checked)

    def add_section(self, layout, title, items):
        section_title = QtWidgets.QLabel(title)
        section_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(section_title)

        for item in items:
            if isinstance(item, tuple):
                label = QtWidgets.QLabel(f"<b>{item[0]}:</b> {item[1]}")
            else:
                label = QtWidgets.QLabel(item)
            label.setWordWrap(True)
            layout.addWidget(label)
        layout.addSpacing(10)

class DownloadManager(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.download_finished)
        self.downloads = {}
        print("DownloadManager initialized")

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        self.download_list = QtWidgets.QListWidget()
        layout.addWidget(self.download_list)

    def add_download(self, url):
        print(f"Adding download for URL: {url}")
        url = QUrl(url)
        file_info = QFileInfo(url.path())
        file_name = file_info.fileName()
        if not file_name:
            file_name = "download"
        save_path, _ = QFileDialog.getSaveFileName(self, "Save File", QDir.homePath() + "/Downloads/" + file_name)
        if save_path:
            print(f"Saving file to: {save_path}")
            request = QNetworkRequest(url)
            reply = self.network_manager.get(request)
            item = QListWidgetItem(f"Downloading: {file_name}")
            self.download_list.addItem(item)
            progress_bar = QProgressBar(self.download_list)
            self.download_list.setItemWidget(item, progress_bar)
            self.downloads[reply] = {
                "item": item,
                "progress_bar": progress_bar,
                "file": open(save_path, "wb"),
                "file_name": file_name
            }
            reply.downloadProgress.connect(lambda received, total, r=reply: self.update_progress(received, total, r))
            reply.readyRead.connect(lambda r=reply: self.save_data(r))
        else:
            print("File save cancelled by user")

    def update_progress(self, received, total, reply):
        download = self.downloads.get(reply)
        if download:
            progress = int(received * 100 / total)
            download["progress_bar"].setValue(progress)
            download["item"].setText(f"Downloading: {download['file_name']} - {progress}%")

    def save_data(self, reply):
        download = self.downloads.get(reply)
        if download:
            download["file"].write(reply.readAll())

    def download_finished(self, reply):
        download = self.downloads.get(reply)
        if download:
            download["file"].close()
            self.downloads.pop(reply)
            download["item"].setText(f"Completed: {download['file_name']}")
            download["progress_bar"].setValue(100)
        reply.deleteLater()

class AdBlocker(QWebEngineUrlRequestInterceptor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ad_hosts = set()
        self.tracker_hosts = set()
        self.cache_file = "adblocker_cache.json"
        self.cache_duration = timedelta(days=7)
        self.load_hosts()
    
    def load_hosts(self):
        if self.is_cache_valid():
            self.load_from_cache()
        else:
            self.load_ad_hosts()
            self.load_tracker_hosts()
            self.save_to_cache()
    
    def is_cache_valid(self):
        if not os.path.exists(self.cache_file):
            return False
        with open(self.cache_file, 'r') as f:
            cache = json.load(f)
        last_updated = datetime.fromisoformat(cache['last_updated'])
        return datetime.now() - last_updated < self.cache_duration

    def load_from_cache(self):
        with open(self.cache_file, 'r') as f:
            cache = json.load(f)
        self.ad_hosts = set(cache['ad_hosts'])
        self.tracker_hosts = set(cache['tracker_hosts'])
    
    def save_to_cache(self):
        cache = {
            'last_updated': datetime.now().isoformat(),
            'ad_hosts': list(self.ad_hosts),
            'tracker_hosts': list(self.tracker_hosts)
        }
        with open(self.cache_file, 'w') as f:
            json.dump(cache, f)

    def load_ad_hosts(self):
        url = "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_adservers.txt"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                for line in response.text.splitlines():
                    if line.startswith('||') and '^' in line:
                        domain = line.split('^')[0][2:]
                        self.ad_hosts.add(domain)
            else:
                print(f"Failed to fetch ad list. Status code: {response.status_code}")
        except requests.RequestException as e:
            print(f"Error fetching ad list: {e}")
            self.ad_hosts.update([
                'ads.google.com',
                'googleadservices.com',
                'doubleclick.net',
            ])

    def load_tracker_hosts(self):
        url = "https://raw.githubusercontent.com/easylist/easylist/master/easyprivacy/easyprivacy_trackingservers.txt"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                for line in response.text.splitlines():
                    if line.startswith('||') and '^' in line:
                        domain = line.split('^')[0][2:]
                        self.tracker_hosts.add(domain)
            else:
                print(f"Failed to fetch tracker list. Status code: {response.status_code}")
        except requests.RequestException as e:
            print(f"Error fetching tracker list: {e}")
            self.tracker_hosts.update([
                'analytics.google.com',
                'facebook.com',
                'tracking.example.com',
            ])

    def interceptRequest(self, info):
        url = info.requestUrl()
        if self.should_block_ad(url) or self.should_block_tracker(url):
            info.block(True)

    def should_block_ad(self, url):
        return any(url.host().endswith(host) for host in self.ad_hosts)

    def should_block_tracker(self, url):
        return any(url.host().endswith(host) for host in self.tracker_hosts)

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


class BrowserTab(QWebEngineView):
    def __init__(self, url="https://www.google.com", profile=None, parent=None):
        super().__init__(parent)
        self.ad_blocker = AdBlocker(self)
        self.profile = profile or QWebEngineProfile.defaultProfile()
        self._page = QWebEnginePage(self.profile, self)
        self.profile.setUrlRequestInterceptor(self.ad_blocker)
        self.setPage(self._page)
        self.custom_page = CustomWebEnginePage(self)
        self.web_page = QWebEnginePage(self.profile, self)
        self.setUrl(QUrl(url))
        self.reader_mode_active = False
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.custom_page.console_message.connect(self.handle_console_message)
        self._page.loadFinished.connect(self.page_loaded)
        self.tts_engine = None
        self.thread_pool = QThreadPool()
        self.page().profile().setUrlRequestInterceptor(self.ad_blocker)
        self.image_url = None
        print("BrowserTab initialized")
        self.source_window = None
    
    def page_loaded(self, ok):
        if ok:
            print("Page loaded successfully")
            self._page.runJavaScript("""
                document.addEventListener('contextmenu', function(e) {
                    if (e.target.tagName.toLowerCase() === 'img') {
                        window.imageUrl = e.target.src;
                        console.log('Right-clicked on image:', window.imageUrl);
                    } else {
                        window.imageUrl = null;
                        console.log('Right-clicked, but not on image');
                    }
                });
            """)
        else:
            print("Page failed to load")
    
    def contextMenuEvent(self, event):
        menu = self.page().createStandardContextMenu()
        selected_text = self.page().selectedText()
        if selected_text:
            speak_action = QAction("Speak Selected Text", self)
            speak_action.triggered.connect(lambda: self.speak_text(selected_text))
            menu.addAction(speak_action)
        menu.exec_(event.globalPos())

    def speak_text(self, text):
        if self.tts_engine is not None:
            self.thread_pool.clear()
        self.tts_engine = TextToSpeechEngine(text, self.on_tts_finished)
        self.thread_pool.start(self.tts_engine)

    def on_tts_finished(self):
        print("Text-to-speech finished")
    
    def show_context_menu(self, position):
        menu = QtWidgets.QMenu(self)
        js_code = """
            var element = document.elementFromPoint(%d, %d);
            var link = element ? element.closest('a') : null;
            link ? link.href : null;
            """ % (position.x(), position.y())
        self.page().runJavaScript(js_code, lambda link_url: self.build_context_menu(menu, position, link_url))
    
    def build_context_menu(self, menu, position, link_url):
        print("Building context menu")
        self.page().runJavaScript("window.imageUrl;", self.handle_image_context_menu)
        if self.image_url:
            print(f"Image URL found: {self.image_url}")
            download_action = QAction("Download Image", self)
            download_action.triggered.connect(self.download_image)
            menu.addAction(download_action)
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
    
    def handle_image_context_menu(self, image_url):
        if image_url:
            print(f"Handling image context menu, image_url: {image_url}")
            self.image_url = image_url
    
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
    
    def toggle_reader_mode(self):
        if not self.reader_mode_active:
            js_code = """
            (function() {
                var script = document.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/@mozilla/readability@0.4.4/Readability.js';
                script.onload = function() {
                    var article = new Readability(document).parse();
                    if (article) {
                        document.body.innerHTML = '<h1>' + article.title + '</h1>' + article.content;

                        var style = document.createElement('style');
                        style.innerHTML = `
                            body { font-family: Arial, sans-serif; font-size: 18px; line-height: 1.6; background-color: #f5f5f5; color: #333; margin: 0 auto; max-width: 800px; padding: 20px; }
                            h1 { font-size: 2em; font-weight: bold; }
                            img { max-width: 100%; height: auto; }
                            p { margin-bottom: 20px; }
                        `;
                        document.head.appendChild(style);
                    } else {
                        alert('Failed to extract readable content.');
                    }
                };
                document.head.appendChild(script);
            })();
            """
            self.page().runJavaScript(js_code)
            self.reader_mode_active = True
        else:
            self.reload()
            self.reader_mode_active = False
    
    def closeEvent(self, event):
        self.web_page.deleteLater()
        self.profile.setUrlRequestInterceptor(None)
        self.web_page.setParent(None)
        self.profile.deleteLater()
        super().closeEvent(event)

class PrivateBrowserTab(BrowserTab):
    def __init__(self, url="https://www.google.com", profile=None, parent=None):
        super().__init__(url, parent)
        self.profile = profile or QWebEngineProfile(None)
        self.page = QWebEnginePage(self.profile, self)
        self.setPage(self.page)
        self.setUrl(QUrl(url))
    
    def page_loaded(self, ok):
        if ok:
            print("Private page loaded successfully")
            self._page.runJavaScript("""
                document.addEventListener('contextmenu', function(e) {
                    if (e.target.tagName.toLowerCase() === 'img') {
                        window.imageUrl = e.target.src;
                        console.log('Right-clicked on image (private):', window.imageUrl);
                    } else {
                        window.imageUrl = null;
                        console.log('Right-clicked, but not on image (private)');
                    }
                });
            """)
        else:
            print("Private page failed to load")
    
    def closeEvent(self, event):
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
        self.create_tts_toggle()
        self.is_private_mode = False
        self.default_profile = QWebEngineProfile.defaultProfile()
        self.private_profile = QWebEngineProfile(None)
        self.reader_mode_active = False
        self.cleanup_timer = QTimer(self)
        self.cleanup_timer.setSingleShot(True)
        self.cleanup_timer.timeout.connect(self.delayed_cleanup)
        self.create_private_mode_toggle()
        self.download_manager = DownloadManager()
        self.add_new_tab("https://www.google.com")
    
    def add_new_tab(self, url=None, is_private=None):
        if is_private is None:
            is_private = self.is_private_mode
        if url is None:
            new_tab_page = CustomNewTabPage(self, is_private)
            i = self.tabs.addTab(new_tab_page, "New Private Tab" if is_private else "New Tab")
        else:
            if is_private:
                browser = PrivateBrowserTab(url, self.private_profile)
            else:
                browser = BrowserTab(url, self.default_profile)
            i = self.tabs.addTab(browser, "New Private Tab" if is_private else "New Tab")
            browser.urlChanged.connect(lambda qurl, browser=browser: self.update_url_bar(qurl, browser))
            browser.loadFinished.connect(lambda _, i=i, browser=browser: 
                self.tabs.setTabText(i, browser._page.title()))
        self.tabs.setCurrentIndex(i)

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
    
    def open_accessibility_page(self):
        accessibility_page = AccessibilityPage(self)
        i = self.tabs.addTab(accessibility_page, "Accessibility")
        self.tabs.setCurrentIndex(i)
    
    def set_application_style(self):
        QtWidgets.QApplication.setStyle(QStyleFactory.create("Fusion"))
        dark_palette = QtGui.QPalette()
        dark_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
        dark_palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.Base, QtGui.QColor(25, 25, 25))
        dark_palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(53, 53, 53))
        dark_palette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.Button, QtGui.QColor(53, 53, 53))
        dark_palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
        dark_palette.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))
        dark_palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
        dark_palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)
        QtWidgets.QApplication.setPalette(dark_palette)
        self.setStyleSheet("""
            QToolBar {
                background-color: #2b2b2b;
                border: none;
                padding: 5px;
            }
            QToolBar QToolButton {
                background-color: transparent;
                border: none;
                border-radius: 3px;
                padding: 5px;
            }
            QToolBar QToolButton:hover {
                background-color: #3a3a3a;
            }
            QToolBar QLineEdit {
                background-color: #1e1e1e;
                border: 1px solid #3a3a3a;
                border-radius: 3px;
                color: white;
                padding: 3px;
            }
        """)

    def create_navigation_bar(self):
        """Create the navigation bar with URL entry, back, reload, go buttons, and new tab button."""
        self.navigation_bar = QtWidgets.QToolBar("Navigation")
        self.navigation_bar.setMovable(False)
        back_button = QAction(QIcon.fromTheme("go-previous", QIcon(":/icons/back.svg")), "Back", self)
        back_button.triggered.connect(self.go_back)
        self.navigation_bar.addAction(back_button)
        forward_button = QAction(QIcon.fromTheme("go-next", QIcon(":/icons/forward.svg")), "Forward", self)
        forward_button.triggered.connect(self.go_forward)
        self.navigation_bar.addAction(forward_button)
        reload_button = QAction(QIcon.fromTheme("view-refresh", QIcon(":/icons/reload.svg")), "Reload", self)
        reload_button.triggered.connect(self.reload_page)
        self.navigation_bar.addAction(reload_button)
        self.url_bar = QtWidgets.QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.navigation_bar.addWidget(self.url_bar)
        go_button = QAction(QIcon.fromTheme("go-jump", QIcon(":/icons/go.svg")), "Go", self)
        go_button.triggered.connect(self.navigate_to_url)
        self.navigation_bar.addAction(go_button)
        new_tab_button = QAction(QIcon.fromTheme("tab-new", QIcon(":/icons/new_tab.svg")), "New Tab", self)
        new_tab_button.triggered.connect(lambda: self.add_new_tab())
        self.navigation_bar.addAction(new_tab_button)
        reader_mode_button = QAction(QIcon.fromTheme("format-justify-fill", QIcon(":/icons/reader_mode.svg")), "Reader Mode", self)
        reader_mode_button.triggered.connect(self.toggle_reader_mode)
        self.navigation_bar.addAction(reader_mode_button)
        dev_tools_button = QAction(QIcon.fromTheme("applications-development", QIcon(":/icons/dev_tools.svg")), "Debug Menu", self)
        dev_tools_button.triggered.connect(self.open_dev_tools)
        self.navigation_bar.addAction(dev_tools_button)
        history_button = QAction(QIcon.fromTheme("document-open-recent", QIcon(":/icons/history.svg")), "History", self)
        history_button.triggered.connect(self.open_history_page)
        self.navigation_bar.addAction(history_button)
        fullscreen_button = QAction(QIcon.fromTheme("view-fullscreen", QIcon(":/icons/fullscreen.svg")), "Fullscreen", self)
        fullscreen_button.triggered.connect(self.toggle_fullscreen)
        self.navigation_bar.addAction(fullscreen_button)
        download_button = QAction(QIcon.fromTheme("download", QIcon(":/icons/download.svg")), "Downloads", self)
        download_button.triggered.connect(self.open_download_manager)
        self.navigation_bar.addAction(download_button)
    
    def open_download_manager(self):
        for i in range(self.tabs.count()):
            if isinstance(self.tabs.widget(i), DownloadManager):
                self.tabs.setCurrentIndex(i)
                return
        download_tab_index = self.tabs.addTab(self.download_manager, "Downloads")
        self.tabs.setCurrentIndex(download_tab_index)


    def go_forward(self):
        if self.tabs.count() > 0:
            self.tabs.currentWidget().forward()

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
        help_menu.addAction("Accessibility", self.open_accessibility_page)
        self.bookmarks_menu = menu_bar.addMenu("Bookmarks")
        add_bookmark_action = QtWidgets.QAction("Add Bookmark", self)
        add_bookmark_action.triggered.connect(self.add_bookmark)
        self.bookmarks_menu.addAction(add_bookmark_action)
        self.bookmarks_menu.addSeparator()
        self.load_bookmarks_menu()

    def show_about_dialog(self):
        """Show an About dialog with browser information."""
        QtWidgets.QMessageBox.information(self, "About PyBrowse", "PyBrowse - Version 0.2.3")
    
    def update_tab_title(self, tab, title):
        index = self.tabs.indexOf(tab)
        if index != -1:
            self.tabs.setTabText(index, title)

    def close_tab(self, index):
        """Close the tab at the given index."""
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)

    def navigate_to_url(self):
        query = self.url_bar.text().strip()
        # Basically this is checking to see if it's a URL
        if re.match(r'^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$', query):
            if not query.startswith(('http://', 'https://')):
                query = 'http://' + query
        else:
            query = f'https://www.google.com/search?q={quote(query)}'

        current_tab = self.tabs.currentWidget()
        if isinstance(current_tab, BrowserTab):
            current_tab.setUrl(QtCore.QUrl(query))
        elif isinstance(current_tab, DownloadManager):
            self.download_manager.add_download(query)

    def update_url_bar(self, q, browser=None):
        if browser != self.tabs.currentWidget():
            return
        if isinstance(q, int):
            # This is likely an index, not a URL. Let's ignore it.
            return
        if not isinstance(q, QUrl):
            # This is essentially saying: if it's not a QUrl object, try to convert it
            # (Rough English translation, of course)
            q = QUrl(str(q))
        if q.toString() == 'about:blank':
            return
        self.url_bar.setText(q.toString())
        self.url_bar.setCursorPosition(0)

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

    def toggle_reader_mode(self):
        current_tab = self.tabs.currentWidget()
        if isinstance(current_tab, BrowserTab):
            current_tab.toggle_reader_mode()
    
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
    
    def create_tts_toggle(self):
        self.tts_action = QAction("Enable Text-to-Speech", self)
        self.tts_action.setCheckable(True)
        self.tts_action.toggled.connect(self.toggle_tts)
        self.navigation_bar.addAction(self.tts_action)

    def toggle_tts(self, enabled):
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if isinstance(tab, BrowserTab):
                tab.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu if enabled else QtCore.Qt.NoContextMenu)
    
    # To also prevent memory leaks and such 
    def closeEvent(self, event):
        while self.tabs.count() > 0:
            widget = self.tabs.widget(0)
            self.tabs.removeTab(0)
            if hasattr(widget, 'close'):
                widget.close()
            widget.deleteLater()
        if hasattr(self, 'download_manager'):
            self.download_manager.close()
            self.download_manager.deleteLater()
        event.accept()

    def start_cleanup(self):
        while self.tabs.count() > 0:
            tab = self.tabs.widget(0)
            self.tabs.removeTab(0)
            if isinstance(tab, BrowserTab):
                tab.close()
                tab.deleteLater()
        QTimer.singleShot(100, self.delayed_cleanup)

    def delayed_cleanup(self):
        self.tabs.deleteLater()
        self.close()
    


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = PyBrowse()
    window.show()
    sys.exit(app.exec_())