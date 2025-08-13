from __future__ import annotations

import re, time
from typing import List, Dict
import pandas as pd

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from .base import build_driver, parse_date_from_attr, norm_time_24h, rows_to_df, REQUIRED_COLUMNS

COUNTRY = "Honduras"
BASE_URL = "https://cinepolis.com.hn/"

def _get_cinemas(driver) -> List[Dict[str, str]]:
    """Return list of {'name':..., 'url':...} for all cinemas (except 'todo')."""
    driver.get(BASE_URL)
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(2)

    cinemas = []
    for el in driver.find_elements(By.CLASS_NAME, "Cinema_cinema__3mgID"):
        a = el.find_element(By.TAG_NAME, "a")
        name = (a.get_attribute("data-site-name") or "").strip()
        href = a.get_attribute("href")
        if name and href and name.lower() != "todo":
            cinemas.append({"name": name, "url": href})
    return cinemas

def _scrape_cinema(driver, cinema_url: str, cinema_name: str) -> List[Dict]:
    """Scrape up to 'today + 7' dates for one cinema."""
    driver.get(cinema_url)
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(2)

    rows: List[Dict] = []

    # Date pills (skip possible header; keep first 8 = today + 7)
    date_items = driver.find_elements(By.CLASS_NAME, "movie-date")
    date_items = date_items[1:9] if len(date_items) > 1 else date_items

    for date_item in date_items:
        try:
            label = date_item.find_element(By.TAG_NAME, "label")
            dt = parse_date_from_attr(label.get_attribute("for"))
            if not dt:
                continue
        except NoSuchElementException:
            continue

        # Click date to load showtimes
        try:
            label.click()
            time.sleep(1.5)
        except Exception:
            continue

        # Movie blocks
        projections = driver.find_elements(By.CLASS_NAME, "movie-projection")
        for proj in projections:
            # Title
            try:
                title = proj.find_element(By.TAG_NAME, "h2").text.strip()
            except Exception:
                title = ""

            # Format (often "... | ... | Format" in first span)
            fmt = ""
            try:
                spans = proj.find_elements(By.TAG_NAME, "span")
                if spans:
                    parts = (spans[0].text or "").split("|")
                    if len(parts) >= 3:
                        fmt = parts[2].strip()
            except Exception:
                pass

            # Times inside <ul><li><label>
            try:
                ul = proj.find_element(By.TAG_NAME, "ul")
            except Exception:
                continue

            for li in ul.find_elements(By.TAG_NAME, "li"):
                try:
                    lbl = li.find_element(By.TAG_NAME, "label")
                    # Extract visible time text
                    m_time = re.search(r">([^<]+)<span", lbl.get_attribute("outerHTML") or "")
                    raw_time = m_time.group(1).strip() if m_time else lbl.text.strip()

                    rows.append({
                        "Country": COUNTRY,
                        "Theater": cinema_name,
                        "Date": dt,                         # python date object
                        "Time": norm_time_24h(raw_time),    # "HH:MM" when possible
                        "Movie": title,
                        "Format": fmt,
                    })
                except Exception:
                    continue

    return rows

def scrape(headless: bool = True) -> pd.DataFrame:
    """
    Public entrypoint used by the orchestrator (cinepolis.py).

    Returns a DataFrame with columns:
    ['Country', 'Theater', 'Date', 'Time', 'Movie', 'Format']
    """
    driver = None
    try:
        driver = build_driver(headless=headless)
        rows: List[Dict] = []
        for cinema in _get_cinemas(driver):
            try:
                rows.extend(_scrape_cinema(driver, cinema["url"], cinema["name"]))
            except TimeoutException:
                # If one cinema fails/times out, continue with the next
                continue
        return rows_to_df(rows)
    finally:
        if driver:
            driver.quit()
