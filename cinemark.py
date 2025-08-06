import os
import time
from datetime import datetime, timezone
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
import pandas as pd
from selenium.common.exceptions import (
    NoSuchElementException, 
    TimeoutException, 
    ElementNotInteractableException,
    WebDriverException
)

# Diccionario&lista de url y su respectivo pais
PAISES_URLS = {
    "El Salvador": "https://www.cinemarkca.com/el-salvador",
    "Guatemala": "https://www.cinemarkca.com/guatemala",
    "Honduras": "https://www.cinemarkca.com/honduras",
    "Costa Rica": "https://www.cinemarkca.com/costa-rica",
    "Panamá": "https://www.cinemarkca.com/panama",
    "Nicaragua": "https://www.cinemarkca.com/nicaragua"
}

class ScraperCinemarkCompleto:
    def __init__(self, ruta_driver, pais, url):
        """
        Inicializa el scraper con la configuración básica.
        
        Args:
            ruta_driver (str): Ruta al ejecutable de chromedriver
            pais (str): Nombre del país
            url (str): URL del país en Cinemark
        """
        self.ruta_driver = ruta_driver
        self.pais = pais
        self.url = url
        self.driver = None
        self.cine_actual = ""
        self.lista_cines = []
        self.configurar_navegador()
        
    def configurar_navegador(self):
        """Configura el navegador Chrome con opciones para scraping robusto."""
        chrome_options = Options()
        
        # Evitar deteccion, mejora rendimiento
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        #Configuraciones para suprimir errores o warnings
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-direct-composition")
        chrome_options.add_argument("--disable-features=VoiceTranscription,SpeechRecognition")
        chrome_options.add_argument("--disable-speech-api")
        chrome_options.add_argument("--disable-gcm")
        chrome_options.add_argument("--disable-sync")
        chrome_options.add_argument("--disable-machine-learning-model-downloader")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation', 'enable-cloud-services'])
        
        # Configuracion del servicio
        servicio = Service(executable_path=self.ruta_driver)
        
        try:
            self.driver = webdriver.Chrome(service=servicio, options=chrome_options)
            # Configurar tiempos de espera para levantar ventana
            self.driver.set_page_load_timeout(30) # Tiempo max para cargar una pagina
            self.driver.set_script_timeout(30)  # Tiempo max para ejecutar scripts JS que existen en la pagina web
            print("Navegador configurado correctamente")
        except WebDriverException as e:
            raise RuntimeError(f"Error al iniciar el navegador: {str(e)}")
    
    def aceptar_cookies(self):
        """
        Intenta aceptar las cookies si aparece el popup de anuncio.
        Si no aparece, continua sin error.
        """
        try:
            boton_cookies = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.modal-cookies__accept-button"))
            )
            boton_cookies.click()
            print("Cookies aceptadas correctamente.")
            return True
        except TimeoutException:
            print("No apareció el popup de cookies - continuando...")
            return True
        except Exception as e:
            print(f"Error inesperado al manejar cookies: {str(e)}")
            return False
    
    def manejar_selector_cines(self):
        """
        Maneja el modal de selección de cines.
        Obtiene la lista completa de cines disponibles y selecciona el primero del ddl.
        
        Returns:
            bool: True si se selecciono correctamente, False si hubo error critico
        """
        try:
            # Esperar a que aparezca el modal para seleccionar cines
            WebDriverWait(self.driver, 15).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "div.modal-theatre-select"))
            )
            
            # Obtener el dropdown de cines
            selector_cines = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "select.form-control"))
            )
            
            # Obtener lista de cines disponibles
            opciones_cines = selector_cines.find_elements(By.TAG_NAME, "option")[1:] #Excluye primera opcion que es seleccionar uno
            self.lista_cines = [opcion.text.strip() for opcion in opciones_cines] #Almacena los nombres de los cines en self.lista_cines
            
            if not self.lista_cines:
                raise ValueError("No se encontraron cines disponibles")
            
            print(f"Cines disponibles: {self.lista_cines}")
            
            # Seleccionar el primer cine de la lista
            self.cine_actual = self.lista_cines[0]
            selector_cines.click()
            opciones_cines[0].click()
            
            # Habilitar y hacer click en el btn Aceptar
            boton_aceptarmodal = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-primary.next"))
                )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton_aceptarmodal)
            boton_aceptarmodal.click()
            print(f"Botón Aceptar clickeado, esperando a que se cierre el modal...")

            print(f"Cine seleccionado: {self.cine_actual}")
            
            return True
            
        except (NoSuchElementException, TimeoutException, ValueError) as e:
            print(f"Error crítico al seleccionar cine: {str(e)}")
            return False
        except Exception as e:
            print(f"Error inesperado al manejar selector de cines: {str(e)}")
            return False
    
    
    def cambiar_cine(self, nombre_cine):
        """
        Cambia a un cine especifico siguiendo el orden secuencial de la lista de cines.
        Verifica tanto el nombre como la posicion correcta en el ddl.
        
        Args:
            nombre_cine (str): Nombre exacto del cine a seleccionar
            
        Returns:
            bool: True si se cambio correctamente, False si hubo error
        """
        
        try:     
            # 1 verificar que el cine existe en nuestra lista
            if nombre_cine not in self.lista_cines:
                raise ValueError(f"Cine '{nombre_cine}' no encontrado en la lista de cines disponibles: {self.lista_cines}")
                
            # 2 cerrar cualquier modal que pueda estar interfiriendo
            self.driver.execute_script("""
                const modals = document.querySelectorAll('.close-billboard-modal, .modal-backdrop');
                modals.forEach(modal => {
                    if (modal) modal.click();
                });
             """)
            time.sleep(1)
                
            # 3 abrir el selector de cines en el header
            try:
                boton_selector = WebDriverWait(self.driver, 15).until(
                   EC.element_to_be_clickable((By.CSS_SELECTOR, "header#header button.dropbtn-selector"))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton_selector)
                self.driver.execute_script("arguments[0].click();", boton_selector)
            except (TimeoutException, ElementNotInteractableException):
                raise TimeoutException("No se pudo encontrar/clickear el selector de cines")
            
            # 4 esperar a que el modal de seleccion este completamente visible
            try:
                 WebDriverWait(self.driver, 15).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "div.modal-theatre-select"))
                )
            except TimeoutException:
                raise TimeoutException("El modal de selección de cines no apareció")    
            
            # 5 localizar el ddl de cines
            try:
                selector_cines = WebDriverWait(self.driver, 15).until(
                      EC.presence_of_element_located((By.CSS_SELECTOR, "div.modal-theatre-select select.form-control"))
                )
            except TimeoutException:
                raise TimeoutException("No se encontró el dropdown de cines en el modal")
                
            # 6 obtener todas las opciones disponibles (excluyendo la primera opcion que es vacia)
            opciones = selector_cines.find_elements(By.TAG_NAME, "option")[1:]  #Excluye primera opcion (CINE del ddl)
            nombres_opciones = [opcion.text.strip() for opcion in opciones] # Lista de nombres de cines en el ddl
            print(f"Opciones disponibles en dropdown: {nombres_opciones}") # Imprime las opciones disponibles
                
             # 7 verificar que la lista de cines coincide con el dropdown
            if len(self.lista_cines) != len(nombres_opciones):
                print("Advertencia: La cantidad de cines no coincide con las opciones del dropdown")
                
             # 8 encontrar la posicion del cine en la lista original
            try:
                posicion_lista = self.lista_cines.index(nombre_cine)
                nombre_esperado = self.lista_cines[posicion_lista]
                    
                # Verificar que el nombre coincide con la opción en la misma posicion
                if posicion_lista < len(nombres_opciones):
                     nombre_real = nombres_opciones[posicion_lista]
                     if nombre_esperado != nombre_real:
                          print(f"Advertencia: Nombre no coincide en posición {posicion_lista + 1}")
                          print(f"Esperado: '{nombre_esperado}', Encontrado: '{nombre_real}'")
            except Exception as e:
                print(f"Error al verificar posición: {str(e)}")
                
             # 9 seleccionar por indice (posicion + 1 para saltar opc vacia)
            indice_seleccion = posicion_lista + 1
            try:
                self.driver.execute_script(f"""
                    const select = document.querySelector('div.modal-theatre-select select.form-control');
                    select.selectedIndex = {indice_seleccion};
                    const event = new Event('change', {{ bubbles: true }});
                    select.dispatchEvent(event);
                """)
                time.sleep(1)  # Esperar a que se aplique la seleccion
            except WebDriverException:
                raise WebDriverException("No se pudo seleccionar el cine en el dropdown")
            
             # 10 verificar que la selección se aplico correctamente
            try:
                opcion_seleccionada = selector_cines.find_elements(By.TAG_NAME, "option")[indice_seleccion]
                if opcion_seleccionada.text.strip() != nombre_cine:
                    raise ValueError("No se seleccionó el cine correcto")
            except (NoSuchElementException, IndexError):
                raise NoSuchElementException("No se pudo verificar la selección del cine")
                
            # 11 hacer click en Aceptar
            boton_aceptar = WebDriverWait(self.driver, 15).until(
                 EC.element_to_be_clickable((By.CSS_SELECTOR, "div.modal-theatre-select button.btn-primary.next"))
             )
            self.driver.execute_script("arguments[0].click();", boton_aceptar)
                
            # 12 esperar a que se cierre el modal
            WebDriverWait(self.driver, 15).until(
                  EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.modal-theatre-select"))
            )
                
             # 13 verificar que el cambio se reflejo en el btn del header
            def verificar_cambio(driver):
                try:
                       boton_header = driver.find_element(By.CSS_SELECTOR, "header#header button.dropbtn-selector")
                       texto_boton = boton_header.text.split('\n')[0].strip()
                       return nombre_cine in texto_boton
                except NoSuchElementException:
                       return False
                
            try:
                WebDriverWait(self.driver, 15).until(verificar_cambio)
            except TimeoutException:
                raise TimeoutException("El cambio de cine no se reflejó en el header")
            
            # 14 esperar a que cargue la nueva pag
            WebDriverWait(self.driver, 15).until(
                  EC.presence_of_element_located((By.CSS_SELECTOR, "div.form-group.cinemark-select > select.form-control"))
             )
                
            # 15 actualizar estado
            self.cine_actual = nombre_cine
            print(f"Cambio exitoso a cine: {nombre_cine}")
            return True
                
        except (NoSuchElementException, TimeoutException, ValueError, WebDriverException) as e:
            print(f"Error crítico al cambiar a cine {nombre_cine}: {str(e)}")
            return False
         
    
    def obtener_fechas(self):
        """
        Obtiene todas las fechas disponibles en el ddl.
        
        Returns:
            list: Lista de fechas disponibles o lista vacia si hay error
        """
        try:
            selector_fechas = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.form-group.cinemark-select > select.form-control"))
            )
            
            fechas = [opcion.text for opcion in selector_fechas.find_elements(By.TAG_NAME, "option")][1:]
            
            if not fechas:
                print("Advertencia: No se encontraron fechas disponibles")
                return []
                
            print(f"Fechas disponibles: {fechas}")
            return fechas
            
        except (NoSuchElementException, TimeoutException) as e:
            print(f"Error al obtener fechas: {str(e)}")
            return []
    
    def formatear_fecha(self, fecha_str):
        """
        Convierte fecha de formato 'MAR. 29 JUL. 2025' a '29/07/2025'.
        
        Args:
            fecha_str (str): Fecha en formato 'DIA_SEM. DIA MES. AÑO'
            
        Returns:
            str: Fecha formateada como 'dd/mm/yyyy' o la original si hay error
        """
        try:
            meses = {
                'ENE.': '01', 'FEB.': '02', 'MAR.': '03', 'ABR.': '04',
                'MAY.': '05', 'JUN.': '06', 'JUL.': '07', 'AGO.': '08',
                'SEP.': '09', 'OCT.': '10', 'NOV.': '11', 'DIC.': '12'
            }
            
            # Dividir la cadena fecha (por eje: "MAR. 29 JUL. 2025" -> ['MAR.', '29', 'JUL.', '2025'])
            partes = fecha_str.split()
            
            if len(partes) != 4:
                return fecha_str  # Si no tiene 4 partes, retornar al original
                
            dia = partes[1]  # El dia es siempre la segunda parte (ej: 29)
            mes_abrev = partes[2]  # El mes es la tercera parte (ej: JUL.)
            año = partes[3]  # El año es la cuarta parte
            
            # Obtener num de mes (ej: 'JUL.' -> '07')
            mes_num = meses.get(mes_abrev, '00')
            
            # Formatear como dd/mm/yyyy (asegurando 2 digitos para el dia)
            return f"{int(dia):02d}/{mes_num}/{año}"
            
        except Exception:
            return fecha_str  # Si algo falla, retornar la fecha original
    
    def formatear_hora(self, hora_str):
        """
        Convierte hora de formato '10:30 AM'/'2:10 PM' a formato 24h ('10:30'/'14:10').
        
        Args:
            hora_str (str): Hora en formato 'HH:MM AM/PM'
            
        Returns:
            str: Hora en formato 24h 'HH:MM' o la original si hay error
        """
        try:
            # Separar la parte del tiempo y el indicador AM/PM
            tiempo, periodo = hora_str.split()
            
            # Separar horas y minutos
            horas, minutos = tiempo.split(':')
            horas = int(horas)
            
            # Convertir a 24h / formato horas
            if periodo == 'PM' and horas != 12:
                horas += 12
            elif periodo == 'AM' and horas == 12:
                horas = 0
            
            return f"{horas:02d}:{minutos}"
        except Exception:
            return hora_str  # Si hay error, retornar la hora original
    
    def obtener_peliculas_para_fecha(self, fecha):
        """
        Obtiene peliculas disponibles para una fecha especifica.
        
        Args:
            fecha (str): Fecha para la cual buscar películas
            
        Returns:
            list: Lista de peliculas o lista vacia si hay error
        """
        try:
            # Seleccionar la fecha
            selector_fechas = Select(WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.form-group.cinemark-select > select.form-control"))
            ))
            selector_fechas.select_by_visible_text(fecha)
            
            # Esperar a que carguen las peliculas
            time.sleep(2)  # Espera para que carguen los datos
            
            # Obtener dropdown de peliculas
            selector_peliculas = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='bs-example-navbar-collapse-1']/ul/li[2]/div/select"))
            )
            
            peliculas = [opcion.text for opcion in selector_peliculas.find_elements(By.TAG_NAME, "option")][1:]
            print(f"Películas para {fecha}: {peliculas}")
            return peliculas
            
        except (NoSuchElementException, TimeoutException) as e:
            print(f"No se pudieron obtener películas para {fecha}: {str(e)}")
            return []
    
    def obtener_formatos_para_pelicula(self, fecha, pelicula):
        """
        Obtiene formatos disponibles para una pelicula en fecha especifica.
        
        Args:
            fecha (str): Fecha de la funcion
            pelicula (str): Nombre de la pelicula
            
        Returns:
            list: Lista de formatos o lista vacia si hay error
        """
        try:
            # Seleccionar la pelicula
            selector_peliculas = Select(WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='bs-example-navbar-collapse-1']/ul/li[2]/div/select"))
            ))
            selector_peliculas.select_by_visible_text(pelicula)
            
            # Esperar a que carguen los formatos
            time.sleep(2)
            
            # Obtener dropdown de formatos
            selector_formatos = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='bs-example-navbar-collapse-1']/ul/li[3]/div/select"))
            )
            
            formatos = [opcion.text for opcion in selector_formatos.find_elements(By.TAG_NAME, "option")][1:]
            print(f"Formatos para {pelicula}: {formatos}")
            return formatos
            
        except (NoSuchElementException, TimeoutException) as e:
            print(f"No se pudieron obtener formatos para {pelicula}: {str(e)}")
            return []
    
    def obtener_horarios_para_formato(self, fecha, pelicula, formato):
        """
        Obtiene horarios disponibles para un formato especifico.
        
        Args:
            fecha (str): Fecha de la función
            pelicula (str): Nombre de la película
            formato (str): Formato seleccionado
            
        Returns:
            list: Lista de horarios o lista vacia si hay error
        """
        try:
            # Seleccionar el formato
            selector_formatos = Select(WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='bs-example-navbar-collapse-1']/ul/li[3]/div/select"))
            ))
            selector_formatos.select_by_visible_text(formato)
            
            # Esperar a que carguen los horarios
            time.sleep(2)
            
            # Obtener dropdown de horarios
            selector_horarios = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='bs-example-navbar-collapse-1']/ul/li[4]/div/select"))
            )
            
            horarios = [opcion.text for opcion in selector_horarios.find_elements(By.TAG_NAME, "option")][1:]
            horarios_formateados = [self.formatear_hora(h) for h in horarios]
            print(f"Horarios para {formato}: {horarios_formateados}")
            return horarios_formateados
            
        except (NoSuchElementException, TimeoutException) as e:
            print(f"No se pudieron obtener horarios para {formato}: {str(e)}")
            return []
    
    def recolectar_datos_para_cine(self):
        """
        Recolecta todos los datos para el cine actual, clasificando correctamente por fecha actual.
        
        Returns:
            tuple: (datos_hoy, datos_proximos) - listas de diccionarios con los datos
        """
        datos_hoy = []
        datos_proximos = []
        
        try:
            # Obtener fecha actual del sistema en formato dd/mm/yyyy
            fecha_actual_sistema = datetime.now().strftime("%d/%m/%Y")
            print(f"Fecha actual del sistema: {fecha_actual_sistema}")
            
            fechas = self.obtener_fechas()
            if not fechas:
                print(f"No hay fechas disponibles para {self.cine_actual}")
                return [], []
            
            for fecha in fechas:
                fecha_formateada = self.formatear_fecha(fecha)
                print(f"\nProcesando fecha: {fecha} (Formateada: {fecha_formateada})")
                
                peliculas = self.obtener_peliculas_para_fecha(fecha)
                
                for pelicula in peliculas:
                    formatos = self.obtener_formatos_para_pelicula(fecha, pelicula)
                    
                    for formato in formatos:
                        horarios = self.obtener_horarios_para_formato(fecha, pelicula, formato)
                        
                        for horario in horarios:
                            dato = {
                                "Country": self.pais,
                                "Theater": self.cine_actual.title(),
                                "Date": fecha_formateada,
                                "Time": horario,
                                "Movie": pelicula,
                                "Format": formato
                            }
                            
                            # Clasificar segun si es la fecha actual o no
                            if fecha_formateada == fecha_actual_sistema:
                                datos_hoy.append(dato)
                            else:
                                datos_proximos.append(dato)
            
            return datos_hoy, datos_proximos
            
        except Exception as e:
            print(f"Error al recolectar datos para {self.cine_actual}: {str(e)}")
            return datos_hoy, datos_proximos
    
    def ejecutar_scraping(self):
        """Función principal que ejecuta todo el proceso de scraping."""
        if not self.driver:
            print("Error: Navegador no inicializado")
            return
        
        try:
            # Obtener y mostrar fecha actual
            fecha_actual = datetime.now(timezone.utc).astimezone().strftime("%d/%m/%Y") #Validar que los datos scrapeados son actuales
            print(f"Iniciando scraping para fecha actual: {fecha_actual}")
            
           # Paso 1: Abrir la URL principal
            print(f"Abriendo URL principal para {self.pais}...")
            self.driver.get(self.url)
            
            # Paso 2: Manejar cookies
            print("Manejando cookies...")
            if not self.aceptar_cookies():
                print("Advertencia: No se pudieron manejar las cookies, continuando...")
            
            # Paso 3: Manejar seleccion inicial de cine 
            print("Seleccionando cine inicial...")
            if not self.manejar_selector_cines():
                raise RuntimeError("No se pudo seleccionar el cine inicial - deteniendo scraping") #raise lanza error excepcion
            
            # Paso 4: Recolectar datos para todos los cines
            todos_datos_hoy = [] #Almacena funciones de hoy para todos los cines
            todos_datos_prox = [] #Almacena funciones proximas disponibles para todos los cines
            
            for idx, cine in enumerate(self.lista_cines):
                if idx > 0:  # El primer cine ya esta seleccionado. Solo para cines después del primero
                    print(f"\nCambiando a cine: {cine}")
                    if not self.cambiar_cine(cine):
                        print(f"Saltando cine {cine} debido a errores")
                        continue # Saltar al siguiente cine si falla el cambio
                
                print(f"\nRecolectando datos para cine: {cine}")
                datos_hoy, datos_prox = self.recolectar_datos_para_cine()
                
                if datos_hoy or datos_prox:
                    todos_datos_hoy.extend(datos_hoy)
                    todos_datos_prox.extend(datos_prox)
                    print(f"Datos recolectados para {cine}: {len(datos_hoy)} hoy, {len(datos_prox)} próximos")
                else:
                    print(f"No se encontraron datos para {cine}")
            
            return todos_datos_hoy, todos_datos_prox
                
        except Exception as e:
            print(f"Error durante el scraping: {str(e)}") #Captura cualquier excepción/error que pueda ocurrir durante el scraping
            return [], []
        finally:
            if self.driver:
                self.driver.quit()
                print("Navegador cerrado")

