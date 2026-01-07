import tkinter as tk
from tkinter import ttk, messagebox, filedialog
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
import webbrowser 

# =======================
# API and Limit Configuration
# =======================
MAX_RESULTS_PER_QUERY = 100
SEARCH_HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "search_history.txt")
QUERIES_COUNT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "query_counter.txt")
# Plik konfiguracyjny do zapisu kluczy API
API_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_config.txt")
DATE_FORMAT = "%Y-%m-%d %H:%M:%S" 

# =======================
# Global Variables for API Keys (will be populated on load or input)
# =======================
GLOBAL_API_KEY = ""
GLOBAL_CSE_ID = ""


# =======================
# Working Folder
# =======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "Search_Results")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# =======================
# Key Persistence Functions
# =======================
def save_api_keys(api_key, cse_id):
    """Saves API keys to a local file."""
    try:
        with open(API_CONFIG_FILE, "w") as f:
            f.write(f"API_KEY={api_key}\n")
            f.write(f"CSE_ID={cse_id}\n")
        return True
    except Exception as e:
        print(f"Error saving API keys: {e}")
        return False

def load_api_keys():
    """Loads API keys from a local file and sets global variables."""
    keys = {"API_KEY": "", "CSE_ID": ""}
    try:
        with open(API_CONFIG_FILE, "r") as f:
            for line in f:
                if line.startswith("API_KEY="):
                    keys["API_KEY"] = line.split("=")[1].strip()
                elif line.startswith("CSE_ID="):
                    keys["CSE_ID"] = line.split("=")[1].strip()
    except FileNotFoundError:
        pass
    
    # Ustawienie zmiennych globalnych
    global GLOBAL_API_KEY, GLOBAL_CSE_ID
    GLOBAL_API_KEY = keys["API_KEY"]
    GLOBAL_CSE_ID = keys["CSE_ID"]
    
    return keys


# =======================
# API Key Input Window (MODAL DIALOG)
# =======================

def check_and_require_api_keys():
    """Checks for saved keys and opens the input dialog if they are missing."""
    # 1. Wczytanie kluczy
    keys = load_api_keys()
    
    # 2. Sprawdzenie, czy klucze są puste (jeśli są, wychodzi z funkcji)
    if keys["API_KEY"] and keys["CSE_ID"]:
        return
    
    # 3. Jeśli klucze są puste, wyświetlenie okna dialogowego
    
    # Tworzenie nowego okna TopLevel
    dialog = tk.Toplevel(root)
    dialog.title("Required: Google API Credentials")
    # Dopasowanie rozmiaru do zawartości
    dialog.geometry("400x160") 
    
    # Ustawienie, aby okno było modalne (blokuje interakcję z głównym oknem)
    dialog.transient(root)
    dialog.grab_set() 
    
    frame = ttk.Frame(dialog, padding=10)
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(frame, text="Google API Key:").grid(row=0, column=0, sticky="w", pady=5, padx=5)
    api_entry = ttk.Entry(frame, show='*', width=40) # Pole na klucz jest ukryte
    api_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=5)
    
    ttk.Label(frame, text="CSE ID:").grid(row=1, column=0, sticky="w", pady=5, padx=5)
    cse_entry = ttk.Entry(frame, width=40)
    cse_entry.grid(row=1, column=1, sticky="ew", pady=5, padx=5)
    
    frame.grid_columnconfigure(1, weight=1)

    # Funkcja do obsługi zapisu kluczy
    def submit_keys():
        api_key = api_entry.get().strip()
        cse_id = cse_entry.get().strip()

        if api_key and cse_id:
            if save_api_keys(api_key, cse_id):
                # Ustawienie kluczy globalnych i zamknięcie okna
                global GLOBAL_API_KEY, GLOBAL_CSE_ID
                GLOBAL_API_KEY = api_key
                GLOBAL_CSE_ID = cse_id
                messagebox.showinfo("Success", "API keys saved and loaded.")
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Could not save keys to file.")
        else:
            messagebox.showwarning("Warning", "Please enter both API Key and CSE ID.")

    submit_button = ttk.Button(frame, text="Save and Continue", command=submit_keys)
    submit_button.grid(row=2, column=0, columnspan=2, pady=10)

    # Wymuś oczekiwanie na zamknięcie okna. Używamy lambda: None, aby zablokować zamknięcie krzyżykiem
    # i zmusić użytkownika do wprowadzenia danych lub zamknięcia całego programu
    dialog.protocol("WM_DELETE_WINDOW", lambda: None) 
    root.wait_window(dialog)

    # Po zamknięciu dialogu, jeśli klucze nadal są puste, zamykamy program
    if not GLOBAL_API_KEY or not GLOBAL_CSE_ID:
        root.destroy()
        sys.exit()


