import tkinter as tk
from tkinter import ttk, messagebox
import threading
import pandas as pd
import re
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import random
from datetime import datetime, timedelta
import platform
import sys

# =======================
# API and Limit Configuration
# =======================
API_KEY = ""
CSE_ID = ""
MAX_RESULTS_PER_QUERY = 100
SEARCH_HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "search_history.txt")
QUERIES_COUNT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "query_counter.txt")

# =======================
# Working Folder
# =======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "Search_Results")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# =======================
# Helper Functions
# =======================
def get_query_count():
    """Retrieves the query counter from file or resets it if 9:00 AM has passed."""
    now = datetime.now()
    try:
        with open(QUERIES_COUNT_FILE, "r") as f:
            lines = f.readlines()
            last_date_str = lines[0].strip()
            count = int(lines[1].strip())
            last_date = datetime.strptime(last_date_str, "%Y-%m-%d")

            # Reset logic: next day or same day after 9:00 AM if last count was before 9:00 AM
            if now.date() > last_date.date() or (
                    now.date() == last_date.date() and now.hour >= 9 and last_date.hour < 9):
                reset_query_count()
                return 0
            return count
    except (FileNotFoundError, IndexError, ValueError):
        reset_query_count()
        return 0


def update_query_count(count):
    """Updates the query counter in the file."""
    now = datetime.now()
    with open(QUERIES_COUNT_FILE, "w") as f:
        f.write(now.strftime("%Y-%m-%d") + "\n")
        f.write(str(count) + "\n")


def reset_query_count():
    """Resets the query counter."""
    now = datetime.now()
    with open(QUERIES_COUNT_FILE, "w") as f:
        f.write(now.strftime("%Y-%m-%d") + "\n")
        f.write("0\n")


def load_search_history():
    """Loads history from file and displays it in the window."""
    try:
        with open(SEARCH_HISTORY_FILE, "r") as f:
            history = f.read()
            history_text.config(state=tk.NORMAL)
            history_text.delete("1.0", tk.END)
            history_text.insert(tk.END, history)
            history_text.config(state=tk.DISABLED)
    except FileNotFoundError:
        pass


def open_prospects_file():
    """Opens the generated prospects.xlsx file, cross-platform."""
    file_path = os.path.join(OUTPUT_DIR, "prospects.xlsx")
    if os.path.exists(file_path):
        current_os = platform.system()
        try:
            if current_os == "Windows":
                os.startfile(file_path)
            elif current_os == "Darwin":  # macOS
                os.system(f"open {file_path}")
            elif current_os == "Linux":
                os.system(f"xdg-open {file_path}")
            else:
                messagebox.showerror("Error", "Unsupported operating system for file opening.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while opening the file: {e}")
    else:
        messagebox.showerror("Error", f"File does not exist:\n{file_path}")


def open_history_file():
    """Opens the search history file, cross-platform."""
    if os.path.exists(SEARCH_HISTORY_FILE):
        current_os = platform.system()
        try:
            if current_os == "Windows":
                os.startfile(SEARCH_HISTORY_FILE)
            elif current_os == "Darwin":  # macOS
                os.system(f"open {SEARCH_HISTORY_FILE}")
            elif current_os == "Linux":
                os.system(f"xdg-open {SEARCH_HISTORY_FILE}")
            else:
                messagebox.showerror("Error", "Unsupported operating system for file opening.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while opening the file: {e}")
    else:
        messagebox.showerror("Error", f"History file does not exist:\n{SEARCH_HISTORY_FILE}")


def get_domain_from_url(url):
    """Extracts the main domain from the given URL."""
    try:
        parsed_url = urlparse(url)
        domain_parts = parsed_url.netloc.split('.')
        # Tries to get the last two parts for the main domain (e.g., example.com)
        if len(domain_parts) > 1:
            return '.'.join(domain_parts[-2:])
        return parsed_url.netloc
    except Exception:
        return ""


# =======================
# Scraping Functions
# =======================
EMAIL_RE = re.compile(r"[a-zA-Z0-9.\-+_]+@[a-zA-Z0-9.\-+_]+\.[a-zA-Z]{2,}", re.I)
ZIP_CODE_RE = re.compile(r"\b\d{2}-\d{3}\b")
# General pattern for 9-digit numbers, possibly preceded by a country code and spaces/hyphens
PHONE_RE = re.compile(r"(?:\+?\d{2}\s*)?(\d{3}[\s-]?\d{3}[\s-]?\d{3}|\d{9})")


