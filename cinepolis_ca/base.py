from __future__ import annotations
import os, re, time
from typing import Dict, List, Optional
from datetime import datetime, date
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

REQUIRED_COLUMNS = ["Country", "Theater", "Date", "Time", "Movie", "Format"]

def build_driver(headless: bool = True) -> webdriver.Chrome:
    """Create a Chrome driver with sensible defaults (headless by default)."""
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1920,1080")
    else:
        opts.add_argument("--start-maximized")

    # stability / noise
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--disable-infobars")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-popup-blocking")
    opts.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging", "enable-cloud-services"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--log-level=3")

    # driver path: env or local
    driver_path = os.environ.get("CHROMEDRIVER")
    if not driver_path:
        exe = "chromedriver.exe" if os.name == "nt" else "chromedriver"
        candidate = os.path.join(os.getcwd(), exe)
        driver_path = candidate if os.path.exists(candidate) else exe

    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=opts)
    driver.set_page_load_timeout(60)
    driver.set_script_timeout(30)
    return driver

def parse_date_from_attr(for_attr: str) -> Optional[date]:
    """
    Accepts attrs like 'field-movie-date-YYYY-MM-DD' and returns python date.
    """
    if not for_attr:
        return None
    m = re.search(r"field-movie-date-(\d{4})-(\d{2})-(\d{2})", for_attr)
    if not m:
        return None
    return datetime.strptime(f"{m.group(1)}-{m.group(2)}-{m.group(3)}", "%Y-%m-%d").date()

def norm_time_24h(raw: str) -> str:
    """Try to return HH:MM, else original raw."""
    raw = (raw or "").strip()
    try:
        return datetime.strptime(raw, "%H:%M").strftime("%H:%M")
    except Exception:
        # try HH.MM or H:MM am/pm patterns if some sites use them
        try:
            return datetime.strptime(raw.replace(".", ":"), "%H:%M").strftime("%H:%M")
        except Exception:
            return raw

def rows_to_df(rows: List[Dict]) -> pd.DataFrame:
    """Create DataFrame with required columns and drop rows missing Date."""
    df = pd.DataFrame(rows, columns=REQUIRED_COLUMNS)
    if not df.empty:
        df = df.dropna(subset=["Date"])
    return df
