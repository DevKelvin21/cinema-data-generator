import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, WebDriverException

# Configuración básica para Chrome
def configurar_navegador():
    """Configura el navegador Chrome con opciones para scraping robusto."""
    chrome_options = Options()
    # Configuraciones para evitar detección y mejorar rendimiento
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
        # Configurar y ejecutar el scraper
        ruta_driver = os.path.join(os.getcwd(), "chromedriver.exe")
        if not os.path.exists(ruta_driver):
            raise FileNotFoundError(f"No se encontró chromedriver.exe en {ruta_driver}")
        
        service = Service(ruta_driver)
        browser = webdriver.Chrome(service=service, options=chrome_options)
        browser.set_page_load_timeout(60)
        browser.set_script_timeout(30)
        print("Navegador configurado correctamente")
        return browser
    except WebDriverException as e:
        raise RuntimeError(f"Error al iniciar el navegador: {str(e)}")

browser = configurar_navegador()

# Constantes
PAIS = "El Salvador"
URL_PRINCIPAL = "https://cinepolis.com.sv/"

# Función para obtener la lista de cines

def obtener_cines():
    browser.get(URL_PRINCIPAL)
    WebDriverWait(browser, 15).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
    time.sleep(3)
    cines = []
    for cine in browser.find_elements(By.CLASS_NAME, 'Cinema_cinema__3mgID'):
        a = cine.find_element(By.TAG_NAME, 'a')
        nombre = a.get_attribute('data-site-name')
        href = a.get_attribute('href')
        if nombre and href and nombre.strip().lower() != 'todo':
            cines.append({'nombre': nombre.strip(), 'url': href})
    return cines

# Función para scrapear funciones de un cine

def scrapear_funciones_cine(cine_url, cine_nombre):
    browser.get(cine_url)
    WebDriverWait(browser, 15).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
    time.sleep(2)
    funciones = []
    # Fechas
    fechas = browser.find_elements(By.CLASS_NAME, 'movie-date')
    fechas = fechas[1:9]  # Todas las fechas disponibles excepto la primera
    for fecha in fechas:
        try:
            label = fecha.find_element(By.TAG_NAME, 'label')
            # Obtener fecha del atributo 'for' y formatear a yyyy/mm/dd
            for_attr = label.get_attribute('for')
            # Esperado: field-movie-date-yyyy-mm-dd
            import re
            m = re.search(r'field-movie-date-(\d{4})-(\d{2})-(\d{2})', for_attr or '')
            if m:
                fecha_str = f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
            else:
                fecha_str = ''
        except NoSuchElementException:
            print(f"Advertencia: No se encontró <label> en una fecha para el cine {cine_nombre}.")
            continue
        # Click en la fecha
        try:
            label.click()
            time.sleep(2)
        except Exception:
            continue
        # Películas
        peliculas = browser.find_elements(By.CLASS_NAME, 'movie-projection')
        for peli in peliculas:
            try:
                titulo = peli.find_element(By.TAG_NAME, 'h2').text.strip()
                formato = ''
                spans = peli.find_elements(By.TAG_NAME, 'span')
                if spans:
                    partes = spans[0].text.split('|')
                    if len(partes) >= 3:
                        formato = partes[2].strip()
                # Horarios: buscar labels dentro de ul > li
                ul = peli.find_element(By.TAG_NAME, 'ul')
                for li in ul.find_elements(By.TAG_NAME, 'li'):
                    try:
                        label_hora = li.find_element(By.TAG_NAME, 'label')
                        # El texto suelto de la hora está en label_hora, antes del span
                        label_text = label_hora.get_attribute('innerHTML')
                        # Extraer la hora (antes del primer <span>)
                        import re
                        hora_match = re.search(r'>([^<]+)<span', label_hora.get_attribute('outerHTML'))
                        if hora_match:
                            hora_raw = hora_match.group(1).strip()
                        else:
                            # fallback: solo texto del label
                            hora_raw = label_hora.text.strip()
                        # Formatear a tipo hora (HH:MM)
                        from datetime import datetime
                        try:
                            hora_obj = datetime.strptime(hora_raw, '%H:%M').time()
                            hora_formateada = hora_obj.strftime('%H:%M')
                        except Exception:
                            hora_formateada = hora_raw
                        funciones.append({
                            'Pais': PAIS,
                            'Nombre del cine': cine_nombre,
                            'Fecha de funcion': fecha_str,
                            'hora de funcion': hora_formateada,
                            'Nombre de la pelicula': titulo,
                            'Formato de la pelicula': formato
                        })
                    except Exception:
                        continue
            except Exception:
                continue
    return funciones

# Main

def main():
    try:
        todas_funciones = []
        cines = obtener_cines()
        for cine in cines:
            funciones = scrapear_funciones_cine(cine['url'], cine['nombre'])
            todas_funciones.extend(funciones)
        if todas_funciones:
            df = pd.DataFrame(todas_funciones)
            df['Fecha de funcion'] = pd.to_datetime(df['Fecha de funcion'], errors='coerce').dt.strftime('%d/%m/%Y')
            # Obtener la fecha de hoy (la primera fecha válida scrapeada)
            fechas_ordenadas = df['Fecha de funcion'].drop_duplicates().tolist()
            if fechas_ordenadas:
                fecha_hoy = fechas_ordenadas[0]
                df_hoy = df[df['Fecha de funcion'] == fecha_hoy]
                # Limitar a solo los próximos 7 días (excluyendo hoy)
                fechas_siguientes = [f for f in fechas_ordenadas if f != fecha_hoy][:7]
                df_otros = df[df['Fecha de funcion'].isin(fechas_siguientes)]
                with pd.ExcelWriter('cinepolis_el_salvador.xlsx', engine='openpyxl') as writer:
                    df_hoy.to_excel(writer, sheet_name='Hoy', index=False)
                    df_otros.to_excel(writer, sheet_name='Otras fechas', index=False)
            else:
                df.to_excel('cinepolis_el_salvador.xlsx', index=False)
        print("\nProceso completado. Datos guardados en cinepolis_el_salvador.xlsx")
    except Exception as e:
        print(f"Error en la ejecución principal: {str(e)}")
    finally:
        if browser:
            browser.quit()
            print("Navegador cerrado correctamente")

if __name__ == "__main__":
    main()