def search_with_api(query, lang_code, num_results, tld):
    """Searches for links on Google using the API, with the ability to change the number of results."""
    links = []
    queries_to_make = (num_results + 9) // 10  # 1 API query returns max 10 results

    current_count = get_query_count()
    if current_count + queries_to_make > 100:
        messagebox.showerror("Query Limit", "Daily limit of 100 API queries reached.")
        return []

    for i in range(queries_to_make):
        start_index = i * 10 + 1
        # Construct Google Custom Search API URL
        url = f"https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={CSE_ID}&q={query}&gl={tld}&hl={lang_code}&start={start_index}"

        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            results = response.json()

            if 'items' in results:
                for item in results['items']:
                    links.append({"query": query, "url": item['link']})

            update_query_count(current_count + 1)
            current_count += 1

            sleep_time = random.uniform(2, 5)
            time.sleep(sleep_time)

        except requests.exceptions.RequestException as e:
            print(f"Error during API query for '{query}': {e}")
            break

    return links


def fetch_page_with_requests(url):
    """Fetches page content using requests."""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def extract_contacts(html, base_url):
    """Extracts contact details from HTML, filtering out zip codes."""
    if not html:
        return {"emails": "", "phones": "", "description": "", "contact_links": ""}
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True)
    emails = set(EMAIL_RE.findall(text))

    phones = set()
    all_numbers = PHONE_RE.findall(text)

    # Filter out numbers that look like zip codes or are too short
    for num in all_numbers:
        # The regex for PHONE_RE returns the 9-digit group
        clean_num = num.replace(" ", "").replace("-", "")
        # Check if the number is NOT a zip code and has at least 9 digits (a basic filter)
        if not ZIP_CODE_RE.search(num) and len(clean_num) >= 9:
            phones.add(num)

    desc = ""
    d = soup.find("meta", {"name": "description"}) or soup.find("meta", {"property": "og:description"})
    if d and d.get("content"):
        desc = d.get("content").strip()

    # Find links that are likely contact pages
    contact_links = [urljoin(base_url, a["href"]) for a in soup.select("a[href]")
                     if
                     "kontakt" in a["href"].lower() or "contact" in a["href"].lower() or "mailto:" in a["href"].lower()]
    return {
        "emails": ";".join(sorted(emails)),
        "phones": ";".join(sorted(phones)),
        "description": desc,
        "contact_links": ";".join(contact_links)
    }


