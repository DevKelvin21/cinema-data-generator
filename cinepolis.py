import os
import re
import time
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
)

# =========================
# Configuración Selenium
# =========================
def build_browser() -> webdriver.Chrome:
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    # idioma neutro LATAM
    opts.add_argument("--lang=es-419,es-ES;q=0.9")
    # user-agent realista
    opts.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    )
    # reducir señales de automatización
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    return webdriver.Chrome(options=opts)

# =========================
# Utilidades comunes
# =========================
def aceptar_cookies_si_aparecen(browser: webdriver.Chrome):
    posibles = [
        (By.ID, "onetrust-accept-btn-handler"),
        (By.CSS_SELECTOR, "button#onetrust-accept-btn-handler"),
        (By.CSS_SELECTOR, "button.ot-sdk-button"),
        (By.XPATH, "//button[contains(., 'Aceptar todas')]"),
        (By.XPATH, "//button[contains(., 'Aceptar')]"),
    ]
    for loc in posibles:
        try:
            WebDriverWait(browser, 3).until(EC.element_to_be_clickable(loc)).click()
            time.sleep(0.3)
            return
        except Exception:
            continue

def navegar_con_reintentos(browser: webdriver.Chrome, urls: List[str], intentos: int = 3, sleep_s: int = 2) -> str:
    last_err = None
    for url in urls:
        for i in range(1, intentos + 1):
            try:
                browser.get(url)
                WebDriverWait(browser, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(0.8)
                aceptar_cookies_si_aparecen(browser)
                return url
            except Exception as e:
                last_err = e
                time.sleep(sleep_s * i)
    raise last_err or Exception("No se pudo abrir ninguna URL base.")

def hoy_str() -> str:
    # yyyy/mm/dd (consistente con tu salida)
    return date.today().strftime("%Y/%m/%d")

def to_yyyy_mm_dd_from_label(text: str) -> Optional[str]:
    """
    Deriva yyyy/mm/dd desde 'Hoy', 'Mañana' o 'dd/mm'.
    """
    t = (text or "").strip()
    if not t:
        return None
    tl = t.lower()

    if "hoy" in tl:
        return hoy_str()
    if "mañana" in tl:
        d = date.today() + timedelta(days=1)
        return d.strftime("%Y/%m/%d")

    m = re.search(r"(\d{1,2})/(\d{1,2})", t)
    if m:
        day, month = int(m.group(1)), int(m.group(2))
        year = date.today().year
        return f"{year:04d}/{month:02d}/{day:02d}"

    return None

def to_yyyy_mm_dd_from_for_attr(for_attr: str) -> Optional[str]:
    """
    Convierte for='field-movie-date-YYYY-MM-DD' a yyyy/mm/dd.
    """
    if not for_attr:
        return None
    m = re.search(r"field-movie-date-(\d{4})-(\d{2})-(\d{2})", for_attr)
    if not m:
        return None
    return f"{m.group(1)}/{m.group(2)}/{m.group(3)}"

# =========================
# Países y URLs base
# =========================
COUNTRIES = [
    {
        "PAIS": "Honduras",
        "BASE_URLS": [
            "https://cinepolis.com.hn/",
            "https://www.cinepolis.com.hn/",
            "http://cinepolis.com.hn/",
        ],
    },
    {
        "PAIS": "El Salvador",
        "BASE_URLS": [
            "https://cinepolis.com.sv/",
            "https://www.cinepolis.com.sv/",
            "http://cinepolis.com.sv/",
        ],
    },
    {
        "PAIS": "Costa Rica",
        "BASE_URLS": [
            "https://cinepolis.co.cr/",
            "https://www.cinepolis.co.cr/",
            "http://cinepolis.co.cr/",
        ],
    },
    {
        "PAIS": "Guatemala",
        "BASE_URLS": [
            "https://cinepolis.com.gt/",
            "https://www.cinepolis.com.gt/",
            "http://cinepolis.com.gt/",
        ],
    },
    {
        "PAIS": "Panamá",
        "BASE_URLS": [
            "https://cinepolis.com.pa/",
            "https://www.cinepolis.com.pa/",
            "http://cinepolis.com.pa/",
        ],
    }
]

# =========================
# Extracción: lista de cines
# =========================
def obtener_cines(browser: webdriver.Chrome, base_urls: List[str]) -> List[Dict[str, str]]:
    navegar_con_reintentos(browser, base_urls)

    cines: List[Dict[str, str]] = []

    # Estrategia A: tarjetas con clase "Cinema_cinema..."
    try:
        tarjetas = browser.find_elements(By.CSS_SELECTOR, "[class*='Cinema_cinema']")
        for cine in tarjetas:
            try:
                a = cine.find_element(By.TAG_NAME, "a")
                nombre = (a.get_attribute("data-site-name") or a.text or "").strip()
                href = a.get_attribute("href")
                if nombre and href and nombre.lower() != "todo":
                    cines.append({"nombre": nombre, "url": href})
            except Exception:
                continue
    except Exception:
        pass

    # Estrategia B: cualquier <a> que parezca apuntar a detalle de cine
    if not cines:
        for a in browser.find_elements(By.TAG_NAME, "a"):
            try:
                href = a.get_attribute("href") or ""
                txt = (a.get_attribute("data-site-name") or a.text or "").strip()
                if not href:
                    continue
                if ("cine" in href.lower() or "cines" in href.lower()) and txt and txt.lower() not in ("", "todo", "ver todos"):
                    cines.append({"nombre": txt, "url": href})
            except Exception:
                continue

    # Deduplicar por URL
    vistos, unicos = set(), []
    for c in cines:
        if c["url"] not in vistos:
            vistos.add(c["url"])
            unicos.append(c)
    return unicos

# =========================
# Enumerar fechas visibles (tabs)
# =========================
def enumerar_fechas(browser: webdriver.Chrome, max_days: int = 7) -> List[Tuple[Optional[webdriver.remote.webelement.WebElement], str]]:
    """
    Devuelve [(elemento_clickable_o_None, 'yyyy/mm/dd')] para todas las fechas
    visibles (hasta max_days). Si no encuentra tabs, devuelve solo [(None, hoy)].
    """
    candidatos: List[Tuple[Optional[webdriver.remote.webelement.WebElement], str]] = []

    try:
        elems = []
        # contenedores típicos
        elems.extend(browser.find_elements(By.CSS_SELECTOR, ".movie-date label"))
        elems.extend(browser.find_elements(By.CSS_SELECTOR, ".movie-date"))
        # genéricos
        elems.extend(browser.find_elements(By.TAG_NAME, "button"))
        elems.extend(browser.find_elements(By.TAG_NAME, "label"))

        vistos = set()
        for el in elems:
            try:
                f = None
                for_attr = el.get_attribute("for")
                if for_attr:
                    f = to_yyyy_mm_dd_from_for_attr(for_attr)
                if not f:
                    f = to_yyyy_mm_dd_from_label(el.text)
                if not f or f in vistos:
                    continue
                vistos.add(f)
                candidatos.append((el, f))
            except Exception:
                continue
    except Exception:
        pass

    if not candidatos:
        return [(None, hoy_str())]

    try:
        candidatos.sort(key=lambda t: datetime.strptime(t[1], "%Y/%m/%d"))
    except Exception:
        pass
    return candidatos[:max_days]

# =========================
# Extracción: funciones (todas las fechas visibles)
# =========================
def scrapear_funciones_cine(browser: webdriver.Chrome, cine_url: str, cine_nombre: str, pais: str) -> List[Dict[str, str]]:
    navegar_con_reintentos(browser, [cine_url], intentos=2)

    funciones: List[Dict[str, str]] = []
    fechas = enumerar_fechas(browser, max_days=7) or [(None, hoy_str())]

    for el, fecha_str in fechas:
        if el is not None:
            try:
                WebDriverWait(browser, 4).until(EC.element_to_be_clickable(el)).click()
                time.sleep(1.2)
            except Exception:
                pass

        # Encontrar bloques de película (varias heurísticas)
        estrategias_bloques = [
            (By.CLASS_NAME, "movie-projection"),
            (By.CSS_SELECTOR, "section[class*='movie-card'], div[class*='movie-card']"),
            (By.CSS_SELECTOR, "div[class*='MovieCard']"),
        ]
        bloques = []
        for by, sel in estrategias_bloques:
            try:
                bloques = browser.find_elements(by, sel)
                if bloques:
                    break
            except Exception:
                continue

        for peli in bloques:
            try:
                # Título
                titulo = ""
                for loc in [(By.TAG_NAME, "h2"), (By.TAG_NAME, "h3"), (By.CSS_SELECTOR, ".movie-title, [class*='title']")]:
                    try:
                        el_t = peli.find_element(*loc)
                        if el_t.text.strip():
                            titulo = el_t.text.strip()
                            break
                    except Exception:
                        continue
                if not titulo:
                    titulo = (peli.get_attribute("aria-label") or "").strip() or "(Sin título)"

                # Formato (heurística)
                formato = ""
                try:
                    txt = peli.text
                    for token in ["IMAX", "4DX", "3D", "2D", "PLF"]:
                        if token in txt:
                            formato = token
                            break
                except Exception:
                    pass

                # Horarios
                horarios = []
                for by, sel in [
                    (By.CSS_SELECTOR, "ul li label"),
                    (By.CSS_SELECTOR, "a[href*='compra'], a[href*='checkout'], a[href*='showtime']"),
                    (By.CSS_SELECTOR, "button[aria-label*='Horario'], button.time, a.time"),
                ]:
                    try:
                        horarios = peli.find_elements(by, sel)
                        if horarios:
                            break
                    except Exception:
                        continue

                for h in horarios:
                    try:
                        outer = h.get_attribute("outerHTML") or ""
                        m = re.search(r">([^<]+)<span", outer)
                        hora_raw = m.group(1).strip() if m else (h.text or "").strip()

                        # Normalizar a HH:MM si se puede
                        hora_fmt = hora_raw
                        try:
                            hora_obj = datetime.strptime(hora_raw, "%H:%M").time()
                            hora_fmt = hora_obj.strftime("%H:%M")
                        except Exception:
                            try:
                                hora_obj = datetime.strptime(hora_raw.upper().replace(".", ""), "%I:%M %p").time()
                                hora_fmt = hora_obj.strftime("%H:%M")
                            except Exception:
                                pass

                        funciones.append(
                            {
                                "Country": pais,
                                "Theater": cine_nombre,
                                "Date": fecha_str,   # <- clave: fecha de la pestaña
                                "Time": hora_fmt,
                                "Movie": titulo,
                                "Format": formato,
                            }
                        )
                    except StaleElementReferenceException:
                        continue
                    except Exception:
                        continue
            except Exception:
                continue

    return funciones

# =========================
# Main
# =========================
def main():
    browser = build_browser()
    try:
        todas: List[Dict[str, str]] = []
        for cfg in COUNTRIES:
            pais = cfg["PAIS"]
            base_urls = cfg["BASE_URLS"]
            try:
                cines = obtener_cines(browser, base_urls)
            except Exception as e:
                print(f"[{pais}] No se pudo cargar la lista de cines: {e}")
                cines = []

            if not cines:
                print(f"[{pais}] Sin cines detectados (revisa selectores).")
                continue

            for cine in cines:
                try:
                    funcs = scrapear_funciones_cine(browser, cine["url"], cine["nombre"], pais)
                    todas.extend(funcs)
                except Exception as e:
                    print(f"[{pais}] Error al scrapear {cine['nombre']}: {e}")

        out_path = "cinepolis.xlsx"
        cols = ["Country", "Theater", "Date", "Time", "Movie", "Format"]

        if todas:
            df_all = pd.DataFrame(todas)

            # Split: Today vs Other schedules (usando columna "Date")
            today = hoy_str()
            df_today = df_all[df_all["Date"] == today].copy()
            df_other = df_all[df_all["Date"] != today].copy()

            # Asegurar columnas y orden
            for df in (df_today, df_other):
                for c in cols:
                    if c not in df.columns:
                        df[c] = ""
                df = df[cols]

            with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
                df_today[cols].to_excel(writer, index=False, sheet_name="Today")
                df_other[cols].to_excel(writer, index=False, sheet_name="Other schedules")
            print(f"Archivo generado: {out_path} — Today: {len(df_today)} filas, Other: {len(df_other)} filas")
        else:
            # Crear libro con dos hojas vacías por consistencia
            with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
                pd.DataFrame(columns=cols).to_excel(writer, index=False, sheet_name="Today")
                pd.DataFrame(columns=cols).to_excel(writer, index=False, sheet_name="Other schedules")
            print("No se encontraron funciones. Se generó el archivo con hojas vacías.")

    finally:
        try:
            browser.quit()
        except Exception:
            pass

if __name__ == "__main__":
    main()