# =======================
# Helper Functions (Query Counter, History, etc.)
# =======================
def get_query_count():
    """Retrieves the query counter from file or resets it if 9:00 AM has passed."""
    now = datetime.now()
    try:
        with open(QUERIES_COUNT_FILE, "r") as f:
            lines = f.readlines()
            last_date_str = lines[0].strip()
            count = int(lines[1].strip())
            
            last_date = datetime.strptime(last_date_str, DATE_FORMAT)

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
        f.write(now.strftime(DATE_FORMAT) + "\n")
        f.write(str(count) + "\n")


def reset_query_count():
    """Resets the query counter."""
    now = datetime.now()
    with open(QUERIES_COUNT_FILE, "w") as f:
        f.write(now.strftime(DATE_FORMAT) + "\n")
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
PHONE_RE = re.compile(r"(?:\+?\d{2}\s*)?(\d{3}[\s-]?\d{3}[\s-]?\d{3}|\d{9})")

warning_displayed = False

def search_with_api(query, lang_code, num_results, tld):
    """Searches for links on Google using the API, using global keys."""
    global warning_displayed
    global GLOBAL_API_KEY, GLOBAL_CSE_ID
    
    if not GLOBAL_API_KEY or not GLOBAL_CSE_ID:
        # Ten warunek nie powinien być osiągnięty, jeśli check_and_require_api_keys zadziałało
        root.after(0, lambda: messagebox.showerror("Błąd API", "Brak kluczy Google API Key i CSE ID."))
        return []
        
    links = []
    queries_to_make = (num_results + 9) // 10

    current_count = get_query_count()
    if current_count + queries_to_make > 100:
        root.after(0, lambda: messagebox.showerror("Query Limit", "Daily limit of 100 API queries reached."))
        return []

    for i in range(queries_to_make):
        start_index = i * 10 + 1
        url = f"https://www.googleapis.com/customsearch/v1?key={GLOBAL_API_KEY}&cx={GLOBAL_CSE_ID}&q={query}&gl={tld}&hl={lang_code}&start={start_index}"

        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            results = response.json()

            if 'items' in results:
                for item in results['items']:
                    links.append({"query": query, "url": item['link']})

            current_count += 1
            update_query_count(current_count)
            
            root.after(0, lambda count=current_count: counter_label.config(text=f"Queries: {count}/100"))
            
            if current_count >= 70 and not warning_displayed:
                root.after(0, lambda: messagebox.showwarning("Uwaga: Limit Zapytania", "Zostało 30 zapytań."))
                warning_displayed = True
            
            if current_count >= 100:
                root.after(0, lambda: messagebox.showerror("Query Limit", "Dzienny limit 100 API queries osiągnięty."))
                break


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
    """Extracts contact details from HTML."""
    if not html:
        return {"emails": "", "phones": "", "description": "", "contact_links": ""}
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True)
    emails = set(EMAIL_RE.findall(text))

    phones = set()
    all_numbers = PHONE_RE.findall(text)

    for num in all_numbers:
        clean_num = num.replace(" ", "").replace("-", "")
        if not ZIP_CODE_RE.search(num) and len(clean_num) >= 9:
            phones.add(num)

    desc = ""
    d = soup.find("meta", {"name": "description"}) or soup.find("meta", {"property": "og:description"})
    if d and d.get("content"):
        desc = d.get("content").strip()

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
        if links is None:
            return

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
    next_reset = datetime(now.year, now.month, now.day, 9, 0, 0)
    if now.hour >= 9:
        next_reset += timedelta(days=1)

    time_left = next_reset - now
    hours, remainder = divmod(time_left.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    timer_label.config(text=f"Reset in: {hours:02d}:{minutes:02d}:{seconds:02d}")

    query_count = get_query_count()
    counter_label.config(text=f"Queries: {query_count}/100")

    root.after(1000, update_timer_and_counter)


def run_pipeline():
    """Starts the main process function in a separate thread."""
    global warning_displayed
    
    # Sprawdzenie, czy klucze zostały załadowane 
    if not GLOBAL_API_KEY or not GLOBAL_CSE_ID:
        messagebox.showerror("Błąd Uruchomienia", "Brak kluczy API. Uruchom ponownie i wprowadź klucze.")
        return

    warning_displayed = False
    
    # 1. Pobranie zapytań tekstowych
    queries_text = queries_entry.get("1.0", tk.END).strip()
    queries = [q.strip() for q in queries_text.split("\n") if q.strip()]
        
    if not queries:
        messagebox.showwarning("Warning", "Please enter at least one search phrase.")
        return
    
    selected_country = country_var.get()
    lang_code, tld = country_codes.get(selected_country, ("pl", "pl"))

    def start_process():
        process_queries_and_links(queries, lang_code, tld)

    t = threading.Thread(target=start_process)
    t.start()


# =======================
# Console Redirection Class
# =======================
class ConsoleRedirect:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
        self.text_widget.config(state=tk.DISABLED)

    def flush(self):
        pass


# =======================
# GUI Setup
# =======================
root = tk.Tk()
root.title("Prospecting Tool - Google API")
# Używam zapamiętanej przez Ciebie geometrii:
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


# --- Usunięto: Sekcja Image Search Integration ---
ttk.Label(left_frame, text="--- Search Options ---").pack(anchor="w", pady=(10, 0))


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
    "Poland": ("pl", "pl"), "Germany": ("de", "de"), "United Kingdom": ("en", "uk"),
    "France": ("fr", "fr"), "Spain": ("es", "es"), "Italy": ("it", "it"),
    "Netherlands": ("nl", "nl"), "Belgium": ("nl", "be"), "Sweden": ("sv", "se"),
    "Norway": ("no", "no"), "Denmark": ("da", "dk"), "Finland": ("fi", "fi"),
    "Switzerland": ("de", "ch"), "Austria": ("de", "at"), "Portugal": ("pt", "pt"),
    "Ireland": ("en", "ie"), "Greece": ("el", "gr"), "Czech Republic": ("cs", "cz"),
    "Slovakia": ("sk", "sk"), "Hungary": ("hu", "hu"), "Romania": ("ro", "ro"),
    "Bulgaria": ("bg", "bg"), "Croatia": ("hr", "hr"), "Serbia": ("sr", "rs"),
    "Ukraine": ("uk", "ua"), "Lithuania": ("lt", "lt"), "Latvia": ("lv", "lv"),
    "Estonia": ("et", "ee"), "Slovenia": ("sl", "si"), "Iceland": ("is", "is"),
    "Albania": ("sq", "al"), "Bosnia and Herzegovina": ("bs", "ba"), "Kosovo": ("sq", "xk"),
    "North Macedonia": ("mk", "mk"), "Moldova": ("ro", "md"), "Montenegro": ("sr", "me")
}