def process_queries_and_links(queries, lang_code, tld):
    """Main, synchronous function for processing queries and links."""
    # Write search history
    with open(SEARCH_HISTORY_FILE, "a") as f:
        f.write(f"Search on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        num_results_to_get = int(results_var.get())
        queries_to_make = (num_results_to_get + 9) // 10
        for q in queries:
            f.write(f"- {q} ({queries_to_make} API queries)\n")
        f.write("\n")

    root.after(0, load_search_history)

    num_results_to_get = int(results_var.get())

    # --- Step 1: Search Links ---
    status_label.config(text="⏳ Searching for links...")
    progress["maximum"] = len(queries)
    progress["value"] = 0
    all_links = []

    seen_domains = set()
    filtered_links = []

    for idx, query in enumerate(queries):
        links = search_with_api(query, lang_code, num_results_to_get, tld)

        # Filter links to keep only one link per unique domain
        for link in links:
            domain = get_domain_from_url(link['url'])
            if domain and domain not in seen_domains:
                filtered_links.append(link)
                seen_domains.add(domain)

        progress["value"] = idx + 1
        root.update_idletasks()

    df_links = pd.DataFrame(filtered_links).drop_duplicates(subset=["url"])

    # --- Step 2: Fetch Pages and Extract Contacts ---
    status_label.config(text="⏳ Fetching pages and extracting contacts...")
    contacts_results = []
    progress["maximum"] = len(df_links)
    progress["value"] = 0

    for idx, row in df_links.iterrows():
        html = fetch_page_with_requests(row["url"])
        info = extract_contacts(html, row["url"])
        contacts_results.append({
            "query": row["query"],
            "url": row["url"],
            **info
        })
        progress["value"] = idx + 1
        root.update_idletasks()
        sleep_time = random.uniform(2, 5)
        print(f"Waiting for {sleep_time:.2f} seconds before next page fetch...")
        time.sleep(sleep_time)

    df_contacts = pd.DataFrame(contacts_results).drop_duplicates(subset=["url"])
    contacts_file = os.path.join(OUTPUT_DIR, "prospects.xlsx")

    # --- Step 3: Save to Excel ---
    try:
        if os.path.exists(contacts_file):
            existing_df = pd.read_excel(contacts_file)
            # Concatenate new and existing data, dropping duplicates based on URL
            updated_df = pd.concat([existing_df, df_contacts]).drop_duplicates(subset=["url"]).reset_index(drop=True)
            updated_df.to_excel(contacts_file, index=False)
            messagebox.showinfo("Finished", f"Added {len(df_contacts)} new records to:\n{contacts_file}")
        else:
            df_contacts.to_excel(contacts_file, index=False)
            messagebox.showinfo("Finished", f"Saved {len(df_contacts)} records to:\n{contacts_file}")
    except Exception as e:
        messagebox.showerror("Save Error", f"An error occurred while saving the file: {e}")

    status_label.config(text=f"✅ Ready!")


# =======================
# GUI Functions
# =======================
def update_timer_and_counter():
    """Updates the query counter and reset timer in the GUI."""
    now = datetime.now()
    # Set next reset time to 9:00 AM today or tomorrow
    next_reset = datetime(now.year, now.month, now.day, 9, 0, 0)
    if now.hour >= 9:
        next_reset += timedelta(days=1)

    time_left = next_reset - now
    hours, remainder = divmod(time_left.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    timer_label.config(text=f"Reset in: {hours:02d}:{minutes:02d}:{seconds:02d}")

    query_count = get_query_count()
    counter_label.config(text=f"Queries: {query_count}/100")

    root.after(1000, update_timer_and_counter)  # Schedule next update


def run_pipeline():
    """Starts the main process function in a separate thread."""
    queries_text = queries_entry.get("1.0", tk.END).strip()
    if not queries_text:
        messagebox.showwarning("Warning", "Please enter at least one search phrase.")
        return
    queries = [q.strip() for q in queries_text.split("\n") if q.strip()]

    selected_country = country_var.get()
    # Get lang_code (hl) and tld (gl) from the dictionary
    lang_code, tld = country_codes.get(selected_country, ("pl", "pl"))

    def start_process():
        process_queries_and_links(queries, lang_code, tld)

    t = threading.Thread(target=start_process)
    t.start()


# =======================
# Console Redirection Class
# =======================
class ConsoleRedirect:
    """Class to redirect stdout (print statements) to a Tkinter Text widget."""

    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)  # Scroll to the end
        self.text_widget.config(state=tk.DISABLED)

    def flush(self):
        pass


# =======================
# GUI Setup
# =======================
root = tk.Tk()
root.title("Prospecting Tool - Google API")
# User-requested geometry: root.geometry("1120x720")
root.geometry("1120x720")

# Main frame split into two columns (left and right)
main_frame = ttk.Frame(root, padding=10)
main_frame.pack(fill=tk.BOTH, expand=True)

left_frame = ttk.Frame(main_frame, padding=10)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

right_frame = ttk.Frame(main_frame, padding=10)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# Left Side - Controls
ttk.Label(left_frame, text="Enter search phrases (one per line):").pack(anchor="w")
queries_entry = tk.Text(left_frame, width=50, height=10)
queries_entry.pack(fill=tk.BOTH, expand=True, pady=5)

# Options and Indicators Frame
options_frame = ttk.Frame(left_frame)
options_frame.pack(fill=tk.X, pady=10)

ttk.Label(options_frame, text="Results per query:").pack(side=tk.LEFT)
results_var = tk.StringVar(value=10)
results_menu = ttk.Combobox(options_frame, textvariable=results_var, values=[10, 20, 30, 40, 50], width=5)
results_menu.pack(side=tk.LEFT, padx=(5, 20))

counter_label = ttk.Label(options_frame, text="Queries: 0/100")
counter_label.pack(side=tk.LEFT, padx=10)

timer_label = ttk.Label(options_frame, text="Reset in: 00:00:00")
timer_label.pack(side=tk.LEFT)

# Country List and Codes (Country Name: (language_code, tld))
country_codes = {
    "Poland": ("pl", "pl"),
    "Germany": ("de", "de"),
    "United Kingdom": ("en", "uk"),
    "France": ("fr", "fr"),
    "Spain": ("es", "es"),
    "Italy": ("it", "it"),
    "Netherlands": ("nl", "nl"),
    "Belgium": ("nl", "be"),
    "Sweden": ("sv", "se"),
    "Norway": ("no", "no"),
    "Denmark": ("da", "dk"),
    "Finland": ("fi", "fi"),
    "Switzerland": ("de", "ch"),
    "Austria": ("de", "at"),
    "Portugal": ("pt", "pt"),
    "Ireland": ("en", "ie"),
    "Greece": ("el", "gr"),
    "Czech Republic": ("cs", "cz"),
    "Slovakia": ("sk", "sk"),
    "Hungary": ("hu", "hu"),
    "Romania": ("ro", "ro"),
    "Bulgaria": ("bg", "bg"),
    "Croatia": ("hr", "hr"),
    "Serbia": ("sr", "rs"),
    "Ukraine": ("uk", "ua"),
    "Lithuania": ("lt", "lt"),
    "Latvia": ("lv", "lv"),
    "Estonia": ("et", "ee"),
    "Slovenia": ("sl", "si"),
    "Iceland": ("is", "is"),
    "Albania": ("sq", "al"),
    "Bosnia and Herzegovina": ("bs", "ba"),
    "Kosovo": ("sq", "xk"),
    "North Macedonia": ("mk", "mk"),
    "Moldova": ("ro", "md"),
    "Montenegro": ("sr", "me")
}

country_var = tk.StringVar(value="Poland")
country_menu = ttk.Combobox(left_frame, textvariable=country_var, values=list(country_codes.keys()))
country_menu.pack(pady=5)
# Unfocus the combobox after selection
country_menu.bind("<<ComboboxSelected>>", lambda e: root.focus())

progress = ttk.Progressbar(left_frame, orient="horizontal", length=400, mode="determinate")
progress.pack(pady=5)

status_label = ttk.Label(left_frame, text="Ready")
status_label.pack()

start_button = ttk.Button(left_frame, text="Start Search", command=run_pipeline)
start_button.pack(pady=10)

# Right Side - Search History
history_frame = ttk.Frame(right_frame)
history_frame.pack(fill=tk.BOTH, expand=True)
ttk.Label(history_frame, text="Search History:").pack(anchor="w")

history_text = tk.Text(history_frame, wrap=tk.WORD, state=tk.DISABLED, height=5)
history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

history_scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=history_text.yview)
history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
history_text.config(yscrollcommand=history_scrollbar.set)

