# CODIGO MEJORADO - CINEPOLIS PANAMA SCRAPER
import os
import time
from datetime import datetime, date
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, StaleElementReferenceException
import pandas as pd
from __future__ import annotations
from typing import Optional, List

# URL for Cinepolis Panama
CINEPOLIS_URL = "https://cinepolis.com.pa/"

class ScraperCinepolisPanama:
    def __init__(self):
        """
        Inicializa el scraper con la configuración básica.
        """
        self.pais = "Panama"
        self.url = CINEPOLIS_URL
        self.driver = None
        self.cine_actual = ""
        self.ciudad_actual = ""
        self.lista_ciudades = []
        self.lista_cines = []
        self.df_hoy = pd.DataFrame()
        self.df_proximos = pd.DataFrame()
        self.configurar_navegador()
        self.intentos_fallidos = 0
        
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
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(60)
            self.driver.set_script_timeout(30)
            print("Navegador configurado correctamente")
        except WebDriverException as e:
            raise RuntimeError(f"Error al iniciar el navegador: {str(e)}")
    
    def manejar_alerta(self):
        """Intenta manejar alertas solo si están presentes."""
        try:
            # Busca alertas sin espera explícita (solo si ya están presentes)
            alertas = self.driver.find_elements(By.ID, "alertify-ok")
            for alerta in alertas:
                try:
                    if alerta.is_displayed():
                        alerta.click()
                        print("Alerta cerrada")
                        time.sleep(1)
                except:
                    continue
            return True
        except Exception:
            return False
    
    def verificar_error_404(self):
        """Verifica si la página actual es un error 404 de manera precisa."""
        try:
            # Busca específicamente el div con clase 'g960' que contiene el error 404
            error_div = self.driver.find_elements(By.XPATH, "//div[@class='g960 cf']/p[@class='float-left']")
            if error_div and "Error 404" in error_div[0].text:
                print("Error 404 detectado en la estructura de la página")
                return True
            return False
        except Exception:
            return False
    
    def recuperar_de_404(self):
        """Recuperación optimizada de error 404."""
        try:
            # Intenta el botón "Ir al inicio" específico
            ir_inicio = self.driver.find_elements(By.XPATH, "//p[@class='float-right']/a[@href='/']")
            if ir_inicio:
                ir_inicio[0].click()
                time.sleep(2)
                return True
            
            # Si no encuentra el botón, recarga la página principal
            self.driver.get(self.url)
            time.sleep(3)
            return True
        except Exception:
            return False
    
    def navegar_a_pagina_principal(self):
        """Navegación optimizada que solo maneja errores cuando aparecen."""
        max_intentos = 3
        intento = 0
        
        while intento < max_intentos:
            try:
                intento += 1
                self.driver.get(self.url)
                time.sleep(3)
                
                # Manejo condicional de alertas/errores
                if self.verificar_error_404():
                    print("Error 404 detectado al cargar página principal")
                    self.recuperar_de_404()
                    continue
                    
                # Maneja alertas solo si existen
                self.manejar_alerta()
                
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.ID, "cmbCiudades")))
                
                return True
                
            except Exception as e:
                print(f"Intento {intento} fallido: {str(e)}")
                if intento < max_intentos:
                    time.sleep(3)
        
        return False
    
    def obtener_lista_ciudades(self):
            """Obtiene y muestra la lista de ciudades disponibles."""
            try:
                # Limpiar la lista existente
                self.lista_ciudades = []
                
                # Esperar a que el selector de ciudades esté disponible
                select_ciudad = WebDriverWait(self.driver, 25).until(
                    EC.presence_of_element_located((By.ID, "cmbCiudades")))
                
                # Obtener todas las opciones de ciudad
                opciones_ciudad = select_ciudad.find_elements(By.TAG_NAME, "option")
                
                for opcion in opciones_ciudad[1:]:  # Saltamos el primer elemento que es "Selecciona una ciudad"
                    ciudad = {
                        "nombre": opcion.text,
                        "value": opcion.get_attribute("value"),
                        "clave": opcion.get_attribute("clave")
                    }
                    self.lista_ciudades.append(ciudad)
                
                # Mostrar ciudades como array
                ciudades_array = [ciudad['nombre'] for ciudad in self.lista_ciudades]
                print("\nCiudades disponibles:", ciudades_array)
                
                return True
            except Exception as e:
                print(f"Error obteniendo lista de ciudades: {str(e)}")
                return False
    
    def obtener_lista_cines(self):
            """Obtiene y muestra la lista de cines disponibles para la ciudad seleccionada."""
            try:
                # Limpiar la lista existente
                self.lista_cines = []
                
                select_cine = WebDriverWait(self.driver, 25).until(
                    EC.presence_of_element_located((By.ID, "cmbComplejos")))
                opciones_cine = select_cine.find_elements(By.TAG_NAME, "option")
                
                for opcion in opciones_cine[1:]:  # Saltamos el primer elemento que es "Selecciona un cine"
                    cine = {
                        "nombre": opcion.text,
                        "value": opcion.get_attribute("value")
                    }
                    self.lista_cines.append(cine)
                
                # Mostrar cines como array
                cines_array = [cine['nombre'] for cine in self.lista_cines]
                print(f"\nCines disponibles en {self.ciudad_actual}:", cines_array)
                
                return True
            except Exception as e:
                print(f"Error obteniendo lista de cines: {str(e)}")
                return False
    
    def obtener_nombre_cine_actual(self):
        """Obtiene el nombre del cine actualmente mostrado en la página."""
        try:
            # Obtener el segundo hijo del div con id "opcionesComplejo" y luego buscar el span dentro
            cine_element = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 
                "#opcionesComplejo > div:nth-child(2) .chosen-container .chosen-choices .search-choice span")))
            print(f"Nombre del cine actual: {cine_element.text}")
            return cine_element.text
        except (NoSuchElementException, TimeoutException):
            return ""
    
    def esperar_cambio_de_cine(self, nombre_cine_esperado, timeout=30):
        """Espera a que el nombre del cine en la página coincida con el esperado."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                cine_actual = self.obtener_nombre_cine_actual()
                if cine_actual == nombre_cine_esperado:
                    return True
                
                # Si hay un error 404, manejarlo
                if self.verificar_error_404():
                    print("Error 404 detectado durante espera de cambio de cine")
                    self.recuperar_de_404()
                    return False
                
                time.sleep(2)
            except Exception as e:
                print(f"Error verificando cambio de cine: {str(e)}")
                time.sleep(2)
        
        print(f"Timeout esperando cambio a cine: {nombre_cine_esperado}")
        return False
    
    def seleccionar_ciudad_y_cine_con_reintentos(self, ciudad, cine, max_intentos=5):
        """Selecciona una ciudad y un cine específico con reintentos automáticos."""
        intento = 0
        
        while intento < max_intentos:
            intento += 1
            print(f"\nIntento {intento} de seleccionar {cine['nombre']} en {ciudad['nombre']}")
            
            try:
                # Actualizar la ciudad actual
                self.ciudad_actual = ciudad["nombre"]
                
                # Seleccionar ciudad con espera más robusta
                WebDriverWait(self.driver, 25).until(
                    EC.presence_of_element_located((By.ID, "cmbCiudades")))
                select_ciudad = Select(self.driver.find_element(By.ID, "cmbCiudades"))
                select_ciudad.select_by_value(ciudad["value"])
                time.sleep(3)
                
                # Manejar posibles alertas después de selección
                self.manejar_alerta()
                
                # Verificar si apareció error 404
                if self.verificar_error_404():
                    print("Error 404 después de seleccionar ciudad, recuperando...")
                    if not self.recuperar_de_404():
                        self.driver.get(self.url)
                        time.sleep(5)
                        self.manejar_alerta()
                        continue
                
                # Esperar a que se carguen los cines (tiempo aumentado)
                WebDriverWait(self.driver, 25).until(
                    EC.presence_of_element_located((By.ID, "cmbComplejos")))
                
                # Obtener lista de cines actualizada
                if not self.obtener_lista_cines():
                    print("No se pudo obtener lista de cines, reintentando...")
                    continue
                
                # Seleccionar cine
                self.cine_actual = cine["nombre"]
                select_cine = Select(self.driver.find_element(By.ID, "cmbComplejos"))
                select_cine.select_by_value(cine["value"])
                time.sleep(3)
                
                # Manejar posibles alertas después de selección
                self.manejar_alerta()
                
                # Verificar si apareció error 404
                if self.verificar_error_404():
                    print("Error 404 después de seleccionar cine, recuperando...")
                    if not self.recuperar_de_404():
                        self.driver.get(self.url)
                        time.sleep(5)
                        self.manejar_alerta()
                        continue
                
                # Esperar a que el cine cambie realmente en la página (tiempo aumentado)
                if not self.esperar_cambio_de_cine(self.cine_actual, timeout=30):
                    print("No se detectó cambio de cine, reintentando...")
                    continue
                
                # Verificar que los elementos principales estén cargados
                WebDriverWait(self.driver, 25).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".divComplejo")))
                
                print(f"Se seleccionó correctamente Cine: {self.cine_actual} en Ciudad: {self.ciudad_actual}")
                return True
                
            except StaleElementReferenceException:
                print("Elemento obsoleto, reintentando...")
                time.sleep(5)
                continue
            except Exception as e:
                print(f"Error seleccionando cine (intento {intento}): {str(e)}")
                if intento < max_intentos:
                    # Recargar completamente la página y volver a intentar
                    self.driver.get(self.url)
                    time.sleep(5)
                    self.manejar_alerta()
                    self.navegar_a_pagina_principal()
                    continue
                else:
                    return False
        
        print(f"No se pudo seleccionar el cine después de {max_intentos} intentos")
        return False
    
    def verificar_cine_correcto(self):
        """Verifica que el cine mostrado en la página sea el correcto."""
        try:
            cine_pagina = self.obtener_nombre_cine_actual()
            
            if not cine_pagina:
                print("No se pudo obtener el nombre del cine de la página")
                return False
                
            if cine_pagina != self.cine_actual:
                print(f"El cine mostrado ({cine_pagina}) no coincide con el seleccionado ({self.cine_actual})")
                return False
            
            print(f"Verificación exitosa: Cine correcto ({self.cine_actual})")
            return True
        except Exception as e:
            print(f"Error verificando cine correcto: {str(e)}")
            return False
    
    def verificar_elementos_cargados(self):
        """Verifica que los elementos dinámicos estén cargados."""
        try:
            WebDriverWait(self.driver, 25).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-slider")))
            
            WebDriverWait(self.driver, 25).until(
                EC.presence_of_element_located((By.ID, "cmbFechas")))
            
            print("Elementos dinámicos cargados correctamente")
            return True
        except Exception as e:
            print(f"Error verificando elementos cargados: {str(e)}")
            return False
    
    def obtener_fechas_disponibles(self):
        """Obtiene y muestra las fechas disponibles en el selector de fechas."""
        try:
            select_fecha = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "cmbFechas")))
            select_fecha = Select(select_fecha)
            opciones_fecha = select_fecha.options
            
            fechas = []
            fechas_array = []
            for opcion in opciones_fecha:
                fecha_texto = opcion.text
                fecha_value = opcion.get_attribute("value")
                fecha_simple = fecha_texto.split("(")[-1].replace(")", "") if "(" in fecha_texto else fecha_texto
                
                fecha = {
                    "texto": fecha_texto,
                    "value": fecha_value,
                    "formateada": fecha_simple.strip(),
                    "es_hoy": "Hoy" in fecha_texto
                }
                fechas.append(fecha)
                fechas_array.append(fecha_simple.strip())
            
            print("\nFechas disponibles:", fechas_array)
            return fechas
        except Exception as e:
            print(f"Error obteniendo fechas disponibles: {str(e)}")
            return []
        
    def extraer_datos_pelicula(self, pelicula, fecha_value, fecha_texto):
        """Extrae datos de una sola película."""
        try:
            # nombre = pelicula.find_element(By.CSS_SELECTOR, "h3 > .datalayer-movie").text
            nombre = pelicula.find_element(By.CSS_SELECTOR, "h3 a.datalayer-movie").text
            formatos = pelicula.find_elements(By.CSS_SELECTOR, ".horarioExp")
            datos = []
            
            for formato in formatos:
                tipo_formato = " ".join([span.text for span in formato.find_elements(By.CSS_SELECTOR, ".col3 span") if span.text.strip()])
                horarios = [h.text for h in formato.find_elements(By.CSS_SELECTOR, ".col9 .btnhorario a")]
                
                for hora in horarios:
                    datos.append({
                        "Country": self.pais,
                        "Theater": self.cine_actual,
                        "Date": fecha_texto,
                        "Time": hora,
                        "Movie": nombre,
                        "Format": tipo_formato
                    })
            
            return datos
        except Exception as e:
            print(f"Error extrayendo datos de película: {str(e)}")
            return []

    def recolectar_datos_peliculas(self):
        """Recolecta datos de todas las películas para la fecha actual."""
        try:
            select_fecha = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "cmbFechas")))
            select_fecha = Select(select_fecha)
            fecha_option = select_fecha.first_selected_option
            fecha_texto = fecha_option.text
            fecha_value = fecha_option.get_attribute("value")
            fecha_simple = fecha_texto.split("(")[-1].replace(")", "") if "(" in fecha_texto else fecha_texto
            
            time.sleep(2)
            peliculas = self.driver.find_elements(By.CSS_SELECTOR, "article.tituloPelicula")
            
            todos_datos = []
            for pelicula in peliculas:
                datos_pelicula = self.extraer_datos_pelicula(pelicula, fecha_value, fecha_simple.strip())
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
            
            print("Datos agregados al DataFrame correctamente")
            return True
        except Exception as e:
            print(f"Error guardando datos en DataFrame: {str(e)}")
            return False
    
    def procesar_cine(self, ciudad, cine):
        """Procesa un cine específico, obteniendo datos de todas las fechas disponibles."""
        try:
            print(f"\nPROCESANDO CINE: {cine['nombre']}")
            
            if not self.seleccionar_ciudad_y_cine_con_reintentos(ciudad, cine):
                print(f"No se pudo seleccionar el cine {cine['nombre']}")
                return False
            
            time.sleep(2)
            
            if not self.verificar_cine_correcto():
                print(f"No se pudo verificar el cine {cine['nombre']}")
                return False
            
            if not self.verificar_elementos_cargados():
                print(f"No se cargaron los elementos para el cine {cine['nombre']}")
                return False
            
            fechas = self.obtener_fechas_disponibles()
            # Limitar a solo los primeros 7 días disponibles
            fechas = fechas[:8]
            for fecha in fechas:
                print(f"\nProcesando fecha: {fecha['texto']}")
                try:
                    select_fecha = WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.ID, "cmbFechas")))
                    select_fecha = Select(select_fecha)
                    select_fecha.select_by_value(fecha["value"])
                    time.sleep(2)
                    datos_peliculas = self.recolectar_datos_peliculas()
                    if datos_peliculas:
                        print(f"Encontradas {len(datos_peliculas)} funciones para esta fecha")
                        self.guardar_datos_dataframe(datos_peliculas, es_hoy=fecha["es_hoy"])
                    else:
                        print("No se encontraron funciones para esta fecha")
                except Exception as e:
                    print(f"Error procesando fecha {fecha['texto']}: {str(e)}")
                    continue
            
            return True
        except Exception as e:
            print(f"Error procesando cine {cine['nombre']}: {str(e)}")
            return False
    
    def ejecutar_scraping(self):
        """Ejecuta el proceso completo de scraping."""
        try:
            if not self.navegar_a_pagina_principal():
                raise RuntimeError("No se pudo navegar a la página principal")
            
            if not self.obtener_lista_ciudades():
                raise RuntimeError("No se pudo obtener la lista de ciudades")
            
            for ciudad in self.lista_ciudades:
                print(f"\nPROCESANDO CIUDAD: {ciudad['nombre']}")
                
                try:
                    select_ciudad = WebDriverWait(self.driver, 25).until(
                        EC.presence_of_element_located((By.ID, "cmbCiudades")))
                    select_ciudad = Select(select_ciudad)
                    select_ciudad.select_by_value(ciudad["value"])
                    time.sleep(3)
                    
                    if not self.obtener_lista_cines():
                        print(f"No se pudo obtener la lista de cines para {ciudad['nombre']}")
                        continue
                    
                    for cine in self.lista_cines:
                        self.procesar_cine(ciudad, cine)
                        time.sleep(2)
                
                except Exception as e:
                    print(f"Error procesando ciudad {ciudad['nombre']}: {str(e)}")
                    continue
            
            print("\nProceso de scraping completado")
            
        except Exception as e:
            print(f"Error durante el scraping: {str(e)}")
            raise
        finally:
            if self.driver:
                self.driver.quit()
                print("Navegador cerrado correctamente")

    def exponer_datos(self):
        """Expone los datos recolectados en DataFrames."""
        return self.df_hoy, self.df_proximos


CONTRACT_COLS = ["Country", "Theater", "Date", "Time", "Movie", "Format"]

def _normalize_and_combine(df_hoy: Optional[pd.DataFrame],
                           df_prox: Optional[pd.DataFrame]) -> pd.DataFrame:
    def _fix(df: Optional[pd.DataFrame]) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame(columns=CONTRACT_COLS)

        # Map any Spanish headers (just in case) -> contract
        cols_map = {
            "Country": "Country",
            "Theater": "Theater",
            "Date": "Date",
            "Time": "Time",
            "Movie": "Movie",
            "Format": "Format",
            "Pais": "Country",
            "Nombre del cine": "Theater",
            "Fecha de funcion": "Date",
            "hora de funcion": "Time",
            "Nombre de la pelicula": "Movie",
            "Formato de la pelicula": "Format",
        }
        df2 = df.rename(columns=cols_map)

        # Keep only contract columns that exist
        present = [c for c in CONTRACT_COLS if c in df2.columns]
        df2 = df2[present].copy()

        # Trim strings
        for c in ["Country", "Theater", "Time", "Movie", "Format"]:
            if c in df2.columns:
                df2[c] = df2[c].astype(str).str.strip()

        # Parse Date (Panamá scraper sets Date from site text like "dd/mm/yyyy" or similar)
        if "Date" in df2.columns:
            parsed = pd.to_datetime(df2["Date"], errors="coerce", dayfirst=True)
            df2["Date"] = parsed.dt.date  # real date objects

        # Drop rows without valid date
        if "Date" in df2.columns:
            df2 = df2.dropna(subset=["Date"])

        # Reindex to full contract (missing cols become NaN)
        return df2.reindex(columns=CONTRACT_COLS)

    a = _fix(df_hoy)
    b = _fix(df_prox)
    if a.empty and b.empty:
        return pd.DataFrame(columns=CONTRACT_COLS)
    return pd.concat([a, b], ignore_index=True)

def scrape(headless: bool = True) -> pd.DataFrame:
    """
    Orchestrator entrypoint for Panamá scraper.
    Runs the existing class and returns a single DataFrame with contract columns
    and Date as datetime.date.
    """
    scraper = ScraperCinepolisPanama()  # class already configures headless in configurar_navegador()
    scraper.ejecutar_scraping()
    df_hoy, df_proximos = scraper.exponer_datos()
    return _normalize_and_combine(df_hoy, df_proximos)

# Optional: keep CLI runnable for quick checks
if __name__ == "__main__":
    out = scrape()
    print(out.head())
    print("Rows:", len(out))