country_var = tk.StringVar(value="Poland")
country_menu = ttk.Combobox(left_frame, textvariable=country_var, values=list(country_codes.keys()))
country_menu.pack(pady=5)
country_menu.bind("<<ComboboxSelected>>", lambda e: root.focus())

# Informacja, że klucze są wczytane 
ttk.Label(left_frame, text="--- API Keys Loaded ---").pack(anchor="w", pady=(10, 0))


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

sys.stdout = ConsoleRedirect(console_text)

buttons_frame = ttk.Frame(right_frame)
buttons_frame.pack(pady=10)

open_file_button = ttk.Button(buttons_frame, text="Open .xlsx File", command=open_prospects_file)
open_file_button.pack(side=tk.LEFT, padx=5)

open_history_button = ttk.Button(buttons_frame, text="Open History .txt", command=open_history_file)
open_history_button.pack(side=tk.LEFT, padx=5)


# --- INITIALIZATION LOGIC ---

# Sprawdzenie i wymuszenie wprowadzenia kluczy API, jeśli są nieobecne
check_and_require_api_keys()

# Wczytanie historii i uruchomienie timera
history_text.config(state=tk.NORMAL)
load_search_history()
history_text.config(state=tk.DISABLED)

update_timer_and_counter()
root.mainloop()