def guardar_en_excel(todos_datos_hoy, todos_datos_prox, ruta_archivo=None):
    """
    Guarda los datos en un archivo Excel con dos hojas.
    
    Args:
        todos_datos_hoy (list): Datos para la fecha actual
        todos_datos_prox (list): Datos para fechas futuras
        ruta_archivo (str, optional): Ruta personalizada para el archivo
        
    Returns:
        str: Ruta del archivo guardado
    """
    try:
        if not ruta_archivo:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            ruta_archivo = f"datos_cinemark_{timestamp}.xlsx"
        
        # Filtrar datos_hoy por si acaso hay fechas incorrectas
        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        datos_hoy_filtrados = [d for d in todos_datos_hoy if d["Date"] == fecha_actual]
        
        if len(datos_hoy_filtrados) != len(todos_datos_hoy):
            print(f"Advertencia: Se filtraron {len(todos_datos_hoy)-len(datos_hoy_filtrados)} registros con fecha incorrecta en 'Today'")
        
        # Crear DataFrames
        columnas = ["Country", "Theater", "Date", "Time", "Movie", "Format"]
        
        df_hoy = pd.DataFrame(datos_hoy_filtrados, columns=columnas) if datos_hoy_filtrados else pd.DataFrame(columns=columnas)
        df_prox = pd.DataFrame(todos_datos_prox, columns=columnas) if todos_datos_prox else pd.DataFrame(columns=columnas)
        
        # Guardar en Excel
        with pd.ExcelWriter(ruta_archivo, engine='openpyxl') as writer:
            df_hoy.to_excel(writer, sheet_name='Today', index=False)
            df_prox.to_excel(writer, sheet_name='Other schedules', index=False)
        
        print(f"\nDatos guardados en: {ruta_archivo}")
        print(f"- Hoy: {len(datos_hoy_filtrados)} funciones")
        print(f"- Próximas: {len(todos_datos_prox)} funciones")
        
        return ruta_archivo
        
    except Exception as e:
        print(f"Error crítico al guardar Excel: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        # Verificar que el driver existe en la carpeta
        ruta_driver = os.path.join(os.getcwd(), "chromedriver.exe")
        if not os.path.exists(ruta_driver):
            raise FileNotFoundError(f"No se encontró chromedriver.exe en {ruta_driver}")
        
        print("Iniciando scraping de Cinemark Centroamérica...")
        
        # Listas para acumular todos los datos
        todos_datos_hoy_global = []
        todos_datos_prox_global = []
        
        # Iterar sobre cada pais y su URL
        for pais, url in PAISES_URLS.items():
            print(f"\nIniciando scraping para {pais}...")
            scraper = ScraperCinemarkCompleto(ruta_driver, pais, url)
            datos_hoy, datos_prox = scraper.ejecutar_scraping()
            
            if datos_hoy or datos_prox:
                todos_datos_hoy_global.extend(datos_hoy)
                todos_datos_prox_global.extend(datos_prox)
                print(f"\nDatos recolectados para {pais}: {len(datos_hoy)} hoy, {len(datos_prox)} próximos")
            else:
                print(f"\nNo se encontraron datos para {pais}")
        
        # Guardar todos los datos acumulados en un solo Excel al final
        if todos_datos_hoy_global or todos_datos_prox_global:
            guardar_en_excel(todos_datos_hoy_global, todos_datos_prox_global)
        else:
            print("\nNo se recolectaron datos para ningún país")
        
    except Exception as e:
        print(f"Error inicial: {str(e)}")