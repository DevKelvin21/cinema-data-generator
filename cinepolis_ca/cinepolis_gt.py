import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, StaleElementReferenceException
import pandas as pd

def _first_text(el, selectors):
    """Return el.text for the first selector that exists; else ''."""
    from selenium.common.exceptions import NoSuchElementException
    for sel in selectors:
        try:
            t = el.find_element(By.CSS_SELECTOR, sel).text.strip()
            if t:
                return t
        except NoSuchElementException:
            continue
    return ""

# URL for Cinepolis Guatemala
CINEPOLIS_URL = "https://cinepolis.com.gt/"

class ScraperCinepolisGuatemala:
    def __init__(self, ruta_driver):
        """
        Inicializa el scraper con la configuración básica.
        """
        self.pais = "Guatemala"
        self.url = CINEPOLIS_URL
        self.driver = None
        self.cine_actual = ""
        self.ciudad_actual = ""
        self.lista_ciudades = []
        self.lista_cines = []
        self.ruta_driver = ruta_driver
        self.df_hoy = pd.DataFrame()
        self.df_proximos = pd.DataFrame()
        self.configurar_navegador()
        
    def configurar_navegador(self):
        """Configura el navegador Chrome con opciones para scraping robusto."""
        chrome_options = Options()
        # Configuraciones para evitar detección y mejorar rendimiento
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-direct-composition")
        chrome_options.add_argument("--disable-features=VoiceTranscription,SpeechRecognition")
        chrome_options.add_argument("--disable-speech-api")
        chrome_options.add_argument("--disable-gcm")
        chrome_options.add_argument("--disable-sync")
        chrome_options.add_argument("--disable-machine-learning-model-downloader")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation', 'enable-cloud-services'])
        try:
            service = Service(self.ruta_driver)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(60)
            self.driver.set_script_timeout(30)
        except WebDriverException as e:
            raise RuntimeError(f"Error al iniciar el navegador: {str(e)}")
    
    def cerrar_popup_video(self):
        """Cierra el popup de video que aparece al cargar la página."""
        try:
            close_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#takeover-close")))
            close_button.click()
            time.sleep(1)
            return True
        except (TimeoutException, NoSuchElementException):
            return False
        except Exception as e:
            print(f"Error al intentar cerrar el popup de video: {str(e)}")
            return False
    
    def navegar_a_pagina_principal(self):
        """Navega a la página principal de Cinepolis y cierra popups."""
        try:
            self.driver.get(self.url)
            time.sleep(1)
            
            # Cerrar popups si existen
            self.cerrar_popup_video()
            
            return True
        except Exception as e:
            print(f"Error navegando a la página principal: {str(e)}")
            return False
    
    def obtener_lista_ciudades(self):
        """Obtiene y muestra la lista de ciudades disponibles."""
        try:
            # Limpiar la lista existente
            self.lista_ciudades = []
            
            # Esperar a que el selector de ciudades esté disponible
            select_ciudad = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "ciudad"))
            )
            
            # Obtener todas las opciones de ciudad
            opciones_ciudad = select_ciudad.find_elements(By.TAG_NAME, "option")
            
            for opcion in opciones_ciudad[1:]:  # Saltamos el primer elemento que es "Selecciona una ciudad"
                ciudad = {
                    "nombre": opcion.text,
                    "value": opcion.get_attribute("value")
                }
                self.lista_ciudades.append(ciudad)
            
            # Mostrar ciudades como array
            ciudades_array = [ciudad['nombre'] for ciudad in self.lista_ciudades]
            
            return True
        except Exception as e:
            print(f"Error obteniendo lista de ciudades: {str(e)}")
            return False
    
    def obtener_lista_cines(self):
        """Obtiene y muestra la lista de cines disponibles para la ciudad seleccionada."""
        try:
            # Limpiar la lista existente
            self.lista_cines = []
            
            select_cine = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "cine"))
            )
            opciones_cine = select_cine.find_elements(By.TAG_NAME, "option")
            
            for opcion in opciones_cine[1:]:  # Saltamos el primer elemento que es "Selecciona un cine"
                cine = {
                    "nombre": opcion.text,
                    "value": opcion.get_attribute("value")
                }
                self.lista_cines.append(cine)
            
            # Mostrar cines como array
            cines_array = [cine['nombre'] for cine in self.lista_cines]
            
            return True
        except Exception as e:
            print(f"Error obteniendo lista de cines: {str(e)}")
            return False
    
    def obtener_nombre_cine_actual(self):
        """Obtiene el nombre del cine actualmente mostrado en la página."""
        try:
            cine_element = self.driver.find_element(By.CSS_SELECTOR, ".complejo p")
            return cine_element.text
        except NoSuchElementException:
            return ""
    
    def esperar_cambio_de_cine(self, nombre_cine_esperado, timeout=15):
        """Espera a que el nombre del cine en la página coincida con el esperado."""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: self.obtener_nombre_cine_actual() == nombre_cine_esperado
            )
            return True
        except TimeoutException:
            return False
    
    def seleccionar_ciudad_y_cine(self, ciudad, cine):
        """Selecciona una ciudad y un cine específico."""
        try:
            # Actualizar la ciudad actual inmediatamente
            self.ciudad_actual = ciudad["nombre"]
            
            # Seleccionar ciudad
            select_ciudad = Select(self.driver.find_element(By.ID, "ciudad"))
            select_ciudad.select_by_value(ciudad["value"])
            time.sleep(3)  # Esperar a que se actualice la página
            
            # Obtener lista de cines actualizada
            if not self.obtener_lista_cines():
                return False
            
            # Seleccionar cine
            self.cine_actual = cine["nombre"]
            select_cine = Select(self.driver.find_element(By.ID, "cine"))
            select_cine.select_by_value(cine["value"])
            
            # Esperar a que el cine cambie realmente en la página
            if not self.esperar_cambio_de_cine(self.cine_actual):
                return False
            
            # Esperar a que la página se recargue completamente
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".contenido-cartelera-principal")))
            
            return True
        except StaleElementReferenceException:
            time.sleep(3)
            return self.seleccionar_ciudad_y_cine(ciudad, cine)
        except Exception as e:
            print(f"Error seleccionando ciudad y cine: {str(e)}")
            return False
    
    def verificar_cine_correcto(self):
        """Verifica que el cine mostrado en la página sea el correcto."""
        try:
            # Obtener el nombre actual del cine en la página
            cine_pagina = self.obtener_nombre_cine_actual()
            
            if not cine_pagina:
                return False
                
            if cine_pagina != self.cine_actual:
                return False
            
            return True
        except Exception as e:
            print(f"Error verificando cine correcto: {str(e)}")
            return False
    
    def verificar_elementos_cargados(self):
        """Verifica que los elementos dinámicos estén cargados."""
        try:
            # Verificar slider de horario
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".MuiSlider-root")))
            
            # Verificar selector de fecha
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "dia")))
            
            return True
        except Exception as e:
            print(f"Error verificando elementos cargados: {str(e)}")
            return False
    
    def obtener_fechas_disponibles(self):
        """Obtiene y muestra las fechas disponibles en el selector de fechas."""
        try:
            select_fecha = Select(self.driver.find_element(By.ID, "dia"))
            opciones_fecha = select_fecha.options
            
            fechas = []
            fechas_array = []
            for opcion in opciones_fecha:
                fecha_obj = datetime.strptime(opcion.get_attribute("value"), "%Y-%m-%d")
                fecha_formateada = fecha_obj.strftime("%d/%m/%Y")
                
                fecha = {
                    "texto": opcion.text,
                    "value": opcion.get_attribute("value"),
                    "formateada": fecha_formateada,
                    "es_hoy": "Hoy" in opcion.text
                }
                fechas.append(fecha)
                fechas_array.append(fecha_formateada)
            
            # Mostrar fechas como array
            
            return fechas
        except Exception as e:
            print(f"Error obteniendo fechas disponibles: {str(e)}")
            return []
        
    def extraer_datos_pelicula(self, pelicula, fecha_value, fecha_texto):
        """Extrae datos de una sola película con formato de fecha DD/MM/YYYY."""
        try:
            # Fecha: YYYY-MM-DD -> DD/MM/YYYY
            fecha_obj = datetime.strptime(fecha_value, "%Y-%m-%d")
            fecha_formateada = fecha_obj.strftime("%d/%m/%Y")

            # Título: probar varias opciones (el DOM cambia entre builds)
            titulo = _first_text(pelicula, [
                "h3",
                "h2",
                "header h3",
                "header h2",
                "a.datalayer-movie",
                "[class*='movie'] h3",
                "[class*='Movie'] h3",
                "[class*='movie'] h2",
                "[class*='Movie'] h2",
            ])

            # Formatos y horarios: conservar tu estrategia, pero con tolerancia
            datos = []
            # contenedores de formato (pueden llamarse .formato, o variar)
            formato_containers = [
                ".formato",
                "[class*='formato']",
                "[class*='Formato']",
            ]
            hora_selectors = [
                ".horas p",             # tu selector original
                "ul li label",          # fallback en otros sitios
                ".col9 .btnhorario a",  # estilo Panamá
                ".horarios p",
            ]
            nombre_formato_selectors = [
                ".formato-nombre",
                "[class*='formato-nombre']",
                "[class*='Formato'] .formato-nombre",
                ".col3 span",           # estilo Panamá (múltiples spans)
            ]

            contenedores = []
            for sel in formato_containers:
                contenedores = pelicula.find_elements(By.CSS_SELECTOR, sel)
                if contenedores:
                    break

            if not contenedores:
                # Si no hay contenedores, intentemos tratar la tarjeta como un bloque único de horarios.
                horarios = []
                for hsel in hora_selectors:
                    horarios = [h.text.strip() for h in pelicula.find_elements(By.CSS_SELECTOR, hsel) if h.text.strip()]
                    if horarios:
                        break
                if horarios:
                    for hora in horarios:
                        datos.append({
                            "Country": self.pais,
                            "Theater": self.cine_actual,
                            "Date": fecha_formateada,
                            "Time": hora,
                            "Movie": titulo,
                            "Format": "",  # desconocido
                        })
                    return datos
                else:
                    # No encontramos nada útil
                    return []

            # Hay contenedores de formato
            for cont in contenedores:
                # nombre del formato
                tipo_formato = _first_text(cont, nombre_formato_selectors)
                if not tipo_formato:
                    # algunos sitios ponen el formato en múltiples spans col3
                    spans = cont.find_elements(By.CSS_SELECTOR, ".col3 span")
                    if spans:
                        tipo_formato = " ".join([s.text.strip() for s in spans if s.text.strip()])

                # horarios
                horarios = []
                for hsel in hora_selectors:
                    horarios = [h.text.strip() for h in cont.find_elements(By.CSS_SELECTOR, hsel) if h.text.strip()]
                    if horarios:
                        break

                for hora in horarios:
                    datos.append({
                        "Country": self.pais,
                        "Theater": self.cine_actual,
                        "Date": fecha_formateada,
                        "Time": hora,
                        "Movie": titulo,
                        "Format": tipo_formato,
                    })

            return datos
        except Exception as e:
            print(f"Error extrayendo datos de película: {str(e)}")
            return []


    def recolectar_datos_peliculas(self):
        """Recolecta datos de todas las películas para la fecha actual."""
        try:
            # Obtener fecha seleccionada
            fecha_selector = Select(self.driver.find_element(By.ID, "dia"))
            fecha_option = fecha_selector.first_selected_option
            fecha_texto = fecha_option.text
            fecha_value = fecha_option.get_attribute("value")

            # Espera a que carguen las películas DESPUÉS de cambiar la fecha.
            # Intentar varias firmas de contenedor (React renombra clases con frecuencia).
            card_selectors = [
                "[class*='SingleScheduleMovie__SingleScheduleComponent']",
                "[class*='SingleScheduleComponent']",
                ".SingleScheduleMovie__SingleScheduleComponent-sc-1n3hti2-0",
                "article.tituloPelicula",               # fallback tipo PA
                ".movie-projection",                    # fallback tipo CR/SV/HN
            ]
            peliculas = []
            for sel in card_selectors:
                try:
                    peliculas = WebDriverWait(self.driver, 8).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, sel))
                    )
                    if peliculas:
                        break
                except TimeoutException:
                    continue

            if not peliculas:
                # último intento sin espera (por si ya estaban en DOM)
                for sel in card_selectors:
                    found = self.driver.find_elements(By.CSS_SELECTOR, sel)
                    if found:
                        peliculas = found
                        break

            todos_datos = []
            for pelicula in peliculas:
                datos_pelicula = self.extraer_datos_pelicula(pelicula, fecha_value, fecha_texto)
                if datos_pelicula:
                    todos_datos.extend(datos_pelicula)

            return todos_datos
        except Exception as e:
            print(f"Error recolectando datos pelicula: {str(e)}")
            return []


    
    def guardar_datos_dataframe(self, datos, es_hoy):
        """Guarda los datos en un DataFrame según si es hoy o fechas futuras."""
        try:
            columnas = ["Country", "Theater", "Date", "Time", "Movie", "Format"]
            df_datos = pd.DataFrame(datos, columns=columnas)
            
            if es_hoy:
                if not hasattr(self, 'df_hoy'):
                    self.df_hoy = pd.DataFrame(columns=columnas)
                self.df_hoy = pd.concat([self.df_hoy, df_datos], ignore_index=True)
            else:
                if not hasattr(self, 'df_proximos'):
                    self.df_proximos = pd.DataFrame(columns=columnas)
                self.df_proximos = pd.concat([self.df_proximos, df_datos], ignore_index=True)
            
            return True
        except Exception as e:
            print(f"Error guardando datos en DataFrame: {str(e)}")
            return False

    def procesar_cine(self, ciudad, cine):
        """Procesa un cine específico, obteniendo datos solo de hoy y las siguientes 7 fechas."""
        try:
            if not self.seleccionar_ciudad_y_cine(ciudad, cine):
                return False
            time.sleep(1)
            if not self.verificar_cine_correcto():
                return False
            if not self.verificar_elementos_cargados():
                return False
            # Obtener fechas disponibles
            select_fecha = Select(self.driver.find_element(By.ID, "dia"))
            fechas = []
            for option in select_fecha.options:
                fechas.append({
                    "text": option.text,
                    "value": option.get_attribute("value"),
                    "is_today": "Hoy" in option.text
                })
            # Limitar a solo la primera fecha (hoy) y las siguientes 7 fechas
            fechas = fechas[:8]
            for fecha in fechas:
                select_fecha.select_by_value(fecha["value"])
                try:
                    WebDriverWait(self.driver, 8).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 
                            "[class*='SingleScheduleMovie__SingleScheduleComponent'], \
                            [class*='SingleScheduleComponent'], \
                            .SingleScheduleMovie__SingleScheduleComponent-sc-1n3hti2-0, \
                            article.tituloPelicula, \
                            .movie-projection"
                        ))
                    )
                except TimeoutException:
                    pass
                datos_peliculas = self.recolectar_datos_peliculas()
                if datos_peliculas:
                    self.guardar_datos_dataframe(datos_peliculas, es_hoy=fecha["is_today"])
                else:
                    pass
            return True
        except Exception as e:
            print(f"Error procesando cine {cine['nombre']}: {str(e)}")
            return False
    
    def ejecutar_scraping(self):
        """Ejecuta el proceso completo de scraping."""
        try:
            # Navegar a la página principal
            if not self.navegar_a_pagina_principal():
                raise RuntimeError("No se pudo navegar a la página principal")
            
            # Obtener lista de ciudades
            if not self.obtener_lista_ciudades():
                raise RuntimeError("No se pudo obtener la lista de ciudades")
            
            # Procesar cada ciudad y cada cine
            for ciudad in self.lista_ciudades:
                # Seleccionar la ciudad para obtener sus cines
                select_ciudad = Select(self.driver.find_element(By.ID, "ciudad"))
                select_ciudad.select_by_value(ciudad["value"])
                time.sleep(1)
                
                # Obtener lista de cines para esta ciudad
                if not self.obtener_lista_cines():
                    continue
                
                # Procesar cada cine de esta ciudad
                for cine in self.lista_cines:
                    self.procesar_cine(ciudad, cine)
                    time.sleep(1)
            
        except Exception as e:
            print(f"Error durante el scraping: {str(e)}")
            raise
        finally:
            if self.driver:
                self.driver.quit()

    def exponer_datos(self):
        """Expone los datos recolectados en DataFrames."""
        return self.df_hoy, self.df_proximos


