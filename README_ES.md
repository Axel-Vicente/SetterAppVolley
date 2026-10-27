# SetterApp Volley

Herramienta de escritorio para analizar vídeo de voleibol. Permite revisar la distribución de un colocador, hacer tracking de una pelota multicolor después de marcarla manualmente, conservar las trayectorias y registrar los tiempos de colocación.

## Funcionalidades

- Reproducción, pausa, navegación por fotogramas y exportación CSV.
- Inicialización manual: pulsa **Select ball on video** y después haz clic sobre la pelota roja, amarilla y blanca.
- Tracking local por plantilla con actualización gradual; no presupone que la pelota sea blanca.
- Cuando está disponible `opencv-contrib-python`, utiliza CSRT como tracker principal para tolerar mejor movimiento, cambios de escala y estímulos del fondo; la plantilla queda como fallback.
- Detector automático de respaldo basado en HSV, geometría de contornos, círculos de Hough y continuidad entre fotogramas.
- El tracking manual prioriza saturación y color de la pelota, y descarta regiones predominantemente negras para evitar cabezas y ropa oscura.
- Cada colocación marcada congela su trayectoria, dibuja un círculo en el extremo y asigna otro color a la trayectoria siguiente.
- Los destinos son **Punta** (rojo), **Pipe** (naranja), **Opuesto** (verde) y **Central** (amarillo).
- El encabezado muestra el logo del club desde `LogoSanGregorioRojo.png`.
- Borrado de registros seleccionados o de toda la tabla de tiempos.
- Interfaz oscura con los colores del club: rojo, negro y grises.

La trayectoria de cada registro se puede mostrar u ocultar seleccionando la fila y pulsando **Show / hide selected trail**; el doble clic sobre una fila hace lo mismo. La duración se mide desde la selección de la pelota hasta la pulsación de **Espacio**, que finaliza la colocación. El CSV incluye inicio, fin y duración.

## Instalación

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Se necesita Python 3.10 o superior, Tkinter, OpenCV y Pillow.

## Flujo de trabajo

1. Abre un vídeo y utiliza **Play** o la línea de tiempo.
2. Pulsa **Select ball on video** y haz clic en el centro de la pelota. El fotograma actual se usa para crear la plantilla de tracking.
3. Selecciona la posición 1–6 y pulsa **Espacio** en cada colocación.
4. Al marcar una colocación, su trayectoria queda congelada con un círculo final de color; la siguiente utiliza otro color.
5. Usa **Clear trail** para eliminar todas las trayectorias sin borrar los registros de tiempo.
6. Selecciona filas de la tabla y pulsa **Delete selected record**, o usa **Delete all records**.

## Notas sobre el tracking

Para pelotas rojas, amarillas y blancas se recomienda la inicialización manual. El tracker busca en una ventana local alrededor de la posición anterior mediante coincidencia de plantilla y la actualiza lentamente cuando cambian la iluminación o la escala. Si la pelota queda totalmente ocluida, pausa, busca un fotograma donde sea visible y vuelve a seleccionarla. El método `track_selected_ball()` es el punto de extensión para incorporar optical flow, CSRT/KCF o YOLO si se necesita soportar oclusiones más intensas.

## Solución de problemas

- Si se pierde la pelota, pausa y vuelve a seleccionarla en un fotograma donde sea visible.
- Si el techo blanco genera un falso positivo, vuelve a seleccionar la pelota: el tracker usa el patrón rojo/amarillo y no solo el brillo.
- Aumenta el radio máximo si la pelota ocupa más tamaño en el vídeo.
- Usa **Clear trail** antes de comenzar una secuencia de análisis nueva.
- Si un vídeo no se puede decodificar, conviértelo a MP4 H.264 y vuelve a intentarlo.

## Archivos del proyecto

| Archivo | Función |
| --- | --- |
| `app.py` | Interfaz, reproducción, tracking, trayectorias y registros de tiempo |
| `requirements.txt` | Dependencias de Python |
| `README.md` | Documentación en inglés |
