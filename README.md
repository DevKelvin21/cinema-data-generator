# Cinema Data Generator 🎬

**Trabajo Final - Curso de Business Intelligence y Big Data**

Este proyecto es un generador de datos para análisis de información cinematográfica, desarrollado como proyecto final del curso de Business Intelligence y Big Data.

## 📋 Requisitos del Sistema

- **Python**: 3.13.3
- **Sistema Operativo**: macOS, Linux o Windows
- **Git**: Para control de versiones
-**Navegador**: Tener Google Chrome instalado en tu sistema

## 🚀 Configuración del Entorno de Desarrollo

### 1. Clonar el Repositorio

```bash
git clone https://github.com/DevKelvin21/cinema-data-generator.git
cd cinema-data-generator
```

### 2. Crear y Activar Entorno Virtual

Es **obligatorio** trabajar con un entorno virtual para mantener las dependencias aisladas:

#### En macOS/Linux:
```bash
python3.13 -m venv venv
source venv/bin/activate
```

#### En Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar Dependencias

Una vez activado el entorno virtual, instala todas las librerías necesarias:

```bash
pip install -r requirements.txt
```

### 4. Verificar la Instalación

Puedes verificar que todo esté correctamente instalado ejecutando:

```bash
python --version  # Debe mostrar Python 3.13.3
pip list          # Muestra todas las librerías instaladas
```

## 📦 Dependencias Principales

El proyecto utiliza las siguientes librerías principales:

- **pandas** (2.3.1): Manipulación y análisis de datos
- **numpy** (2.3.1): Operaciones numéricas y arrays
- **selenium** (4.34.2): Automatización web y scraping
- **python-dateutil** (2.9.0.post0): Manejo avanzado de fechas

## Configuración del ChromeDriver

1. **Requisitos**
    - Google Chrome instalado
    - Conocer tu versión de Chrome:
      -- Abre Chrome y visita: `chrome://settings/help`
      -- Anota el número de versión (ejemplo: `139.0.7258.66`)

2. **Descarga el ChromeDriver** según tu versión:

    - **Para Chrome versión 114 o inferior**:
     1. Visita: [Chromedriver downloads page](https://chromedriver.chromium.org/downloads)
     2. Busca y descarga la versión exacta que coincida con tu Chrome
     
    - **Para Chrome versión 115 o superior**:
     1. Visita: [Chrome for Testing availability dashboard](https://developer.chrome.com/docs/chromedriver/downloads/version-selection)
     2. Si buscas las versiones más actuales, dirígete a el panel de disponibilidad de Chrome for Testing (CfT).
     3. Descarga la versión estable que coincida con tu número de versión principal (ejemplo: para Chrome 139.x descarga ChromeDriver 139.x)
     
3. **Coloca el archivo**:
   - Descarga el `chromedriver.exe` (Windows) o `chromedriver` (Linux/Mac)
   - Colócalo en la raíz del proyecto junto los archivos .py
   - Ahora esta todo listo para ejecutar el proyecto

## 🌊 Flujo de Trabajo con Git-Flow

Este proyecto utiliza **Git-Flow** como estrategia de branching. Es fundamental seguir estas reglas:

### Ramas Principales
- **`main`**: Rama de producción (solo código estable)
- **`develop`**: Rama de desarrollo (integración de features)

### Ramas de Trabajo
- **`feature/*`**: Para nuevas funcionalidades
- **`hotfix/*`**: Para correcciones urgentes en producción
- **`release/*`**: Para preparar nuevas versiones

### Proceso de Desarrollo

1. **Crear una nueva feature desde develop:**
```bash
git checkout develop
git pull origin develop
git checkout -b feature/nombre-de-tu-feature
```

2. **Desarrollar y hacer commits:**
```bash
git add .
git commit -m "feat: descripción de la funcionalidad"
```

3. **Subir la rama y crear Pull Request:**
```bash
git push origin feature/nombre-de-tu-feature
```

4. **Crear Pull Request:**
   - **Target Branch**: `develop` (siempre)
   - **Título**: Descripción clara de la funcionalidad
   - **Descripción**: Detalle de los cambios realizados
   - **Reviewers**: **OBLIGATORIO** - Solicitar revisión a TODOS los colaboradores

### 🔍 Proceso de Revisión

**IMPORTANTE**: Ningún Pull Request puede ser mergeado sin:
- ✅ Revisión y aprobación de AL MENOS 2 colaboradores
- ✅ Todas las conversaciones resueltas
- ✅ Pasar todas las validaciones (si las hay)
- ✅ Código actualizado con la rama develop

### Comandos Git-Flow Útiles

```bash
# Inicializar git-flow (solo la primera vez)
git flow init

# Crear nueva feature
git flow feature start nombre-feature

# Finalizar feature (crea PR automáticamente)
git flow feature finish nombre-feature

# Crear hotfix
git flow hotfix start version-patch

# Crear release
git flow release start version
```

## 🤝 Colaboración

### Convenciones de Commits
Utilizamos [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` Nueva funcionalidad
- `fix:` Corrección de bug
- `docs:` Cambios en documentación
- `style:` Cambios de formato (no afectan funcionalidad)
- `refactor:` Refactorización de código
- `test:` Agregar o modificar tests
- `chore:` Tareas de mantenimiento

### Ejemplo de Commit:
```bash
git commit -m "feat: agregar scraping de datos de Cinépolis"
```

## 📂 Estructura del Proyecto

```
cinema-data-generator/
├── README.md
├── requirements.txt
├── cinepolis.py                # Script principal 
├── cinemark.py
├── cinepolis_ca/               # Paquete con scrapers por país
│   ├── __init__.py
│   ├── base.py                  # Funciones comunes para los scrapers
│   ├── cinepolis_gt.py
│   ├── cinepolis_sv.py
│   ├── cinepolis_cr.py
│   ├── cinepolis_pa.py
│   ├── cinepolis_hn.py
│   └── (otros países).py
├── chromedriver                 # Driver de Chrome (o chromedriver.exe en Windows)
└── venv/                        # Entorno virtual (local)

```

## 🚨 Notas Importantes

1. **Nunca** hacer push directo a `main` o `develop`
2. **Siempre** trabajar en ramas feature
3. **Obligatorio** solicitar revisión de todos los colaboradores
4. **Mantener** el entorno virtual activado durante el desarrollo
5. **Actualizar** requirements.txt si instalas nuevas dependencias

## 📞 Soporte

Si tienes problemas con la configuración del entorno o el flujo de trabajo, contacta a cualquiera de los colaboradores del proyecto.

---

**¡Feliz coding! 🚀**