CONTRACT_COLS = ["Country", "Theater", "Date", "Time", "Movie", "Format"]

def _resolve_chromedriver_path() -> str:
    # Allow CHROMEDRIVER env override; else look for local exe/binary; else 'chromedriver'
    env = os.environ.get("CHROMEDRIVER")
    if env:
        return env
    exe = "chromedriver.exe" if os.name == "nt" else "chromedriver"
    local = os.path.join(os.getcwd(), exe)
    return local if os.path.exists(local) else exe

def _normalize_and_combine(df_hoy: pd.DataFrame, df_prox: pd.DataFrame) -> pd.DataFrame:
    def _fix(df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame(columns=CONTRACT_COLS)
        # Ensure only the expected columns (your class already produces these names)
        cols_map = {
            "Country": "Country",
            "Theater": "Theater",
            "Date": "Date",
            "Time": "Time",
            "Movie": "Movie",
            "Format": "Format",
        }
        # Some earlier versions used Spanish headers; map if needed:
        if "Pais" in df.columns: cols_map["Pais"] = "Country"
        if "Nombre del cine" in df.columns: cols_map["Nombre del cine"] = "Theater"
        if "Fecha de funcion" in df.columns: cols_map["Fecha de funcion"] = "Date"
        if "hora de funcion" in df.columns: cols_map["hora de funcion"] = "Time"
        if "Nombre de la pelicula" in df.columns: cols_map["Nombre de la pelicula"] = "Movie"
        if "Formato de la pelicula" in df.columns: cols_map["Formato de la pelicula"] = "Format"

        df2 = df.rename(columns=cols_map)
        df2 = df2[[c for c in CONTRACT_COLS if c in df2.columns]].copy()

        # Trim strings
        for c in ["Country", "Theater", "Time", "Movie", "Format"]:
            if c in df2.columns:
                df2[c] = df2[c].astype(str).str.strip()

        # Convert Date "DD/MM/YYYY" (as produced by this class) -> python date
        if "Date" in df2.columns:
            parsed = pd.to_datetime(df2["Date"], errors="coerce", dayfirst=True)
            df2["Date"] = parsed.dt.date

        # Drop rows without valid dates
        df2 = df2.dropna(subset=["Date"])
        return df2

    a = _fix(df_hoy)
    b = _fix(df_prox)
    out = pd.concat([a, b], ignore_index=True) if not a.empty or not b.empty else pd.DataFrame(columns=CONTRACT_COLS)
    # Reorder columns
    out = out.reindex(columns=CONTRACT_COLS)
    return out

def scrape(headless: bool = True) -> pd.DataFrame:
    """
    Orchestrator entrypoint for Guatemala scraper.
    Runs the existing class, returns a single DataFrame with contract columns.
    """
    ruta_driver = _resolve_chromedriver_path()
    scraper = ScraperCinepolisGuatemala(ruta_driver)
    # Note: the class already sets headless in configurar_navegador(); we ignore `headless` here.
    scraper.ejecutar_scraping()
    df_hoy, df_proximos = scraper.exponer_datos()
    return _normalize_and_combine(df_hoy, df_proximos)

# Keep the CLI runnable for standalone debugging if you want:
if __name__ == "__main__":
    df = scrape(headless=True)
