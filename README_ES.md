# SetterApp Volley

SetterApp Volley es una herramienta de escritorio para analizar vídeo de voleibol. Está pensada para revisar la distribución de un colocador, mantener visible la trayectoria de la pelota y registrar los tiempos de cada colocación hacia una zona objetivo.

## Funcionalidades

- Reproducción de vídeo, pausa y navegación por fotogramas.
- Traza persistente de la pelota hasta que se borra manualmente.
- Detector inicial configurable por brillo HSV, radio del objeto y circularidad del contorno.
- Marcado manual de colocaciones con selección de posiciones 1–6.
- Cálculo del instante y del intervalo respecto a la colocación anterior.
- Exportación CSV compatible con Excel, LibreOffice y herramientas de análisis de datos.
- Diálogos de error para archivos ilegibles, vídeos inválidos y fallos al decodificar fotogramas.

## Requisitos

- Python 3.10 o superior.
- Tkinter, incluido normalmente en el instalador oficial de Python.
- OpenCV y Pillow, instalables desde `requirements.txt`.

## Instalación

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

En macOS/Linux, activa el entorno con `source .venv/bin/activate`.

## Flujo de trabajo

1. Pulsa **Open video** y selecciona un archivo MP4, MOV, AVI, MKV o M4V.
2. Usa **Play** o la línea de tiempo para llegar a la secuencia deseada.
3. Selecciona la posición objetivo y pulsa **Espacio** en el instante de la colocación. Las teclas 1–6 permiten cambiar de destino rápidamente.
4. Ajusta los radios mínimo y máximo si la pelota aparece demasiado pequeña o grande.
5. Pulsa **Clear trail** para comenzar una nueva secuencia visual sin borrar los tiempos ya registrados.
6. Pulsa **Export CSV** para guardar los instantes y los intervalos.

## Notas sobre la detección

El detector actual es ligero y se ejecuta localmente. Busca regiones claras, compactas y aproximadamente circulares. Es una buena base cuando la pelota contrasta con el fondo, pero no sustituye a un modelo entrenado específicamente para seguimiento deportivo. Para una solución más robusta, se puede reemplazar `detect_ball()` por un perfil HSV calibrado, un tracker CSRT/KCF o un modelo como YOLO entrenado con imágenes de la cámara del equipo.

El marcado temporal es manual de forma intencionada: ofrece un flujo fiable para el entrenador y evita falsos eventos automáticos. Más adelante se puede añadir clasificación automática sin cambiar la tabla de colocaciones ni el formato CSV.

## Solución de problemas

- Si no se puede abrir un vídeo, comprueba que se reproduce localmente y prueba a convertirlo a MP4 H.264.
- Si aparece que no hay fotogramas legibles, el códec puede no ser compatible o el índice del archivo estar dañado.
- Si la traza sigue otro objeto brillante, aumenta el radio mínimo, reduce el máximo o cambia la implementación del detector.
- Si anteriormente aparecía un traceback recursivo en Python 3.13, actualiza a esta versión: Tkinter muestra ahora el error original del callback y la actualización de la línea de tiempo está protegida contra recursión.

## Estructura del proyecto

| Archivo | Función |
| --- | --- |
| `app.py` | Interfaz Tkinter, reproducción, seguimiento, tiempos y exportación CSV |
| `requirements.txt` | Dependencias de Python |
| `README.md` | Documentación en inglés |

## Licencia

Todavía no se ha seleccionado una licencia. Añade una antes de distribuir la aplicación fuera del proyecto.
