import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

# Configuración básica para Chrome
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')

browser = webdriver.Chrome(options=options)

# Constantes
PAIS = "Honduras"
URL_PRINCIPAL = "https://cinepolis.com.hn/"

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
    fechas = fechas[1:3]  # Solo hoy y mañana
    for fecha in fechas:
        try:
            label = fecha.find_element(By.TAG_NAME, 'label')
            fecha_str = label.text.strip()
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
                horarios = []
                ul = peli.find_element(By.TAG_NAME, 'ul')
                for li in ul.find_elements(By.TAG_NAME, 'li'):
                    hora = li.text.strip()
                    if hora:
                        horarios.append(hora)
                for hora in horarios:
                    funciones.append({
                        'Pais': PAIS,
                        'Nombre del cine': cine_nombre,
                        'Fecha de funcion': fecha_str,
                        'hora de funcion': hora,
                        'Nombre de la pelicula': titulo,
                        'Formato de la pelicula': formato
                    })
            except Exception:
                continue
    return funciones

# Main
def main():
    todas_funciones = []
    cines = obtener_cines()
    for cine in cines:
        funciones = scrapear_funciones_cine(cine['url'], cine['nombre'])
        todas_funciones.extend(funciones)
    if todas_funciones:
        df = pd.DataFrame(todas_funciones)
        df.to_excel('cinepolis_honduras.xlsx', index=False)
    browser.quit()

if __name__ == "__main__":
    main()
