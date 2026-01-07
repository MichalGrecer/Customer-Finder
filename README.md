# 🔍 B2B Lead Generator

### *Automating B2B Lead Acquisition using Google Custom Search API.*

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![Tkinter](https://img.shields.io/badge/UI-Tkinter-green?style=for-the-badge)
![Pandas](https://img.shields.io/badge/Data-Pandas-150458?style=for-the-badge&logo=pandas)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

---

## 🌟 About the Project

**Google Prospecting Tool** is an advanced desktop application designed to automate the tedious process of searching for business contacts. The program merges Google search results with a powerful scraping engine, allowing for bulk extraction of contact data directly into an Excel file.

---

## ✨ Key Features

* 🚀 **Bulk Search:** Enter multiple search phrases at once and let the program handle the rest.
* 📧 **Contact Extraction:** Automatically detects email addresses and phone numbers on target websites.
* 🌍 **Global Reach:** Choose from over 30 countries and search languages (including Poland, UK, Germany, and more).
* 📊 **Excel Export:** Results are saved in an organized `.xlsx` file with automatic domain de-duplication.
* 🛡️ **API Limit Management:** Built-in query counter (100/day) with an automatic reset at 9:00 AM.
* 📜 **Search History:** Preview previous sessions and gain quick access to generated files.

---

## 🚀 Quick Start

### Prerequisites
* Python 3.10 or newer.
* Personal Google API Credentials (see instructions below).

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/MichalGrecer/regon_apk.git
   cd regon_apk
    ```
2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3. **Run the program:**
    ```bash
    python wyszukiwarka.py
    ```

---

## ⚙️ Google API Configuration
Upon the first launch, the application will prompt you to provide:

1. **Google API Key**
2. **Search Engine ID (CSE ID)**

This data is securely saved locally in the api_config.txt file, so you won't need to enter it again.


---


## 🖥️ User Interface

The application is optimized for a window size of 1120x720, providing a comfortable view of both search parameters and real-time debug logs in the console.

* **Left Panel:** Query configuration, country selection, and limit tracking.
* **Right Panel:** Search history and real-time script execution preview.

## 📂 Project Structure

* wyszukiwarka.py - Main source code.
* Search_Results/ - Folder where your prospects.xlsx will be generated.
* api_config.txt - (Generated) Stores your credentials.
* query_counter.txt - (Generated) Tracks your daily 100-query limit.
* search_history.txt - (Generated) Logs your search phrases.
