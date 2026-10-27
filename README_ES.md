# SetterApp Volley

Herramienta de análisis de vídeo para entrenadores de voleibol: reproduce un vídeo de un colocador, sigue una pelota con un detector visual configurable, mantiene la trayectoria en pantalla y permite registrar tiempos por destino.

## Arranque

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Tkinter debe estar disponible en la instalación de Python.

## Uso

1. Abre un vídeo y pulsa reproducir. La traza se acumula mientras se detectan candidatos a pelota.
2. Selecciona el destino 1–6 y pulsa `Espacio` (o el botón) en el instante de cada colocación.
3. Usa `Borrar traza` para comenzar una nueva secuencia sin borrar los tiempos.
4. Ajusta el radio mínimo/máximo si la pelota es más pequeña o grande, y exporta los tiempos a CSV.

El detector de esta primera versión busca objetos claros y compactos. En vídeos con pelotas de otro color, hay que ampliar el detector HSV o sustituir `detect_ball()` por un modelo entrenado; la interfaz y el formato de tiempos no dependen de esa implementación.

## Incluye

- Reproducción, pausa y navegación por fotograma.
- Detección configurable por HSV, radio y circularidad.
- Trazas persistentes hasta borrado manual.
- Marcado de colocaciones por destino y cálculo de intervalos.
- Exportación CSV para análisis posterior.
