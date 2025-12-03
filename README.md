# Epidemics Pygame

**Epidemics** es una implementación en Python del popular juego de mesa de estrategia cooperativa "Pandemic". El proyecto incluye una versión completa con interfaz gráfica (GUI) basada en **Pygame** y varias versiones de consola que documentan la evolución de la lógica del juego.

En este juego, tú y tus compañeros forman un equipo de especialistas en control de enfermedades. Vuestra misión es contener cuatro plagas mortales mientras descubren sus curas.

## 📋 Características

*   **Interfaz Gráfica Completa (v0.6):**
    *   Mapa mundial interactivo con conexiones entre ciudades.
    *   Sistema visual de movimiento, tratamiento de enfermedades y construcción de estaciones.
    *   Gestión de cartas de jugador (incluyendo Eventos y Epidemias).
    *   Menús modales para selección de ciudades, descarte de cartas e intercambio de conocimientos.
    *   Registro (Log) de acciones en tiempo real.
*   **Mecánicas de Juego Implementadas:**
    *   Movimiento (Coche, Vuelo Directo, Vuelo Chárter, Puente Aéreo).
    *   Tratar enfermedades y descubrir curas.
    *   Brotes y reacciones en cadena.
    *   Erradicación de enfermedades.
    *   Cartas de Evento Especiales (Puente Aéreo, Subsidio Gubernamental, etc.).
*   **Versiones de Shell:** Historial de desarrollo con versiones de solo texto (v0.1 a v0.4) para probar la lógica pura.

## 🛠️ Requisitos

*   **Python 3.11** o superior.
*   **Pygame** (versión 2.6.1 o superior).

## 🚀 Instalación

1.  **Clona el repositorio:**
    ```bash
    git clone <url-de-tu-repo>
    cd epidemics-pygame
    ```

2.  **Crea un entorno virtual (Opcional pero recomendado):**
    ```bash
    python -m venv venv
    # En Windows:
    venv\Scripts\activate
    # En macOS/Linux:
    source venv/bin/activate
    ```

3.  **Instala las dependencias:**
    Puedes instalarlo manualmente o usando el archivo de configuración si tienes herramientas compatibles.
    ```bash
    pip install pygame
    ```

## 🎮 Cómo Jugar

### 💻Versión Gráfica

El archivo principal de la aplicación gráfica se encuentra en la carpeta `app`. Asegúrate de ejecutarlo desde la raíz del proyecto para que cargue correctamente las imágenes.

```bash
python main.py
```
## 📲Controles:

-Clic Izquierdo: Interactuar con ciudades, botones y cartas.

-Rueda del Ratón: Desplazarse por el registro de texto (log) o listas de ciudades.

-ESC: Salir al menú principal (si el juego ha terminado).
Versiones de Consola

Si prefieres probar la lógica del juego sin gráficos, puedes ejecutar los scripts en shell_version. La versión v0.4 es la más completa en cuanto a reglas.

```bash
python shell_version/pandemic_v0_4.py
```

## 📂 Estructura del Proyecto

app/: Contiene el código fuente de la versión gráfica (pain.py).

images/: Recursos gráficos (mapa, fichas, marcadores, etc.).

shell_version/: Versiones iterativas de la lógica del juego en modo texto.

pandemic_v0_X.py: Clases y lógica.

run_v0_X.py: Ejecutables para la consola.

LICENSE: Licencia MIT.

pyproject.toml: Configuración del proyecto y dependencias.

## 📖 Reglas Básicas

➤Turno del Jugador: Tienes 4 acciones por turno (Mover, Curar, Construir, Compartir, Descubrir Cura, etc.).
Robar Cartas: Al finalizar las acciones, robas 2 cartas de jugador. ¡Cuidado con las cartas de EPIDEMIA!

➤Descarte: Si tienes más de 7 cartas, deberás descartar el exceso.

➤Infección: Al final del turno, nuevas ciudades se infectan.

➤Victoria: Descubrir la cura para las 4 enfermedades (Azul, Amarillo, Negro, Rojo).

➤Derrota:
Se producen 8 brotes.
Se acaban los cubos de enfermedad (no implementado estrictamente por cubos, pero sí por lógica de desborde).
Se acaba el mazo de cartas de jugador.


## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo LICENSE para más detalles.

## Autores: 
    
    Alan
    Lucas
    Kevin
    Nicolas Orjuela Sanchez @norjuelas



