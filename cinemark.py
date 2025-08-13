import os
import time
import random
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

# Diccionario de url y su respectivo pais
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
        """
        self.ruta_driver = ruta_driver
        self.pais = pais
        self.url = url
        self.driver = None
        self.cine_actual = ""
        self.lista_cines = []
        self.configurar_navegador(headless=True)
        
    def configurar_navegador(self, headless=True):
        """Configura el navegador Chrome con opciones para scraping robusto."""
        chrome_options = Options()
        
        # Configuración para modo headless o visible
        if headless:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
        
        # Configuración para evitar detección
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Perfil persistente
        profile_path = os.path.join(os.getcwd(), "chrome_profile")
        if not os.path.exists(profile_path):
            os.makedirs(profile_path)
        chrome_options.add_argument(f"--user-data-dir={profile_path}")
        
        # User-Agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        ]
        chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")
        
        # Configuraciones para suprimir errores o warnings
        chrome_options.add_argument("--disable-direct-composition")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        
        # Configuracion del servicio
        servicio = Service(executable_path=self.ruta_driver)
        
        try:
            self.driver = webdriver.Chrome(service=servicio, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            self.driver.set_script_timeout(30)
            print("Navegador headless configurado correctamente" if headless else "Navegador configurado correctamente (visible)")
        except WebDriverException as e:
            raise RuntimeError(f"Error al iniciar el navegador: {str(e)}")
    
    def esperar_captcha(self, timeout=200):
        """Espera a que el usuario resuelva el CAPTCHA manualmente en navegador visible,
        luego cambia a modo headless para el resto del scraping."""
        try:
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.invisibility_of_element_located((By.ID, "challenge-widget-container")))
                return True
            except TimeoutException:
                pass
            
            print("\n--- CAPTCHA DETECTADO ---")
            print("Por favor resuelve el CAPTCHA en el navegador...")
            
            # Guardar la URL actual antes de cerrar
            current_url = self.driver.current_url
            
            # Configurar navegador visible temporalmente
            self.driver.quit()  # Cerrar la instancia actual
            self.configurar_navegador(headless=False)  # Crear nueva instancia visible
            
            # Recargar la página
            self.driver.get(current_url)
            
            # Esperar a que aparezca el CAPTCHA
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "challenge-widget-container")))
            
            # Esperar interacción humana
            print("\nPor favor resuelve el CAPTCHA en el navegador...")
            print("Una vez resuelto, presiona ENTER en la consola para continuar...")
            input()
            
            print("CAPTCHA resuelto, reiniciando navegador en modo headless...")
            
            # Volver a modo headless
            current_url = self.driver.current_url
            self.driver.quit()
            self.configurar_navegador(headless=True)  # Reconfigura con opciones originales
            self.driver.get(current_url)  # Recargar página con sesión persistente
            
            # Verificar que el CAPTCHA sigue resuelto
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.invisibility_of_element_located((By.ID, "challenge-widget-container")))
                print("CAPTCHA verificado, continuando con scraping...")
                return True
            except TimeoutException:
                print("Error: El CAPTCHA no se resolvió correctamente")
                return False
            
        except Exception as e:
            print(f"Error al manejar CAPTCHA: {str(e)}")
            return False
    
    def aceptar_cookies(self):
        """Intenta aceptar las cookies si aparece el popup."""
        try:
            boton_cookies = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.modal-cookies__accept-button")))
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
        """Maneja el modal de selección de cines y obtiene la lista completa."""
        try:
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "div.modal-theatre-select")))
            
            selector_cines = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "select.form-control")))
            
            opciones_cines = selector_cines.find_elements(By.TAG_NAME, "option")[1:]
            self.lista_cines = [opcion.text.strip() for opcion in opciones_cines]
            
            if not self.lista_cines:
                raise ValueError("No se encontraron cines disponibles")
            
            print(f"Cines disponibles: {self.lista_cines}")
            
            # Seleccionar el primer cine de la lista
            self.cine_actual = self.lista_cines[0]
            selector_cines.click()
            opciones_cines[0].click()
            
            boton_aceptarmodal = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-primary.next"))
                )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton_aceptarmodal)
            boton_aceptarmodal.click()

            print(f"Cine seleccionado: {self.cine_actual}")
            return True
            
        except (NoSuchElementException, TimeoutException, ValueError) as e:
            print(f"Error crítico al seleccionar cine: {str(e)}")
            return False
        except Exception as e:
            print(f"Error inesperado al manejar selector de cines: {str(e)}")
            return False
    
    def cambiar_cine(self, nombre_cine):
        """Cambia a un cine específico solo si no es el cine actual."""
        if self.cine_actual == nombre_cine:
            return True
            
        try:     
            if nombre_cine not in self.lista_cines:
                raise ValueError(f"Cine '{nombre_cine}' no encontrado en la lista de cines disponibles")
                
            self.driver.execute_script("""
                const modals = document.querySelectorAll('.close-billboard-modal, .modal-backdrop');
                modals.forEach(modal => {
                    if (modal) modal.click();
                });
             """)
            time.sleep(0.5)
                
            try:
                boton_selector = WebDriverWait(self.driver, 10).until(
                   EC.element_to_be_clickable((By.CSS_SELECTOR, "header#header button.dropbtn-selector"))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton_selector)
                self.driver.execute_script("arguments[0].click();", boton_selector)
            except (TimeoutException, ElementNotInteractableException):
                raise TimeoutException("No se pudo encontrar/clickear el selector de cines")
            
            try:
                 WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "div.modal-theatre-select"))
                )
            except TimeoutException:
                raise TimeoutException("El modal de selección de cines no apareció")    
            
            # Selectores alternativos para el dropdown de cines
            selectores_alternativos = [
                "div.modal-theatre-select select.form-control", 
                "div.modal-theatre-select select",               
                "select.form-control",                           
                "div.cinemark-select select",                    
                "div.form-group > select"                        
            ]

            selector_cines = None
            for selector in selectores_alternativos:
                try:
                    selector_cines = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not selector_cines:
                raise TimeoutException("No se encontró el dropdown de cines en el modal")
                    
            opciones = selector_cines.find_elements(By.TAG_NAME, "option")[1:]
            nombres_opciones = [opcion.text.strip() for opcion in opciones]
                
            if len(self.lista_cines) != len(nombres_opciones):
                print("Advertencia: La cantidad de cines no coincide con las opciones del dropdown")
                
            try:
                posicion_lista = self.lista_cines.index(nombre_cine)
                nombre_esperado = self.lista_cines[posicion_lista]
                    
                if posicion_lista < len(nombres_opciones):
                     nombre_real = nombres_opciones[posicion_lista]
                     if nombre_esperado != nombre_real:
                          print(f"Advertencia: Nombre no coincide en posición {posicion_lista + 1}")
                          print(f"Esperado: '{nombre_esperado}', Encontrado: '{nombre_real}'")
            except Exception as e:
                print(f"Error al verificar posición: {str(e)}")
                
            indice_seleccion = posicion_lista + 1
            try:
                self.driver.execute_script(f"""
                    const select = document.querySelector('div.modal-theatre-select select.form-control');
                    select.selectedIndex = {indice_seleccion};
                    const event = new Event('change', {{ bubbles: true }});
                    select.dispatchEvent(event);
                """)
                time.sleep(0.5)
            except WebDriverException:
                raise WebDriverException("No se pudo seleccionar el cine en el dropdown")
            
            try:
                opcion_seleccionada = selector_cines.find_elements(By.TAG_NAME, "option")[indice_seleccion]
                if opcion_seleccionada.text.strip() != nombre_cine:
                    raise ValueError("No se seleccionó el cine correcto")
            except (NoSuchElementException, IndexError):
                raise NoSuchElementException("No se pudo verificar la selección del cine")
                
            boton_aceptar = WebDriverWait(self.driver, 10).until(
                 EC.element_to_be_clickable((By.CSS_SELECTOR, "div.modal-theatre-select button.btn-primary.next"))
             )
            self.driver.execute_script("arguments[0].click();", boton_aceptar)
                
            WebDriverWait(self.driver, 10).until(
                  EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.modal-theatre-select"))
            )
                
            def verificar_cambio(driver):
                try:
                       boton_header = driver.find_element(By.CSS_SELECTOR, "header#header button.dropbtn-selector")
                       texto_boton = boton_header.text.split('\n')[0].strip()
                       return nombre_cine in texto_boton
                except NoSuchElementException:
                       return False
                
            try:
                WebDriverWait(self.driver, 10).until(verificar_cambio)
            except TimeoutException:
                raise TimeoutException("El cambio de cine no se reflejó en el header")
            
            selectores_alternativos_post = [
                "div.form-group.cinemark-select > select.form-control",
                "select.form-control",
                "div.cinemark-select select",
                "div.form-group > select"
            ]

            for selector in selectores_alternativos_post:
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
                
            self.cine_actual = nombre_cine
            print(f"Cambio exitoso a cine...")
            return True
                
        except (NoSuchElementException, TimeoutException, ValueError, WebDriverException) as e:
            print(f"Error crítico al cambiar a cine {nombre_cine}: {str(e)}")
            return False
    
    def obtener_fechas(self):
        """Obtiene todas las fechas disponibles en el ddl."""
        
        selectores_alternativos = [
            "div.form-group.cinemark-select > select.form-control", 
            "select.form-control",                                 
            "div.cinemark-select select",                           
            "div.form-group > select"                               
        ]
        
        for selector in selectores_alternativos:
            try:
                selector_fechas = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                
                # Obtener opciones excluyendo la primera (FECHA)
                opciones = selector_fechas.find_elements(By.TAG_NAME, "option")[1:]
                fechas = [opcion.text for opcion in opciones]
                
                if fechas:
                   print(f"Fechas encontradas: {len(fechas)}")
                   return fechas
                if not fechas:
                    print("Advertencia: No se encontraron fechas disponibles")
                    return []
                
            except (NoSuchElementException, TimeoutException) as e:
                print(f"Error al obtener fechas: {str(e)}")
                return []
    
    def formatear_fecha(self, fecha_str):
        """Convierte fecha de formato 'MAR. 29 JUL. 2025' a '29/07/2025'."""
        try:
            meses = {
                'ENE.': '01', 'FEB.': '02', 'MAR.': '03', 'ABR.': '04',
                'MAY.': '05', 'JUN.': '06', 'JUL.': '07', 'AGO.': '08',
                'SEP.': '09', 'OCT.': '10', 'NOV.': '11', 'DIC.': '12'
            }
            
            partes = fecha_str.split()
            
            if len(partes) != 4:
                return fecha_str
                
            dia = partes[1]
            mes_abrev = partes[2]
            año = partes[3]
            
            mes_num = meses.get(mes_abrev, '00')
            
            return f"{int(dia):02d}/{mes_num}/{año}"
            
        except Exception:
            return fecha_str
    
    def formatear_hora(self, hora_str):
        """Convierte hora de formato '10:30 AM'/'2:10 PM' a formato 24h ('10:30'/'14:10')."""
        try:
            tiempo, periodo = hora_str.split()
            horas, minutos = tiempo.split(':')
            horas = int(horas)
            
            if periodo == 'PM' and horas != 12:
                horas += 12
            elif periodo == 'AM' and horas == 12:
                horas = 0
            
            return f"{horas:02d}:{minutos}"
        except Exception:
            return hora_str
    
    def obtener_peliculas_para_fecha(self, fecha):
        """Obtiene peliculas disponibles para una fecha especifica."""
        try:
            selector_fechas = Select(WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.form-group.cinemark-select > select.form-control"))
            ))
            selector_fechas.select_by_visible_text(fecha)
            
            time.sleep(1)
            
            selector_peliculas = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='bs-example-navbar-collapse-1']/ul/li[2]/div/select"))
            )
            
            peliculas = [opcion.text for opcion in selector_peliculas.find_elements(By.TAG_NAME, "option")][1:]
            print(f"Procesando {fecha} - {len(peliculas)} películas encontradas")
            return peliculas
            
        except (NoSuchElementException, TimeoutException) as e:
            print(f"No se pudieron obtener películas para {fecha}")
            return []
    
    def obtener_formatos_para_pelicula(self, fecha, pelicula):
        """Obtiene formatos disponibles para una pelicula en fecha especifica."""
        try:
            selector_peliculas = Select(WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='bs-example-navbar-collapse-1']/ul/li[2]/div/select")))
            )
            selector_peliculas.select_by_visible_text(pelicula)
            
            time.sleep(1)
            
            selector_formatos = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='bs-example-navbar-collapse-1']/ul/li[3]/div/select"))
            )
            
            formatos = [opcion.text for opcion in selector_formatos.find_elements(By.TAG_NAME, "option")][1:]
            return formatos
            
        except (NoSuchElementException, TimeoutException):
            return []
    
    def obtener_horarios_para_formato(self, fecha, pelicula, formato):
        """Obtiene horarios disponibles para un formato especifico."""
        try:
            selector_formatos = Select(WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='bs-example-navbar-collapse-1']/ul/li[3]/div/select"))
            ))
            selector_formatos.select_by_visible_text(formato)
            
            time.sleep(0.5)
            
            selector_horarios = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='bs-example-navbar-collapse-1']/ul/li[4]/div/select"))
            )
            
            horarios = [opcion.text for opcion in selector_horarios.find_elements(By.TAG_NAME, "option")][1:]
            horarios_formateados = [self.formatear_hora(h) for h in horarios]
            return horarios_formateados
            
        except (NoSuchElementException, TimeoutException):
            return []
    
    def recolectar_datos_para_cine(self):
        """
        Recolecta datos para el cine actual.
        Si hoy no está disponible, no genera datos para 'Today'.
        Procesa hasta 7 fechas futuras.
        """
        datos_hoy = []
        datos_proximos = []
        
        try:
            hoy = datetime.now()
            fecha_actual_sistema = hoy.strftime("%d/%m/%Y")
            
            fechas_disponibles = self.obtener_fechas()
            if not fechas_disponibles:
                print(f"No hay fechas disponibles para {self.cine_actual}")
                return [], []
            
            # Convertir fechas a objetos datetime para comparación
            fechas_con_objetos = []
            for fecha in fechas_disponibles:
                fecha_formateada = self.formatear_fecha(fecha)
                try:
                    dia, mes, año = fecha_formateada.split('/')
                    fecha_obj = datetime(int(año), int(mes), int(dia))
                    fechas_con_objetos.append((fecha, fecha_formateada, fecha_obj))
                except:
                    continue
            
            # Ordenar fechas por fecha_obj
            fechas_con_objetos.sort(key=lambda x: x[2])
            
            # Seleccionar fechas a procesar (hoy si existe + hasta 7 futuras)
            fechas_a_procesar = []
            hoy_encontrado = False
            
            for fecha, fecha_formateada, fecha_obj in fechas_con_objetos:
                if fecha_obj.date() == hoy.date():
                    fechas_a_procesar.append((fecha, fecha_formateada, True))  # True = es hoy
                    hoy_encontrado = True
                elif fecha_obj.date() > hoy.date() and len(fechas_a_procesar) - int(hoy_encontrado) < 7:
                    fechas_a_procesar.append((fecha, fecha_formateada, False))  # False = no es hoy
            
            if not fechas_a_procesar:
                print("No hay fechas válidas para procesar")
                return [], []
            
            if hoy_encontrado:
                print(f"Fecha de hoy encontrada: {fecha_actual_sistema}")
            else:
                print("No se encontró la fecha de hoy en las disponibles")
            
            # Procesar cada fecha
            for fecha, fecha_formateada, es_hoy in fechas_a_procesar:
                print(f"\nProcesando fecha: {fecha} (Formateada: {fecha_formateada}) - {'Hoy' if es_hoy else 'Próxima'}")
                
                peliculas = self.obtener_peliculas_para_fecha(fecha)
                if not peliculas:
                    print("No hay películas para esta fecha")
                    continue
                
                for pelicula in peliculas:
                    formatos = self.obtener_formatos_para_pelicula(fecha, pelicula)
                    if not formatos:
                        print(f"No hay formatos para {pelicula}")
                        continue
                    
                    for formato in formatos:
                        horarios = self.obtener_horarios_para_formato(fecha, pelicula, formato)
                        if not horarios:
                            print(f"No hay horarios para {pelicula} - {formato}")
                            continue
                        
                        for horario in horarios:
                            dato = {
                                "Country": self.pais,
                                "Theater": self.cine_actual.title(),
                                "Date": fecha_formateada,
                                "Time": horario,
                                "Movie": pelicula,
                                "Format": formato
                            }
                            
                            if es_hoy:
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
            return [], []
        
        try:
            fecha_actual = datetime.now(timezone.utc).astimezone().strftime("%d/%m/%Y")
            print(f"Iniciando scraping para fecha actual: {fecha_actual}")
            
            print(f"Abriendo URL principal para {self.pais}...")
            self.driver.get(self.url)
            
            if not self.esperar_captcha():
                print("No se resolvió el CAPTCHA, saltando este país...")
                return [], []
            
            print("Manejando cookies...")
            if not self.aceptar_cookies():
                print("Advertencia: No se pudieron manejar las cookies, continuando...")
            
            print("Seleccionando cine inicial...")
            if not self.manejar_selector_cines():
                raise RuntimeError("No se pudo seleccionar el cine inicial - deteniendo scraping")
            
            todos_datos_hoy = []
            todos_datos_prox = []
            cines_procesados = set()  # Evita procesar cines duplicados
            
            for idx, cine in enumerate(self.lista_cines):
                if cine in cines_procesados:
                    print(f"\nCine {cine} ya procesado, saltando...")
                    continue
                    
                if idx > 0:
                    print(f"\nCambiando a cine: {cine}")
                    if not self.cambiar_cine(cine):
                        print(f"Saltando cine {cine} debido a errores")
                        continue
                
                print(f"\nRecolectando datos para cine...")
                datos_hoy, datos_prox = self.recolectar_datos_para_cine()
                
                if datos_hoy or datos_prox:
                    todos_datos_hoy.extend(datos_hoy)
                    todos_datos_prox.extend(datos_prox)
                    cines_procesados.add(cine) 
                    print(f"Datos recolectados para {cine}: {len(datos_hoy)} hoy, {len(datos_prox)} próximos")
                else:
                    print(f"No se encontraron datos para {cine}")
            
            return todos_datos_hoy, todos_datos_prox
                
        except Exception as e:
            print(f"Error durante el scraping: {str(e)}")
            return [], []
        finally:
            if self.driver:
                self.driver.quit()
                print("Navegador cerrado")

def guardar_en_excel(todos_datos_hoy, todos_datos_prox, ruta_archivo=None):
    """
    Guarda los datos en un archivo Excel con dos hojas.
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