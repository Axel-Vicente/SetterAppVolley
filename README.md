# SetterApp Volley

Desktop video-analysis tool for volleyball coaches. It reviews a setter's distribution, tracks a multicolour ball after manual initialization, keeps trajectories visible, and records placement timing.

## Features

- Video playback, pause, frame seeking, and CSV export.
- Manual ball initialization: click **Select ball on video**, then click the red/yellow/white ball.
- Local template tracking with gradual template refresh, so tracking does not assume a white ball.
- Automatic fallback detector using HSV, contour geometry, Hough circles, and frame continuity.
- Every marked placement freezes its trajectory, draws an endpoint circle, and starts the next trajectory in another color.
- Delete selected placement records or delete the complete timing table.
- Dark club-themed interface using red, black, and greys.

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Python 3.10+, Tkinter, OpenCV, and Pillow are required.

## Workflow

1. Open a video and use **Play** or the timeline.
2. Press **Select ball on video** and click the ball center. The current frame is used to create the tracking template.
3. Select target position 1–6 and press **Space** at each placement.
4. At every placement, the current trajectory is frozen with a colored endpoint circle; the following trajectory gets the next color.
5. Use **Clear trail** to remove all trajectories without deleting timing records.
6. Select table rows and use **Delete selected record**, or use **Delete all records**.

## Tracking notes

Manual initialization is recommended for red/yellow/white balls. The tracker searches a local window around the previous position using template matching and updates the template slowly for lighting and scale changes. If the ball becomes fully occluded, pause, seek to a visible frame, and select it again. The `track_selected_ball()` method is the extension point for optical flow, CSRT/KCF, or YOLO when stronger occlusion handling is needed.

## Troubleshooting

- If the ball is lost, pause and reselect it at a visible frame.
- Increase the maximum radius if the ball appears large in the source video.
- Use **Clear trail** before starting a new analysis sequence.
- If a video cannot be decoded, convert it to H.264 MP4 and try again.

## Project files

| File | Purpose |
| --- | --- |
| `app.py` | User interface, playback, tracking, trajectories, and timing records |
| `requirements.txt` | Python dependencies |
| `README_ES.md` | Spanish documentation |
