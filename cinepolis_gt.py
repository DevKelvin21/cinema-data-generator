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
            print("Navegador configurado correctamente")
        except WebDriverException as e:
            raise RuntimeError(f"Error al iniciar el navegador: {str(e)}")
    
    def cerrar_popup_video(self):
        """Cierra el popup de video que aparece al cargar la página."""
        try:
            close_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#takeover-close")))
            close_button.click()
            print("Popup de video cerrado exitosamente")
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
            
            print(f"Navegación a {self.url} completada")
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
            print(f"\nCines disponibles en {self.ciudad_actual}:", cines_array)
            
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
            print(f"Timeout esperando cambio a cine: {nombre_cine_esperado}")
            return False
    
    def seleccionar_ciudad_y_cine(self, ciudad, cine):
        """Selecciona una ciudad y un cine específico."""
        try:
            # Actualizar la ciudad actual inmediatamente
            self.ciudad_actual = ciudad["nombre"]
            print(f"\nSeleccionando ciudad: {self.ciudad_actual}")
            
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
            
            print(f"\nSe seleccionó correctamente Cine: {self.cine_actual} en Ciudad: {self.ciudad_actual}")
            return True
        except StaleElementReferenceException:
            print("Error: Elemento obsoleto al seleccionar ciudad/cine. Reintentando...")
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
                print("Error: No se pudo obtener el nombre del cine de la página")
                return False
                
            if cine_pagina != self.cine_actual:
                print(f"Error: El cine mostrado ({cine_pagina}) no coincide con el seleccionado ({self.cine_actual})")
                return False
            
            print(f"Verificación exitosa: Cine correcto ({self.cine_actual})")
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
            
            print("Elementos dinámicos cargados correctamente")
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
            print("\nFechas disponibles:", fechas_array)
            
            return fechas
        except Exception as e:
            print(f"Error obteniendo fechas disponibles: {str(e)}")
            return []
        
    def extraer_datos_pelicula(self, pelicula, fecha_value, fecha_texto):
        """Extrae datos de una sola película con formato de fecha DD/MM/YYYY."""
        try:
            # Convertir fecha de YYYY-MM-DD a DD/MM/YYYY
            fecha_obj = datetime.strptime(fecha_value, "%Y-%m-%d")
            fecha_formateada = fecha_obj.strftime("%d/%m/%Y")
            
            # Extraer nombre de la película
            nombre = pelicula.find_element(By.CSS_SELECTOR, "h3").text
            
            # Extraer formatos y horarios
            formatos = pelicula.find_elements(By.CSS_SELECTOR, ".formato")
            datos = []
            
            for formato in formatos:
                tipo_formato = formato.find_element(By.CSS_SELECTOR, ".formato-nombre").text
                horarios = [h.text for h in formato.find_elements(By.CSS_SELECTOR, ".horas p")]
                
                for hora in horarios:
                    datos.append({
                        "Country": self.pais,
                        "Theater": self.cine_actual,
                        "Date": fecha_formateada,  # Formato DD/MM/YYYY
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
            # Obtener fecha seleccionada
            fecha_selector = Select(self.driver.find_element(By.ID, "dia"))
            fecha_option = fecha_selector.first_selected_option
            fecha_texto = fecha_option.text
            fecha_value = fecha_option.get_attribute("value")
            
            # Esperar a que carguen las películas
            time.sleep(1)
            
            # Localizar todas las películas
            peliculas = self.driver.find_elements(By.CSS_SELECTOR, ".SingleScheduleMovie__SingleScheduleComponent-sc-1n3hti2-0")
            
            todos_datos = []
            for pelicula in peliculas:
                datos_pelicula = self.extraer_datos_pelicula(pelicula, fecha_value, fecha_texto)
                if datos_pelicula:
                    todos_datos.extend(datos_pelicula)
            
            return todos_datos
        except Exception as e:
            print(f"Error recolectando datos pelicula: {str(e)}")
            return []

    def crear_estructura_excel(self):
        """Crea la estructura básica del Excel con las columnas requeridas."""
        # Obtener fecha actual para el nombre del archivo
        fecha_actual = datetime.now().strftime("%Y%m%d")
        nombre_archivo = f"cinepolis_data_{fecha_actual}.xlsx"
        
        # Columnas exactas requeridas
        columnas = ["Country", "Theater", "Date", "Time", "Movie", "Format"]
        
        df_hoy = pd.DataFrame(columns=columnas)
        df_proximos = pd.DataFrame(columns=columnas)
        
        # Crear el archivo Excel con las dos hojas
        with pd.ExcelWriter(nombre_archivo, engine='openpyxl') as writer:
            df_hoy.to_excel(writer, sheet_name='Today', index=False)
            df_proximos.to_excel(writer, sheet_name='Other schedules', index=False)
        
        print(f"\nEstructura de Excel creada correctamente en {nombre_archivo}")
        return nombre_archivo
    
    def guardar_datos_excel(self, datos, es_hoy, nombre_archivo):
        """Guarda los datos en el archivo Excel según la hoja correspondiente."""
        try:
            # Leer el archivo Excel existente
            with pd.ExcelFile(nombre_archivo) as excel:
                df_hoy = pd.read_excel(excel, sheet_name='Today')
                df_proximos = pd.read_excel(excel, sheet_name='Other schedules')
            
            # Convertir a DataFrame
            df_datos = pd.DataFrame(datos)
            
            # Agregar los nuevos datos
            if es_hoy:
                df_hoy = pd.concat([df_hoy, df_datos], ignore_index=True)
            else:
                df_proximos = pd.concat([df_proximos, df_datos], ignore_index=True)
            
            # Guardar de nuevo en el Excel
            with pd.ExcelWriter(nombre_archivo, engine='openpyxl') as writer:
                df_hoy.to_excel(writer, sheet_name='Today', index=False)
                df_proximos.to_excel(writer, sheet_name='Other schedules', index=False)
            
            print(f"Datos guardados exitosamente en el Excel")
            return True
        except Exception as e:
            print(f"Error guardando datos en Excel: {str(e)}")
            return False
    
    def procesar_cine(self, ciudad, cine, nombre_archivo):
        """Procesa un cine específico, obteniendo datos solo de hoy y las siguientes 7 fechas."""
        try:
            print(f"\nPROCESANDO CINE: {cine['nombre']}")
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
                print(f"\nProcesando fecha: {fecha['text']}")
                select_fecha.select_by_value(fecha["value"])
                time.sleep(1)
                datos_peliculas = self.recolectar_datos_peliculas()
                if datos_peliculas:
                    print(f"Encontradas {len(datos_peliculas)} funciones para esta fecha")
                    self.guardar_datos_excel(datos_peliculas, es_hoy=fecha["is_today"], nombre_archivo=nombre_archivo)
                else:
                    print("No se encontraron funciones para esta fecha")
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
            
            # Crear estructura del Excel con nombre basado en fecha actual
            nombre_archivo = self.crear_estructura_excel()
            
            # Procesar cada ciudad y cada cine
            for ciudad in self.lista_ciudades:
                print(f"\nPROCESANDO CIUDAD: {ciudad['nombre']}")
                
                # Seleccionar la ciudad para obtener sus cines
                select_ciudad = Select(self.driver.find_element(By.ID, "ciudad"))
                select_ciudad.select_by_value(ciudad["value"])
                time.sleep(1)
                
                # Obtener lista de cines para esta ciudad
                if not self.obtener_lista_cines():
                    continue
                
                # Procesar cada cine de esta ciudad
                for cine in self.lista_cines:
                    self.procesar_cine(ciudad, cine, nombre_archivo)
                    time.sleep(1)
            
            print("\nProceso de scraping completado")
            return nombre_archivo
            
        except Exception as e:
            print(f"Error durante el scraping: {str(e)}")
            raise
        finally:
            if self.driver:
                self.driver.quit()
                print("Navegador cerrado correctamente")

if __name__ == "__main__":
    try:
        # Configurar y ejecutar el scraper
        ruta_driver = os.path.join(os.getcwd(), "chromedriver.exe")
        if not os.path.exists(ruta_driver):
            raise FileNotFoundError(f"No se encontró chromedriver.exe en {ruta_driver}")
        scraper = ScraperCinepolisGuatemala(ruta_driver)
        nombre_archivo = scraper.ejecutar_scraping()
        print(f"\nProceso completado. Datos guardados en {nombre_archivo}")
    except Exception as e:
        print(f"Error en la ejecución principal: {str(e)}")