from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
import time
import pandas as pd
from datetime import datetime
from openpyxl import load_workbook
import os
from typing import Optional, Dict, List

# Configuración del WebDriver - mejorada para cross-platform
def initialize_webdriver():
    """Inicializa el webdriver con configuración cross-platform"""
    driver_path = 'msedgedriver.exe' if os.name == 'nt' else 'msedgedriver'
    service = Service(executable_path=driver_path)
    options = webdriver.EdgeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Edge(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

# Inicializar el navegador globalmente
browser = initialize_webdriver()

# Función para esperar y encontrar un elemento
def wait_and_find_element(by, value, wait_time=10) -> Optional[webdriver.remote.webelement.WebElement]:
    """Espera a que un elemento esté presente en el DOM y lo retorna"""
    try:
        return WebDriverWait(browser, wait_time).until(
            EC.presence_of_element_located((by, value))
        )
    except TimeoutException:
        print(f"Elemento {value} no encontrado.")
        return None

# Función para esperar a que un elemento sea clicable y hacer clic
def wait_and_click_element(by, value, wait_time=10) -> bool:
    """Espera a que un elemento sea clicable y hace clic en él"""
    try:
        element = WebDriverWait(browser, wait_time).until(
            EC.element_to_be_clickable((by, value))
        )
        browser.execute_script("arguments[0].scrollIntoView(true);", element)
        element.click()
        return True
    except TimeoutException:
        print(f"El elemento {value} no estuvo disponible para hacer clic.")
        return False
    except StaleElementReferenceException:
        print(f"El elemento {value} ya no es accesible en el DOM.")
        return False

# Función para cerrar el popup si aparece
def close_popup(wait_time=6) -> bool:
    """Cierra el popup si aparece en la página"""
    try:
        close_button = WebDriverWait(browser, wait_time).until(
            EC.element_to_be_clickable((By.ID, 'takeover-close'))
        )
        close_button.click()
        print("Popup cerrado.")
        return True
    except TimeoutException:
        print("No apareció ningún popup.")
        return False

# Función para obtener la fecha actual en el formato deseado
def get_current_date() -> str:
    """Retorna la fecha actual en formato DD-MM-YYYY"""
    return datetime.now().strftime("%d-%m-%Y")

# Función para determinar el país basado en la extensión de la URL
def determine_country(url: str) -> str:
    """Determina el país basado en la extensión de la URL"""
    country_mapping = {
        ".sv": "El Salvador",
        ".gt": "Guatemala", 
        ".cr": "Costa Rica",
        ".pa": "Panamá"
    }
    
    for extension, country in country_mapping.items():
        if extension in url:
            return country
    return "Desconocido"

# Crear el DataFrame con estructura mejorada
movie_data: Dict[str, List] = {
    'Fecha': [],
    'País': [],
    'Cine': [],
    'Nombre Cine': [],
    'Titulo': [],
    'Idioma': [],
    'Hora': [],
    'Formato': [] 
}

# Función para extraer información de las películas, con reintentos
def extract_movie_info_with_retries() -> None:
    """Extrae información de películas con reintentos automáticos"""
    attempts = 2
    while attempts > 0:
        try:
            extract_movie_information()
            break  # Salir del bucle si la extracción fue exitosa
        except Exception as e:
            print(f"Error al extraer información de películas: {e}")
            attempts -= 1
            if attempts > 0:
                print("Intentando nuevamente...")
            else:
                print("Se agotaron los intentos para esta ciudad.")

# Función para extraer información de las películas
def extract_movie_information() -> None:
    """Extrae la información de las películas según el país"""
    global is_panama_site
    current_url = browser.current_url
    is_panama_site = ".pa" in current_url
    
    if is_panama_site:
        extract_panama_movie_data()
    else:
        extract_other_countries_movie_data()

def extract_panama_movie_data() -> None:
    """Lógica específica para extraer datos del sitio de Panamá"""
    print("Procesando información para Panamá")

    # Esperar y encontrar elementos
    cinema_list = wait_and_find_element(By.CLASS_NAME, 'listaCarteleraHorario')
    
    if cinema_list:
        # Encontrar todos los cines
        cinemas = cinema_list.find_elements(By.CLASS_NAME, 'divComplejo')
        for cinema in cinemas:
            try:
                cinema_name_element = cinema.find_element(By.TAG_NAME, 'h2')
                cinema_name = cinema_name_element.text if cinema_name_element else "Desconocido"
                cinema_name = cinema_name.rstrip('?').strip()

                dates = cinema.find_elements(By.CLASS_NAME, 'divFecha')
                for date in dates:
                    movies = date.find_elements(By.CLASS_NAME, 'tituloPelicula')
                    for movie in movies:
                        title = movie.find_element(By.CLASS_NAME, 'datalayer-movie').text
                        formats = movie.find_elements(By.CLASS_NAME, 'horarioExp')
                        for format_element in formats:
                            format_type = format_element.find_element(By.CLASS_NAME, 'col3').text
                            
                            # Inicializar formato como "2D" por defecto
                            movie_format = "2D"
                            
                            # Verificar si hay una imagen con clase 3D
                            try:
                                format_element.find_element(By.XPATH, ".//img[contains(@src, '3d.png')]")
                                movie_format = "3D"
                            except NoSuchElementException:
                                pass  # No encontró la imagen, formato sigue siendo "2D"
                            
                            # Verificar si hay una imagen con clase 4D
                            try:
                                format_element.find_element(By.XPATH, ".//img[contains(@src, '4d.png')]")
                                movie_format = "4D"
                            except NoSuchElementException:
                                pass  # No encontró la imagen, formato sigue siendo el actual
                            
                            times = format_element.find_elements(By.CLASS_NAME, 'btnhorario')
                            for time_element in times:
                                time_text = time_element.text
                                add_movie_data_entry(cinema_name, title, format_type, time_text, movie_format)
                                
            except NoSuchElementException:
                print(f"Algunos elementos no se encontraron en {cinema_name}.")
                continue

def extract_other_countries_movie_data() -> None:
    """Lógica para extraer datos de otros países (El Salvador, Guatemala, Costa Rica)"""
    try:
        main_billboard_content = wait_and_find_element(By.CLASS_NAME, 'contenido-cartelera-principal')
        if main_billboard_content:
            list_billboards = main_billboard_content.find_element(By.ID, 'listBillboards')
            billboards = list_billboards.find_elements(By.CLASS_NAME, 'ScheduleMovie__ScheduleMovieComponent-sc-7752wm-0')

            for billboard in billboards:
                try:
                    cinema_name_element = billboard.find_element(By.TAG_NAME, 'h2')
                    cinema_name = cinema_name_element.text if cinema_name_element else "Desconocido"

                    header_element = billboard.find_element(By.TAG_NAME, 'h3')
                    header = header_element.text if header_element else "Sin encabezado"

                    movies = billboard.find_elements(By.CLASS_NAME, 'SingleScheduleMovie__SingleScheduleComponent-sc-1n3hti2-0')
                    for movie in movies:
                        title = movie.find_element(By.CLASS_NAME, 'nombre').find_element(By.TAG_NAME, 'h3').text
                        formats = movie.find_element(By.CLASS_NAME, 'contenedor-formatos').find_elements(By.CLASS_NAME, 'formato')
                        for format_element in formats:
                            format_type = format_element.find_element(By.CLASS_NAME, 'formato-nombre').text
                            times = format_element.find_element(By.CLASS_NAME, 'horas').find_elements(By.TAG_NAME, 'a')
                            for time_element in times:
                                time_text = time_element.find_element(By.TAG_NAME, 'p').text
                                
                                # Verificar si es formato 3D o 4D
                                final_format = "2D"  # Valor por defecto
                                try:
                                    format_element.find_element(By.XPATH, ".//img[contains(@src, '3d.png')]")
                                    final_format = "3D"
                                except NoSuchElementException:
                                    pass  # No encontró la imagen 3D
                                
                                try:
                                    format_element.find_element(By.XPATH, ".//img[contains(@src, '4d.png')]")
                                    final_format = "4D"
                                except NoSuchElementException:
                                    pass  # No encontró la imagen 4D

                                add_movie_data_entry(cinema_name, title, format_type, time_text, final_format)
                                
                except NoSuchElementException:
                    print(f"Algunos elementos no se encontraron en {cinema_name}.")
                    continue
    except NoSuchElementException:
        print("No se pudo encontrar la cartelera principal.")

def add_movie_data_entry(cinema_name: str, title: str, language: str, time: str, format_type: str) -> None:
    """Agrega una entrada de datos de película al diccionario global"""
    movie_data['Fecha'].append(get_current_date())
    movie_data['País'].append(determine_country(browser.current_url))
    movie_data['Cine'].append("Cinepolis")
    movie_data['Nombre Cine'].append(cinema_name)
    movie_data['Titulo'].append(title)
    movie_data['Idioma'].append(language)
    movie_data['Hora'].append(time)
    movie_data['Formato'].append(format_type)


# Función para procesar una URL
def process_url(url: str) -> None:
    """Procesa una URL específica de Cinépolis"""
    global is_panama_site
    browser.get(url)

    # Esperar a que el popup aparezca y cerrarlo si está presente
    close_popup()
    is_panama_site = ".pa" in url

    # Esperar a que el menú se cargue
    if is_panama_site:
        wait_and_find_element(By.CLASS_NAME, 'contentBusqueda')
    else:
        wait_and_find_element(By.ID, 'header-principal')

    # Bucle principal para iterar sobre las ciudades
    processed_cities = set()  # Para llevar un registro de las ciudades ya procesadas

    while True:
        try:
            # Seleccionar el elemento de la ciudad según el valor de is_panama_site
            if is_panama_site:
                city_select = wait_and_find_element(By.ID, 'cmbCiudades')
            else:
                city_select = wait_and_find_element(By.ID, 'ciudad')
            
            if not city_select:
                print("No se pudo encontrar el selector de ciudades.")
                break
                
            cities = city_select.find_elements(By.TAG_NAME, 'option')

            if not cities:
                print("No se encontraron opciones de ciudad.")
                break

            # Ignorar la primera opción
            for city in cities[1:]:
                city_value = city.get_attribute('value')
                if city_value and city_value not in processed_cities:
                    city.click()
                    processed_cities.add(city_value)
                    time.sleep(3)
                    
                    if is_panama_site:
                        wait_and_click_element(By.CSS_SELECTOR, 'input.btn.btnEnviar.btnVerCartelera')
                    else:
                        wait_and_click_element(By.XPATH, '//button[text()="VER CARTELERA"]')
                    
                    time.sleep(5)
                    extract_movie_information()

                    # Actualizar el elemento select de ciudades después de hacer clic
                    if is_panama_site:
                        city_select = wait_and_find_element(By.ID, 'cmbCiudades')
                    else:
                        city_select = wait_and_find_element(By.ID, 'ciudad')

                    if city_select:
                        cities = city_select.find_elements(By.TAG_NAME, 'option')

        except StaleElementReferenceException:
            print("Elemento obsoleto encontrado, actualizando la lista de ciudades.")
            continue

        # Salir del bucle si ya se procesaron todas las ciudades
        if city_select:
            available_cities = [city for city in city_select.find_elements(By.TAG_NAME, 'option')[1:] 
                              if city.get_attribute('value')]
            if len(processed_cities) >= len(available_cities):
                print("Todas las ciudades han sido procesadas.")
                break
        else:
            break

def save_data_to_excel() -> str:
    """Guarda los datos extraídos en un archivo Excel y retorna el nombre del archivo"""
    df = pd.DataFrame(movie_data)
    filename = f'Cinepolis_{get_current_date()}.xlsx'
    df.to_excel(filename, index=False)
    print(f'Archivo Excel guardado como {filename}')

    # Ajustar el ancho de las columnas
    wb = load_workbook(filename)
    ws = wb.active

    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column_letter].width = adjusted_width

    wb.save(filename)
    print(f'Ancho de columnas ajustado en {filename}')
    return filename

def main() -> None:
    """Función principal que ejecuta todo el proceso de scraping"""
    try:
        # Procesar las URLs de Cinépolis
        cinepolis_urls = [
            "https://cinepolis.com.sv/",
            "https://cinepolis.com.gt/",
            "https://cinepolis.co.cr/",
            "https://cinepolis.com.pa/"
        ]

        print("Iniciando proceso de extracción de datos de Cinépolis...")
        
        for url in cinepolis_urls:
            print(f"Procesando: {url}")
            process_url(url)

        # Guardar datos en Excel
        filename = save_data_to_excel()
        print(f"Proceso completado. Total de registros extraídos: {len(movie_data['Fecha'])}")
        
    except Exception as e:
        print(f"Error durante la ejecución: {e}")
    finally:
        browser.quit()
        print("Navegador cerrado.")

# Ejecutar el programa principal
if __name__ == "__main__":
    main()
