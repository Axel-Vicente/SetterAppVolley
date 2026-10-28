# SetterApp Volley

SetterApp Volley is a desktop video-analysis tool for volleyball coaches. It is designed to review a setter's distribution, follow a multicolour ball during a rally, preserve completed trajectories, and measure each placement.

## Features

- Local video playback with pause, frame seeking, and timeline navigation.
- Manual ball initialization by drawing a circle over the ball; the circle defines the tracking diameter.
- CSRT tracking through `opencv-contrib-python`, with template matching and HSV/contour detection as fallbacks.
- Filters that prioritize the ball's colour pattern and reject predominantly black regions and implausible background matches.
- Four placement targets with fixed trail colours:
  - Punta — red
  - Pipe — orange
  - Opuesto — green
  - Central — yellow
- A placement starts when the ball is selected and ends when `Space` is pressed.
- Each completed placement freezes its trail and shows a circle at its endpoint.
- Registered trails can be shown or hidden independently from the timing table. Double-clicking a row toggles visibility.
- `Clear trail` removes only the active, unregistered trail. Registered trails are removed only when their placement record is deleted.
- CSV export with target, start time, end time, and duration.
- Export of an annotated video with visible trails and endpoint circles. The generated video does not include audio.
- Export of a JSON trail template containing points, frame indices, colours, visibility, and timings for reuse.
- Club logo and red/black/grey visual theme.

## Requirements

- Python 3.10 or newer.
- Tkinter, normally included with the official Python installer.
- OpenCV contrib and Pillow.
- A video file readable by OpenCV, preferably H.264 MP4.

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
2. Pause on a frame where the ball is clearly visible.
3. Press **Draw ball circle**, click the ball centre, and drag to its edge. The circle defines the diameter, starts the timing, and initializes the tracker.
4. Select **Punta**, **Pipe**, **Opuesto**, or **Central**. The number keys `1`–`4` are shortcuts.
5. Press `Space` when the placement ends. The table records its duration and the trajectory becomes a completed coloured segment.
6. Select a table row and use **Show / hide selected trail**, or double-click the row, to focus on specific placements.
7. Use **Clear trail** only to discard the current unregistered segment. Use **Delete selected record** to remove a completed placement and its trajectory.
8. Click **Export CSV** to save the analysis.
9. Click **Export video** to create an annotated MP4 using the trails currently visible in the table. Click **Export trail template** to save the geometry as JSON.

## Tracking notes

Manual initialization is recommended for red/yellow/white balls and busy scenes. The circle should cover the full ball without including too much background; CSRT tracks that region rather than only the brightest point. If the ball becomes fully occluded or CSRT drifts, pause and draw the circle again on a visible frame.

The tracking extension points are `create_visual_tracker()`, `track_selected_ball()`, and `detect_ball()` in `app.py`. They can later be replaced by optical flow, a Kalman filter, or a detector trained on the club's camera angle.

## Troubleshooting

- If CSRT is unavailable, reinstall with `python -m pip install -r requirements.txt`; the project requires `opencv-contrib-python`.
- If the ball is lost, pause and select it again while clearly visible.
- If the manually drawn circle is too small or large, repeat **Draw ball circle** and drag precisely from the ball centre to its edge.
- If a white ceiling causes a false match, reinitialize the tracker; colour and saturation are used in addition to brightness.
- If the video cannot be decoded, convert it to H.264 MP4.

## Project files

| File | Purpose |
| --- | --- |
| `app.py` | Interface, playback, tracking, trajectories, timing, and CSV export |
| `requirements.txt` | Python dependencies |
| `LogoSanGregorioRojo.png` | Club logo shown in the header |
| `README_ES.md` | Spanish documentation |
