from __future__ import annotations
import re, time
from typing import List, Dict
from datetime import date
import pandas as pd

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from .base import build_driver, parse_date_from_attr, norm_time_24h, rows_to_df, REQUIRED_COLUMNS

COUNTRY = "Costa Rica"
BASE_URL = "https://cinepolis.co.cr/"

def _get_cinemas(driver) -> List[Dict[str, str]]:
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
    driver.get(cinema_url)
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(2)
    rows: List[Dict] = []

    date_items = driver.find_elements(By.CLASS_NAME, "movie-date")[1:9]  # skip first, limit 8
    for date_item in date_items:
        try:
            label = date_item.find_element(By.TAG_NAME, "label")
            dt: date = parse_date_from_attr(label.get_attribute("for"))
            if not dt:
                continue
        except NoSuchElementException:
            continue

        try:
            label.click()
            time.sleep(1.5)
        except Exception:
            continue

        projections = driver.find_elements(By.CLASS_NAME, "movie-projection")
        for proj in projections:
            try:
                title = proj.find_element(By.TAG_NAME, "h2").text.strip()
            except Exception:
                title = ""

            fmt = ""
            try:
                spans = proj.find_elements(By.TAG_NAME, "span")
                if spans:
                    parts = (spans[0].text or "").split("|")
                    if len(parts) >= 3:
                        fmt = parts[2].strip()
            except Exception:
                pass

            try:
                ul = proj.find_element(By.TAG_NAME, "ul")
            except Exception:
                continue

            for li in ul.find_elements(By.TAG_NAME, "li"):
                try:
                    lbl = li.find_element(By.TAG_NAME, "label")
                    m_time = re.search(r">([^<]+)<span", lbl.get_attribute("outerHTML") or "")
                    raw_time = m_time.group(1).strip() if m_time else lbl.text.strip()
                    rows.append({
                        "Country": COUNTRY,
                        "Theater": cinema_name,
                        "Date": dt,
                        "Time": norm_time_24h(raw_time),
                        "Movie": title,
                        "Format": fmt,
                    })
                except Exception:
                    continue
    return rows

def scrape(headless: bool = True) -> pd.DataFrame:
    driver = None
    try:
        driver = build_driver(headless=headless)
        rows: List[Dict] = []
        for cinema in _get_cinemas(driver):
            try:
                rows.extend(_scrape_cinema(driver, cinema["url"], cinema["name"]))
            except TimeoutException:
                continue
        return rows_to_df(rows)
    finally:
        if driver:
            driver.quit()
