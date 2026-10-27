# SetterApp Volley

SetterApp Volley is a desktop video-analysis tool for volleyball coaches. It is designed to review a setter's distribution, keep a visual ball trajectory on top of the video, and record the timing of each set to a target zone.

## Features

- Video playback with play/pause and frame seeking.
- Persistent ball trail that remains visible until manually cleared.
- Multi-candidate ball detector combining HSV brightness, contour geometry, Hough circles, and frame-to-frame continuity.
- Manual placement markers with target selection for positions 1–6.
- Timestamp and interval calculation between consecutive placements.
- CSV export for later analysis in Excel, LibreOffice, or a data-analysis workflow.
- Deletion of selected placement records or the complete timing table.
- Modern dark interface using the club palette: red, black, and greys.
- Error dialogs for unreadable files, invalid videos, and frame-decoding failures.

## Requirements

- Python 3.10 or newer.
- Tkinter, normally included with the official Python installer.
- OpenCV and Pillow, installed from `requirements.txt`.

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

On macOS/Linux, activate the environment with `source .venv/bin/activate`.

## Workflow

1. Click **Open video** and select an MP4, MOV, AVI, MKV, or M4V file.
2. Use **Play** or the timeline to reach the desired sequence.
3. Select the target position and press **Space** at the instant of the placement. The number keys 1–6 select targets quickly.
4. Adjust the detector radius limits when the ball is too small or too large in the source video. The detector now combines bright-object segmentation with circle detection and rejects implausible jumps between frames.
5. Use **Clear trail** to start a new visual sequence without deleting registered timings.
6. Select rows in the timing table and use **Delete selected record**, or use **Delete all records** to reset the table.
7. Click **Export CSV** to save timestamps and intervals.

## Detection notes

The current detector is lightweight and runs locally. It generates candidates from bright low-saturation regions and Hough circles, then scores them using circularity, radius, and distance from the previous detection. This is more tolerant of motion blur and busy backgrounds than a single threshold, but it is not a trained sports-tracking model. For production-grade tracking, the `detect_ball()` method can be replaced with a calibrated HSV profile, CSRT/KCF tracking, or a model such as YOLO trained on frames from the team's camera setup.

The timing marker is manual by design: it provides a reliable coaching workflow while avoiding false automatic placement events. Automatic event classification can be added later without changing the placement table or CSV schema.

## Troubleshooting

- If a video cannot be opened, verify that it plays locally and try exporting it to H.264 MP4.
- If the application reports that no frames are readable, the file may contain an unsupported codec or a damaged index.
- If the trail follows another bright object, increase the minimum radius, lower the maximum radius, or change the detector implementation.
- If the application previously showed a recursive Python 3.13 traceback, update to this version: Tkinter now reports the original callback error directly, and timeline updates are guarded against callback recursion.

## Project structure

| File | Purpose |
| --- | --- |
| `app.py` | Tkinter interface, video playback, tracking, timing, and CSV export |
| `requirements.txt` | Python dependencies |
| `README_ES.md` | Spanish documentation |

## License

No license has been selected yet. Add one before distributing the application outside the project.
