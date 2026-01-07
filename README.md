# 🔍 Google Prospecting Tool

### *Automatyzacja pozyskiwania leadów B2B przy użyciu Google Custom Search API.*

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![Tkinter](https://img.shields.io/badge/UI-Tkinter-green?style=for-the-badge)
![Pandas](https://img.shields.io/badge/Data-Pandas-150458?style=for-the-badge&logo=pandas)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

---

## 🌟 O projekcie

**Google Prospecting Tool** to zaawansowana aplikacja desktopowa, która automatyzuje żmudny proces wyszukiwania kontaktów biznesowych. Program łączy wyniki wyszukiwania Google z silnikiem scrapującym, pozwalając na masowe pobieranie danych kontaktowych bezpośrednio do pliku Excel.



---

## ✨ Kluczowe funkcje

* 🚀 **Masowe wyszukiwanie:** Wprowadzaj wiele fraz naraz, a program zajmie się resztą.
* 📧 **Ekstrakcja kontaktów:** Automatyczne wykrywanie adresów e-mail oraz numerów telefonów na stronach internetowych.
* 🌍 **Globalny zasięg:** Wybór spośród ponad 30 krajów i języków wyszukiwania (w tym Polska, UK, Niemcy).
* 📊 **Eksport do Excela:** Wyniki są zapisywane w uporządkowanym pliku `.xlsx` z automatycznym usuwaniem duplikatów domen.
* 🛡️ **Zarządzanie limitami API:** Wbudowany licznik zapytań (100/dobę) z automatycznym resetem o godzinie 9:00 rano.
* 📜 **Historia wyszukiwania:** Podgląd poprzednich sesji i szybki dostęp do wygenerowanych plików.

---

## 🚀 Szybki Start

### Wymagania
* Python 3.10 lub nowszy.
* Własne klucze Google API (instrukcja poniżej).

### Instalacja

1. **Klonowanie repozytorium:**
   ```bash
   git clone [https://github.com/MichalGrecer/regon_apk.git](https://github.com/MichalGrecer/regon_apk.git)
   cd regon_apk 
    ```
2. **Instalacja zależności**
    ```bash
    pip install -r requirements.txt
    ```
3. **Uruchomienie programu:**
    ```bash
    python wyszukiwarka.py
    ```

---

## ⚙️ Konfiguracja Google API 
Przy pierwszym uruchomieniu aplikacja poprosi o podanie:

1. **Google API Key**
2. **Search Engine ID (CSE ID)**

Dane te zostaną bezpiecznie zapisane lokalnie w pliku api_config.txt, więc nie musisz ich wpisywać ponownie.


---


## 🖥️ Interfejs użytkownika

Aplikacja została zoptymalizowana do pracy w oknie o wymiarach 1120x720, co zapewnia wygodny podgląd zarówno parametrów wyszukiwania, jak i logów debugowania w konsoli.

* **Lewy panel:** Konfiguracja zapytań, wybór kraju i licznik limitów.
* **Prawy panel:** Historia wyszukiwania oraz podgląd pracy skryptu w czasie rzeczywistym.
