import tkinter as tk
from tkinter import ttk, messagebox
from tkhtmlview import HTMLLabel
import requests

browser_version = "0.0.1"

class Browser:
    def __init__(self, root):
        self.root = root
        self.root.title("PyBrowse")
        self.root.geometry("800x600")
        self.root.configure(bg='#e1e1e1')
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        self.default_html = "<h1>Welcome to PyBrowse</h1><p>Enter a URL above and click 'Go'!</p>"
        self.url_frame = tk.Frame(self.root, bg='#d3d3d3', padx=10, pady=5)
        self.url_frame.pack(fill='x')
        self.url_entry = ttk.Entry(self.url_frame, width=80, font=('Arial', 12))
        self.url_entry.pack(side='left', padx=5)
        self.go_button = ttk.Button(self.url_frame, text="Go", command=self.load_url)
        self.go_button.pack(side='left', padx=5)
        self.back_button = ttk.Button(self.url_frame, text="Back", command=self.go_back)
        self.back_button.pack(side='left', padx=5)
        self.refresh_button = ttk.Button(self.url_frame, text="Refresh", command=self.refresh_page)
        self.refresh_button.pack(side='left', padx=5)
        self.content_frame = tk.Frame(self.root)
        self.content_frame.pack(fill='both', expand=True, padx=10, pady=10)
        self.content_scrollbar = tk.Scrollbar(self.content_frame)
        self.content_scrollbar.pack(side='right', fill='y')
        self.html_display = HTMLLabel(self.content_frame, html=self.default_html, 
                                      font=('Arial', 10), bg='#fff', relief='sunken')
        self.html_display.pack(fill='both', expand=True)
        self.html_display.fit_height()
        self.html_display.bind("<Configure>", lambda e: self.content_scrollbar.set(0, 1))
        self.html_display.config(yscrollcommand=self.content_scrollbar.set)
        self.content_scrollbar.config(command=self.html_display.yview)
        self.history = []
        self.current_url = None

    def load_url(self):
        """Fetch and load HTML content from a URL."""
        url = self.url_entry.get()
        if not url.startswith("http"):
            url = "http://" + url

        try:
            response = requests.get(url)
            response.raise_for_status()
            html_content = response.text
            self.html_display.set_html(html_content)
            self.history.append(url)
            self.current_url = url

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to load URL: {url}\n\n{e}")

    def go_back(self):
        """Simulate going back in history."""
        if len(self.history) > 1:
            self.history.pop()  
            previous_url = self.history[-1]
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, previous_url)
            self.load_url()

    def refresh_page(self):
        """Reload the current page."""
        if self.current_url:
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, self.current_url)
            self.load_url()
    
    def show_about(self):
        """Display the About dialog with browser version."""
        messagebox.showinfo("About Simple Tkinter Browser", f"PyBrowse\nVersion: {browser_version}")

root = tk.Tk()
app = Browser(root)
root.mainloop()