# Console Output Window
console_frame = ttk.Frame(right_frame)
console_frame.pack(fill=tk.BOTH, expand=True)
ttk.Label(console_frame, text="Debug Console:").pack(anchor="w", pady=(10, 0))

console_text = tk.Text(console_frame, wrap=tk.WORD, state=tk.DISABLED, height=10, bg="#2b2b2b", fg="#cccccc")
console_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

console_scrollbar = ttk.Scrollbar(console_frame, orient="vertical", command=console_text.yview)
console_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
console_text.config(yscrollcommand=console_scrollbar.set)

# Redirect console output (stdout) to the GUI Text widget
sys.stdout = ConsoleRedirect(console_text)

buttons_frame = ttk.Frame(right_frame)
buttons_frame.pack(pady=10)

open_file_button = ttk.Button(buttons_frame, text="Open .xlsx File", command=open_prospects_file)
open_file_button.pack(side=tk.LEFT, padx=5)

open_history_button = ttk.Button(buttons_frame, text="Open History .txt", command=open_history_file)
open_history_button.pack(side=tk.LEFT, padx=5)

# Initial load of history and start of timer
history_text.config(state=tk.NORMAL)
load_search_history()
history_text.config(state=tk.DISABLED)

update_timer_and_counter()
root.mainloop()