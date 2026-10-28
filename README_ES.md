# SetterApp Volley

SetterApp Volley es una herramienta de escritorio para entrenadores de voleibol. Permite revisar la distribución de un colocador, seguir una pelota multicolor durante la jugada, conservar las trayectorias terminadas y medir cada colocación.

## Funcionalidades

- Reproducción local de vídeo, pausa, navegación por fotogramas y línea de tiempo.
- Inicialización manual de la pelota haciendo clic sobre ella en el vídeo.
- Tracking CSRT mediante `opencv-contrib-python`, con coincidencia de plantilla y detección HSV/contornos como alternativas.
- Filtros que priorizan el patrón de color de la pelota y descartan regiones predominantemente negras y coincidencias poco plausibles del fondo.
- Cuatro destinos con colores fijos de trayectoria:
  - Punta — rojo
  - Pipe — naranja
  - Opuesto — verde
  - Central — amarillo
- La colocación comienza al seleccionar la pelota y termina al pulsar `Espacio`.
- Cada colocación terminada congela su trayectoria y muestra un círculo en el extremo.
- Las trayectorias registradas se pueden mostrar u ocultar de forma independiente desde la tabla. El doble clic sobre una fila alterna su visibilidad.
- **Clear trail** solo elimina la trayectoria activa no registrada. Las trayectorias guardadas solo se eliminan al borrar su registro.
- Exportación CSV con destino, inicio, fin y duración.
- Exportación de un vídeo anotado con las trayectorias visibles y círculos finales. El vídeo se genera sin audio.
- Exportación de una plantilla JSON con puntos, fotogramas, colores, visibilidad y tiempos para reutilizar el análisis.
- Logo del club e interfaz con tema rojo, negro y grises.

## Requisitos

- Python 3.10 o superior.
- Tkinter, incluido normalmente en el instalador oficial de Python.
- OpenCV contrib y Pillow.
- Un vídeo compatible con OpenCV, preferiblemente MP4 H.264.

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
2. Pausa en un fotograma donde la pelota sea claramente visible.
3. Pulsa **Select ball on video** y haz clic en el centro de la pelota. Esto inicia el tiempo e inicializa el tracker.
4. Selecciona **Punta**, **Pipe**, **Opuesto** o **Central**. Las teclas `1`–`4` sirven como atajos.
5. Pulsa `Espacio` cuando termine la colocación. La tabla registra su duración y la trayectoria pasa a ser un segmento coloreado terminado.
6. Selecciona una fila y utiliza **Show / hide selected trail**, o haz doble clic, para consultar colocaciones concretas.
7. Usa **Clear trail** solo para descartar el segmento activo no registrado. Usa **Delete selected record** para eliminar una colocación terminada y su trayectoria.
8. Pulsa **Export CSV** para guardar el análisis.
9. Pulsa **Export video** para crear un MP4 anotado con las trayectorias que estén visibles en la tabla. Pulsa **Export trail template** para guardar los datos geométricos en JSON.

## Notas sobre el tracking

La inicialización manual se recomienda para pelotas rojas, amarillas y blancas y para jugadas con muchos estímulos. CSRT sigue una región y no únicamente el punto más brillante, por lo que tolera mejor jugadores y elementos móviles del fondo. Si la pelota queda totalmente ocluida o CSRT se desvía, pausa y vuelve a inicializarla en un fotograma donde sea visible.

Los puntos de extensión del tracking son `create_visual_tracker()`, `track_selected_ball()` y `detect_ball()` en `app.py`. Más adelante se pueden sustituir por optical flow, un filtro de Kalman o un detector entrenado con el ángulo de cámara del club.

## Solución de problemas

- Si CSRT no está disponible, reinstala con `python -m pip install -r requirements.txt`; el proyecto necesita `opencv-contrib-python`.
- Si se pierde la pelota, pausa y vuelve a seleccionarla cuando sea claramente visible.
- Si el recuadro inicial es demasiado pequeño o grande, ajusta los controles de radio antes de seleccionar la pelota.
- Si el techo blanco produce un falso positivo, reinicializa el tracker; además del brillo se utilizan color y saturación.
- Si el vídeo no se puede decodificar, conviértelo a MP4 H.264.

## Archivos del proyecto

| Archivo | Función |
| --- | --- |
| `app.py` | Interfaz, reproducción, tracking, trayectorias, tiempos y exportación CSV |
| `requirements.txt` | Dependencias de Python |
| `LogoSanGregorioRojo.png` | Logo del club mostrado en el encabezado |
| `README.md` | Documentación en inglés |
