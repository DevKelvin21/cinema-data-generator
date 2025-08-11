# Proyecto Final:

### Descripcion:

Crear un script de python que cree un archivo excell con informacion sobre la cadena de cinepolis en El Salvador.

El archivo debe recopilar:
- Pais (El Salvador)
- Nombre del cine (especifico para cada local)
- Fecha de funcion
- hora de funcion
- Nombre de la pelicula
- Formato de la pelicula

#### Fuente de los datos:

Recolectar los datos de `https://cinepolis.com.sv/` usando estrategias de webscraping, usando los las librerias de los requerimientos listados en `requirements.txt`

#### Estrategia de desarrollo:

Implementar un script basandose en los scripts previamente creados, por ejemplo, `cinepolis_sandbox.py`


#### Estructura de la pagina:

1. **Seleccionar cine**
- class: `Tab_tabListItem__3d-NC`
- text: `Seleccionar un cine`
- description: Tab para clickear seleccionar cines, una vez presionado este boton, despliega la lista de los cines disponibles

2. **Lista de cines**
- class per item: `Cinema_cinema__3mgID`
- content: This div contains an `a` tag that has it's own `data-site-name` parameter, wich contains the name of the cinema. Within it, it contains the name of the cinema, enclosed in an `h4` tag
- description: Este div es una tarjeta que te lleva a navegar hacia la pagina del teatro local, al darle click, se redirecciona la pagina a `cinepolis.com.sv/cinema/<nombre del cine>`

3. **Fecha de pelicula**
- class: `movie-date`
- content: un `label` tag con `for=` que contiene la fecha en formato `field-movie-date-<yyyy-mm-dd>`, el contenido del label, incluye un string con el dia de la semana abreviado, no sera necesario aparentemente.

4. **Tarjeta de pelicula**
- class: `movie-projection movie-projection-alt`
- content:

  a. un `h2` con el titulo de la pelicula a extraerse

  b. un `span` con un texto que sigue el siguiente estilo: `<Clasificacion> | <duracion de pelicula> | <Formato>`

  c. un `ul` con una serie de `li` que contienen los horarios de pelicula
  
5. **pill de horario**
  
  - Content: un label, con la hora de la pelicula, ademas de un span, que contiene el formato de dicha pelicula

#### RUTINA:

1. Entrar en `cinepolis.com.sv`: Datos fijos a recolectar: 
  
  - pais, fijo, El Salvador 

2. Clickear en `Seleccionar cine`

3. Para cada uno de los teatros: 

    3.1: Recolectar: - Nombre del cine
    
    3.2: clickear en el teatro

    3.3: Seleccionar primer y segundo elemento de `Fecha de pelicula` para cada uno:

      3.3.1: Recolectar: - Fecha de pelicula

      3.3.2: Seleccionar todas las peliculas, para cada `Tarjeta de pelicula`: 
      
      3.3.2.1: Recolectar: - Nombre de pelicula

      3.3.2.2: Para cada `Pill de horario` de la tarjeta: 

      3.3.2.2.1: -Recolectar: hora de la pelicula, formato de la pelicula

### OBJETIVO:

Recolectar los datos de tal manera, que para cada funcion de cine, recolectado de todas las Pills, aparezca en una tabla, el Pais, el Nombre del cine, fecha de la pelicula, el nombre de la pleicula, la hora de la pelicula y el formato de la pelicula

de tal manera que para todas las funciones, de todos los cines, exista una entrada en la tabla con los datos requeridos.
