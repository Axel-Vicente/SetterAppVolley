"""SetterApp Volley: video review, ball trail and setter timing notebook."""

from __future__ import annotations

import csv
import math
import os
import traceback
import tkinter as tk
from dataclasses import dataclass
from tkinter import filedialog, messagebox, ttk

import cv2
from PIL import Image, ImageTk


@dataclass
class Placement:
    number: int
    position: str
    start_timestamp: float
    end_timestamp: float
    duration: float


@dataclass
class TrailSegment:
    points: list[tuple[int, int]]
    color: tuple[int, int, int]
    visible: bool = True


class SetterApp:
    TARGETS = {
        1: ("Punta", (36, 36, 220)),
        2: ("Pipe", (0, 145, 255)),
        3: ("Opuesto", (65, 185, 75)),
        4: ("Central", (0, 220, 255)),
    }

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("SetterApp Volley")
        self.root.geometry("1280x820")
        self.root.minsize(980, 650)
        self.cap: cv2.VideoCapture | None = None
        self.video_path = ""
        self.fps, self.frame_count, self.frame_index = 25.0, 0, 0
        self.playing = False
        self.after_id: str | None = None
        self.updating_seek = False
        self.last_ball: tuple[int, int] | None = None
        self.awaiting_ball_click = False
        self.tracker_template = None
        self.cv_tracker = None
        self.tracker_template_gray = None
        self.tracker_template_hsv = None
        self.tracker_color_hist = None
        self.tracker_patch_radius = 18
        self.tracker_lost_frames = 0
        self.completed_trails: list[TrailSegment] = []
        self.display_origin = (0, 0)
        self.display_scale = 1.0
        self.display_size = (0, 0)
        self.tracking = tk.BooleanVar(value=True)
        self.show_overlay = tk.BooleanVar(value=True)
        self.selected_position = tk.IntVar(value=1)
        self.min_radius, self.max_radius = tk.IntVar(value=3), tk.IntVar(value=60)
        self.saturation, self.value = tk.IntVar(value=45), tk.IntVar(value=80)
        self.trail: list[tuple[int, int]] = []
        self.placements: list[Placement] = []
        self.placement_start_timestamp: float | None = None
        self.photo: ImageTk.PhotoImage | None = None
        self._build_ui()
        self.root.report_callback_exception = self.report_callback_exception
        self.canvas.bind("<Button-1>", self.select_ball_from_canvas)
        self.root.bind("<space>", lambda _event: self.record_placement())
        for number in range(1, 5):
            self.root.bind(str(number), lambda _event, n=number: self.selected_position.set(n))
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _build_ui(self) -> None:
        self.root.configure(bg="#0b0b0d")
        style = ttk.Style(self.root); style.theme_use("clam")
        style.configure("TFrame", background="#0b0b0d"); style.configure("Panel.TFrame", background="#151518")
        style.configure("TLabel", background="#0b0b0d", foreground="#eeeeef"); style.configure("Panel.TLabel", background="#151518", foreground="#eeeeef")
        style.configure("Header.TLabel", font=("Segoe UI", 19, "bold"), foreground="#e3262e"); style.configure("TButton", padding=8, background="#29292d", foreground="#f4f4f5")
        style.map("TButton", background=[("active", "#3a3a40")]); style.configure("Primary.TButton", background="#d71920", foreground="#ffffff", font=("Segoe UI", 10, "bold")); style.map("Primary.TButton", background=[("active", "#ef343b")])
        style.configure("Danger.TButton", background="#702126", foreground="#ffffff"); style.map("Danger.TButton", background=[("active", "#a52c34")])
        style.configure("Treeview", rowheight=28, background="#202024", fieldbackground="#202024", foreground="#f4f7fb")
        style.configure("Treeview.Heading", background="#303035", foreground="#ffffff")
        header = ttk.Frame(self.root, padding=(18, 12, 18, 8)); header.pack(fill="x")
        self.logo_photo = None
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "LogoSanGregorioRojo.png")
        if os.path.exists(logo_path):
            logo = Image.open(logo_path).convert("RGBA"); logo.thumbnail((58, 58), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo)
            ttk.Label(header, image=self.logo_photo).pack(side="left", padx=(0, 10))
        ttk.Label(header, text="SetterApp Volley", style="Header.TLabel").pack(side="left")
        ttk.Label(header, text=" - video analysis", font=("Segoe UI", 10)).pack(side="left", pady=5)
        ttk.Button(header, text="Open video", style="Primary.TButton", command=self.open_video).pack(side="right")
        main = ttk.Frame(self.root, padding=(18, 0, 18, 18)); main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=3); main.columnconfigure(1, weight=1); main.rowconfigure(0, weight=1)
        viewer = ttk.Frame(main); viewer.grid(row=0, column=0, sticky="nsew", padx=(0, 14)); viewer.rowconfigure(0, weight=1); viewer.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(viewer, bg="#080b10", highlightthickness=0); self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.create_text(30, 30, anchor="nw", fill="#8493a7", text="Open a video to start", tags="empty")
        controls = ttk.Frame(viewer, padding=(0, 12, 0, 0)); controls.grid(row=1, column=0, sticky="ew"); controls.columnconfigure(1, weight=1)
        self.play_button = ttk.Button(controls, text="Play", command=self.toggle_play, state="disabled"); self.play_button.grid(row=0, column=0, padx=(0, 8))
        self.seek = ttk.Scale(controls, from_=0, to=1, command=self.seek_video); self.seek.grid(row=0, column=1, sticky="ew")
        self.time_label = ttk.Label(controls, text="00:00.000 / 00:00.000", width=22); self.time_label.grid(row=0, column=2, padx=(8, 0))
        sidebar = ttk.Frame(main, style="Panel.TFrame", padding=16); sidebar.grid(row=0, column=1, sticky="nsew"); sidebar.columnconfigure(0, weight=1)
        ttk.Label(sidebar, text="Placement target", style="Panel.TLabel", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 6))
        pos_frame = ttk.Frame(sidebar); pos_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        for i, (name, rgb) in self.TARGETS.items():
            cell = ttk.Frame(pos_frame, style="Panel.TFrame"); cell.grid(row=(i - 1) // 2, column=(i - 1) % 2, sticky="w", padx=(0, 12), pady=3)
            swatch_rgb = (rgb[2], rgb[1], rgb[0])
            tk.Label(cell, bg="#%02x%02x%02x" % swatch_rgb, width=2, height=1).pack(side="left", padx=(0, 5))
            ttk.Radiobutton(cell, text=f"{i} - {name}", value=i, variable=self.selected_position).pack(side="left")
        self.record_button = ttk.Button(sidebar, text="Mark placement (Space)", style="Primary.TButton", command=self.record_placement, state="disabled"); self.record_button.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        ttk.Label(sidebar, text="Tracking", style="Panel.TLabel", font=("Segoe UI", 12, "bold")).grid(row=3, column=0, sticky="w", pady=(0, 6))
        ttk.Checkbutton(sidebar, text="Detect ball", variable=self.tracking).grid(row=4, column=0, sticky="w"); ttk.Checkbutton(sidebar, text="Show trail", variable=self.show_overlay).grid(row=5, column=0, sticky="w", pady=(0, 7))
        ttk.Button(sidebar, text="Select ball on video", command=self.start_ball_selection).grid(row=6, column=0, sticky="ew", pady=(2, 7))
        ttk.Label(sidebar, text="Minimum / maximum radius", style="Panel.TLabel").grid(row=7, column=0, sticky="w")
        radius = ttk.Frame(sidebar); radius.grid(row=7, column=0, sticky="ew")
        ttk.Spinbox(radius, from_=2, to=100, textvariable=self.min_radius, width=6).pack(side="left"); ttk.Label(radius, text=" - ").pack(side="left"); ttk.Spinbox(radius, from_=5, to=150, textvariable=self.max_radius, width=6).pack(side="left")
        radius.grid(row=8)
        ttk.Button(sidebar, text="Clear trail", command=self.clear_trail).grid(row=9, column=0, sticky="ew", pady=(10, 4)); ttk.Button(sidebar, text="Export CSV", command=self.export_csv).grid(row=10, column=0, sticky="ew", pady=(0, 6))
        ttk.Button(sidebar, text="Delete selected record", style="Danger.TButton", command=self.delete_selected_placement).grid(row=11, column=0, sticky="ew", pady=(0, 4))
        ttk.Button(sidebar, text="Delete all records", style="Danger.TButton", command=self.delete_all_placements).grid(row=12, column=0, sticky="ew", pady=(0, 14))
        ttk.Label(sidebar, text="Registered timings", style="Panel.TLabel", font=("Segoe UI", 12, "bold")).grid(row=13, column=0, sticky="w", pady=(0, 6))
        self.table = ttk.Treeview(sidebar, columns=("n", "position", "duration", "visible"), show="headings", height=12); self.table.grid(row=14, column=0, sticky="nsew"); sidebar.rowconfigure(14, weight=1)
        for column, title, width in (("n", "#", 35), ("position", "Target", 90), ("duration", "Duration", 85), ("visible", "Trail", 65)): self.table.heading(column, text=title); self.table.column(column, width=width, anchor="center")
        self.table.bind("<Double-1>", lambda _event: self.toggle_selected_trails())
        ttk.Button(sidebar, text="Show / hide selected trail", command=self.toggle_selected_trails).grid(row=15, column=0, sticky="ew", pady=(8, 4))
        self.status = ttk.Label(sidebar, text="Ready. Open a video.", style="Panel.TLabel", foreground="#a1a1aa", wraplength=300); self.status.grid(row=16, column=0, sticky="sw", pady=(10, 0))

    def open_video(self) -> None:
        path = filedialog.askopenfilename(title="Select video", filetypes=[("Videos", "*.mp4 *.mov *.avi *.mkv *.m4v"), ("All files", "*.*")])
        if not path: return
        candidate = cv2.VideoCapture(path)
        if not candidate.isOpened(): candidate.release(); self.show_error("Open video", "OpenCV could not open this file. Check the file and its codec."); return
        try:
            fps = candidate.get(cv2.CAP_PROP_FPS); frame_count = int(candidate.get(cv2.CAP_PROP_FRAME_COUNT))
            if not math.isfinite(fps) or fps <= 0: fps = 25.0
            if frame_count <= 0: raise ValueError("The video contains no readable frames.")
            if self.cap: self.cap.release()
            self.cap, self.video_path = candidate, path; self.fps, self.frame_count, self.frame_index = fps, frame_count, 0
            self.trail.clear(); self.completed_trails.clear(); self.last_ball = None; self.tracker_template = None; self.cv_tracker = None; self.tracker_template_gray = None; self.tracker_template_hsv = None; self.tracker_color_hist = None; self.placements.clear(); self.placement_start_timestamp = None
            for item in self.table.get_children(): self.table.delete(item)
            self.seek.configure(to=max(1, frame_count - 1)); self.play_button.configure(state="normal"); self.record_button.configure(state="normal")
            self.status.configure(text=f"{os.path.basename(path)} - {fps:.2f} fps"); self.show_frame()
        except Exception as exc:
            candidate.release(); self.show_error("Load video", str(exc))

    def toggle_play(self) -> None:
        if not self.cap: return
        self.playing = not self.playing; self.play_button.configure(text="Pause" if self.playing else "Play")
        if self.playing: self.advance()

    def advance(self) -> None:
        if not self.playing or not self.cap: return
        self.frame_index += 1
        if self.frame_index >= self.frame_count: self.frame_index = self.frame_count - 1; self.playing = False; self.play_button.configure(text="Play"); return
        self.show_frame(); self.after_id = self.root.after(max(1, round(1000 / self.fps)), self.advance)

    def seek_video(self, value: str) -> None:
        if self.cap and not self.playing and not self.updating_seek:
            self.frame_index = int(float(value)); self.last_ball = None; self.tracker_template = None; self.cv_tracker = None; self.tracker_template_gray = None; self.tracker_template_hsv = None; self.tracker_color_hist = None; self.show_frame()

    def show_frame(self) -> None:
        if not self.cap: return
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_index); ok, frame = self.cap.read()
        if not ok: raise RuntimeError(f"Could not decode frame {self.frame_index}.")
        self.raw_frame = frame.copy()
        if self.tracking.get():
            point = self.track_selected_ball(frame) if self.tracker_template is not None else self.detect_ball(frame)
            if point: self.trail.append(point)
        if self.show_overlay.get(): self.draw_overlay(frame)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB); image = Image.fromarray(rgb); image.thumbnail((self.canvas.winfo_width() or 900, self.canvas.winfo_height() or 600), Image.Resampling.LANCZOS)
        source_height, source_width = self.raw_frame.shape[:2]
        self.display_size = image.size; self.display_scale = min(image.width / source_width, image.height / source_height)
        self.display_origin = ((self.canvas.winfo_width() - image.width) // 2, (self.canvas.winfo_height() - image.height) // 2)
        self.photo = ImageTk.PhotoImage(image); self.canvas.delete("all"); self.canvas.create_image(self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2, image=self.photo, anchor="center")
        self.updating_seek = True
        try: self.seek.set(self.frame_index)
        finally: self.updating_seek = False
        now = self.frame_index / self.fps; self.time_label.configure(text=f"{self.format_time(now)} / {self.format_time(self.frame_count / self.fps)}")

    def start_ball_selection(self) -> None:
        if not self.cap:
            self.status.configure(text="Open a video before selecting the ball")
            return
        self.awaiting_ball_click = True
        self.status.configure(text="Click directly on the ball in the video")

    def select_ball_from_canvas(self, event) -> None:
        if not self.awaiting_ball_click or not self.cap or not hasattr(self, "raw_frame"):
            return
        origin_x, origin_y = self.display_origin
        x = int((event.x - origin_x) / self.display_scale); y = int((event.y - origin_y) / self.display_scale)
        height, width = self.raw_frame.shape[:2]
        if not (0 <= x < width and 0 <= y < height): return
        # A large patch includes court lines and players. Keep the reference
        # tight around the click; it is deliberately never replaced by a
        # later frame, preventing background contamination.
        radius = max(12, min(30, self.max_radius.get() * 2))
        self.tracker_patch_radius = radius
        x1, y1, x2, y2 = max(0, x - radius), max(0, y - radius), min(width, x + radius + 1), min(height, y + radius + 1)
        template = self.raw_frame[y1:y2, x1:x2]
        if template.shape[0] < 8 or template.shape[1] < 8: return
        self.tracker_template = template.copy(); self.tracker_template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        self.tracker_template_hsv = cv2.cvtColor(template, cv2.COLOR_BGR2HSV)
        self.tracker_color_hist = self.build_color_histogram(self.tracker_template_hsv)
        self.tracker_lost_frames = 0
        self.last_ball = (x, y); self.trail.append((x, y)); self.placement_start_timestamp = self.frame_index / self.fps; self.awaiting_ball_click = False
        self.cv_tracker = self.create_visual_tracker()
        if self.cv_tracker is not None:
            bbox = (x1, y1, x2 - x1, y2 - y1)
            try: self.cv_tracker.init(self.raw_frame, bbox)
            except cv2.error: self.cv_tracker = None
        tracker_name = "CSRT" if self.cv_tracker is not None else "template"
        self.status.configure(text=f"Ball selected at ({x}, {y}); {tracker_name} tracking enabled")

    def track_selected_ball(self, frame):
        if self.last_ball is None or self.tracker_template is None: return None
        if self.cv_tracker is not None:
            ok, box = self.cv_tracker.update(frame)
            if not ok: return None
            bx, by, bw, bh = [int(value) for value in box]
            if bw < 6 or bh < 6 or bx < 0 or by < 0 or bx + bw > frame.shape[1] or by + bh > frame.shape[0]: return None
            candidate = cv2.cvtColor(frame[by:by + bh, bx:bx + bw], cv2.COLOR_BGR2HSV)
            black_fraction = float((candidate[:, :, 2] < 38).mean())
            color_score = cv2.compareHist(self.tracker_color_hist, self.build_color_histogram(candidate), cv2.HISTCMP_CORREL)
            if black_fraction > 0.42 or color_score < -0.05: return None
            self.last_ball = (bx + bw // 2, by + bh // 2)
            return self.last_ball
        height, width = frame.shape[:2]; template_height, template_width = self.tracker_template.shape[:2]
        search_radius = max(45, int(max(template_width, template_height) * 3.0))
        x1 = max(0, self.last_ball[0] - search_radius); y1 = max(0, self.last_ball[1] - search_radius)
        x2 = min(width, self.last_ball[0] + search_radius); y2 = min(height, self.last_ball[1] + search_radius)
        search = frame[y1:y2, x1:x2]
        if search.shape[0] < template_height or search.shape[1] < template_width: return self.last_ball
        # Match colour, saturation, and luminance. The saturation channel is
        # important here: a white ceiling can match brightness, but not the
        # red/yellow colour pattern of the ball.
        search_gray = cv2.cvtColor(search, cv2.COLOR_BGR2GRAY)
        search_hsv = cv2.cvtColor(search, cv2.COLOR_BGR2HSV)
        result_color = cv2.matchTemplate(search, self.tracker_template, cv2.TM_CCOEFF_NORMED)
        result_gray = cv2.matchTemplate(search_gray, self.tracker_template_gray, cv2.TM_CCOEFF_NORMED)
        result_saturation = cv2.matchTemplate(search_hsv[:, :, 1], self.tracker_template_hsv[:, :, 1], cv2.TM_CCOEFF_NORMED)
        result = (result_color * 0.35) + (result_gray * 0.20) + (result_saturation * 0.45)
        _, confidence, _, location = cv2.minMaxLoc(result)
        if confidence < 0.48:
            self.tracker_lost_frames += 1
            return None
        self.tracker_lost_frames = 0
        x = x1 + location[0] + template_width // 2; y = y1 + location[1] + template_height // 2
        candidate = search_hsv[location[1]:location[1] + template_height, location[0]:location[0] + template_width]
        color_score = cv2.compareHist(self.tracker_color_hist, self.build_color_histogram(candidate), cv2.HISTCMP_CORREL)
        black_fraction = float((candidate[:, :, 2] < 38).mean())
        # The selected ball is not black. Reject heads, dark clothing, and
        # other dark regions even when their texture matches the template.
        if color_score < 0.08 or black_fraction > 0.28:
            self.tracker_lost_frames += 1
            return None
        self.last_ball = (x, y)
        return self.last_ball

    @staticmethod
    def create_visual_tracker():
        factory = getattr(cv2, "TrackerCSRT_create", None)
        if factory is None and hasattr(cv2, "legacy"): factory = getattr(cv2.legacy, "TrackerCSRT_create", None)
        return factory() if factory is not None else None

    @staticmethod
    def build_color_histogram(hsv_frame):
        non_black = cv2.inRange(hsv_frame, (0, 20, 38), (180, 255, 255))
        histogram = cv2.calcHist([hsv_frame], [0, 1], non_black, [18, 8], [0, 180, 0, 256])
        return cv2.normalize(histogram, histogram).astype("float32")

    def detect_ball(self, frame):
        """Return the most plausible ball candidate using appearance and continuity."""
        height, width = frame.shape[:2]
        min_radius, max_radius = self.min_radius.get(), self.max_radius.get()
        candidates: list[tuple[int, int, float]] = []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # Volleyballs are usually bright, but the low-saturation condition
        # avoids selecting most coloured jerseys and court markings.
        mask = cv2.inRange(hsv, (0, self.saturation.get(), self.value.get()), (180, 255, 255))
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area, perimeter = cv2.contourArea(contour), cv2.arcLength(contour, True)
            if perimeter == 0: continue
            radius = math.sqrt(max(area, 1) / math.pi)
            circularity = 4 * math.pi * area / (perimeter * perimeter)
            if min_radius <= radius <= max_radius and circularity >= 0.20:
                (x, y), _ = cv2.minEnclosingCircle(contour)
                candidates.append((int(x), int(y), circularity * radius))
        # Hough catches motion-blurred or partially segmented balls.
        blurred = cv2.GaussianBlur(gray, (9, 9), 1.5)
        circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1.2, minDist=max(12, min_radius * 2), param1=100, param2=18, minRadius=min_radius, maxRadius=max_radius)
        if circles is not None:
            for x, y, radius in circles[0]: candidates.append((int(x), int(y), float(radius) * 0.8))
        if not candidates: return None
        max_jump = max(width, height) * 0.28
        def score(candidate):
            x, y, appearance = candidate
            if self.last_ball is None: return appearance
            distance = math.hypot(x - self.last_ball[0], y - self.last_ball[1])
            continuity = max(0.0, 1.0 - distance / max_jump)
            return appearance * (0.35 + 1.65 * continuity) if distance <= max_jump else appearance * 0.05
        best = max(candidates, key=score)
        if self.last_ball is not None and math.hypot(best[0] - self.last_ball[0], best[1] - self.last_ball[1]) > max_jump:
            return None
        self.last_ball = (best[0], best[1])
        return self.last_ball

    def draw_overlay(self, frame) -> None:
        for segment in self.completed_trails:
            if not segment.visible: continue
            for first, second in zip(segment.points, segment.points[1:]): cv2.line(frame, first, second, segment.color, 2, cv2.LINE_AA)
            if segment.points:
                cv2.circle(frame, segment.points[-1], 11, (12, 12, 12), -1, cv2.LINE_AA); cv2.circle(frame, segment.points[-1], 8, segment.color, -1, cv2.LINE_AA)
        current_color = self.TARGETS[self.selected_position.get()][1]
        for first, second in zip(self.trail, self.trail[1:]): cv2.line(frame, first, second, current_color, 2, cv2.LINE_AA)
        if self.trail: cv2.circle(frame, self.trail[-1], 8, current_color, 2, cv2.LINE_AA)

    def record_placement(self) -> None:
        if not self.cap: return
        timestamp = self.frame_index / self.fps
        start = self.placement_start_timestamp if self.placement_start_timestamp is not None else timestamp
        duration = max(0.0, timestamp - start)
        target_name, target_color = self.TARGETS[self.selected_position.get()]
        placement = Placement(len(self.placements) + 1, target_name, start, timestamp, duration); self.placements.append(placement)
        self.completed_trails.append(TrailSegment(list(self.trail), target_color))
        self.trail.clear()
        self.placement_start_timestamp = timestamp
        self.table.insert("", "end", values=(placement.number, placement.position, f"{duration:.3f} s", "Shown")); self.status.configure(text=f"Marked {placement.position}: {duration:.3f} s")

    def clear_trail(self) -> None:
        # Only discard the in-progress trajectory. Completed trajectories are
        # owned by their placement record and can only be removed by deleting
        # that record; visibility is handled independently by the table.
        self.trail.clear(); self.last_ball = None; self.status.configure(text="Active trail cleared; registered trails kept"); self.show_frame()

    def delete_selected_placement(self) -> None:
        selected = self.table.selection()
        if not selected:
            messagebox.showinfo("Delete record", "Select one or more records in the table first.")
            return
        indexes = sorted((int(self.table.item(item, "values")[0]) - 1 for item in selected), reverse=True)
        for index in indexes:
            if 0 <= index < len(self.placements): del self.placements[index]
            if 0 <= index < len(self.completed_trails): del self.completed_trails[index]
        self.refresh_placements_table()
        self.status.configure(text=f"Deleted {len(indexes)} record(s)")

    def delete_all_placements(self) -> None:
        if not self.placements: return
        if not messagebox.askyesno("Delete records", "Delete all registered placements?"): return
        self.placements.clear(); self.completed_trails.clear(); self.trail.clear(); self.placement_start_timestamp = None; self.refresh_placements_table(); self.status.configure(text="All placement records deleted")

    def refresh_placements_table(self) -> None:
        for item in self.table.get_children(): self.table.delete(item)
        for number, item in enumerate(self.placements, start=1):
            item.number = number
            visible = self.completed_trails[number - 1].visible if number - 1 < len(self.completed_trails) else True
            self.table.insert("", "end", values=(number, item.position, f"{item.duration:.3f} s", "Shown" if visible else "Hidden"))

    def toggle_selected_trails(self) -> None:
        selected = self.table.selection()
        if not selected:
            messagebox.showinfo("Trail visibility", "Select one or more timing rows first.")
            return
        for item in selected:
            index = int(self.table.item(item, "values")[0]) - 1
            if 0 <= index < len(self.completed_trails): self.completed_trails[index].visible = not self.completed_trails[index].visible
        self.refresh_placements_table(); self.show_frame()

    def export_csv(self) -> None:
        if not self.placements: messagebox.showinfo("Export", "No placements have been registered yet."); return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], initialfile="placement_timings.csv")
        if not path: return
        with open(path, "w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle); writer.writerow(["number", "target", "start_s", "end_s", "duration_s"])
            for item in self.placements: writer.writerow([item.number, item.position, f"{item.start_timestamp:.3f}", f"{item.end_timestamp:.3f}", f"{item.duration:.3f}"])
        self.status.configure(text=f"CSV saved: {os.path.basename(path)}")

    @staticmethod
    def format_time(seconds: float) -> str:
        minutes, remainder = divmod(max(0, seconds), 60); return f"{int(minutes):02d}:{remainder:06.3f}"

    def show_error(self, title: str, detail: str) -> None:
        self.status.configure(text=detail.replace("\n", " ")); messagebox.showerror(title, detail)

    def report_callback_exception(self, exc, value, tb) -> None:
        detail = "".join(traceback.format_exception_only(exc, value)).strip(); self.show_error("Application error", detail)

    def close(self) -> None:
        if self.after_id: self.root.after_cancel(self.after_id)
        if self.cap: self.cap.release()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk(); SetterApp(root); root.mainloop()
