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
    timestamp: float
    interval: float | None


class SetterApp:
    POSITIONS = {1: "1 - Delante", 2: "2 - Delante", 3: "3 - Delante",
                 4: "4 - Detras", 5: "5 - Detras", 6: "6 - Detras"}

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
        self.tracking = tk.BooleanVar(value=True)
        self.show_overlay = tk.BooleanVar(value=True)
        self.selected_position = tk.IntVar(value=1)
        self.min_radius, self.max_radius = tk.IntVar(value=5), tk.IntVar(value=35)
        self.saturation, self.value = tk.IntVar(value=45), tk.IntVar(value=80)
        self.trail: list[tuple[int, int]] = []
        self.placements: list[Placement] = []
        self.photo: ImageTk.PhotoImage | None = None
        self._build_ui()
        self.root.report_callback_exception = self.report_callback_exception
        self.root.bind("<space>", lambda _event: self.record_placement())
        for number in range(1, 7):
            self.root.bind(str(number), lambda _event, n=number: self.selected_position.set(n))
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _build_ui(self) -> None:
        self.root.configure(bg="#10161f")
        style = ttk.Style(self.root); style.theme_use("clam")
        style.configure("TFrame", background="#10161f"); style.configure("TLabel", background="#10161f", foreground="#e8eef7")
        style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground="#62d5c8"); style.configure("TButton", padding=7)
        style.configure("Treeview", rowheight=26, background="#1b2430", fieldbackground="#1b2430", foreground="#f4f7fb")
        style.configure("Treeview.Heading", background="#263445", foreground="#ffffff")
        header = ttk.Frame(self.root, padding=(18, 14, 18, 8)); header.pack(fill="x")
        ttk.Label(header, text="SetterApp Volley", style="Header.TLabel").pack(side="left")
        ttk.Label(header, text=" - video analysis", font=("Segoe UI", 10)).pack(side="left", pady=5)
        ttk.Button(header, text="Open video", command=self.open_video).pack(side="right")
        main = ttk.Frame(self.root, padding=(18, 0, 18, 18)); main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=3); main.columnconfigure(1, weight=1); main.rowconfigure(0, weight=1)
        viewer = ttk.Frame(main); viewer.grid(row=0, column=0, sticky="nsew", padx=(0, 14)); viewer.rowconfigure(0, weight=1); viewer.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(viewer, bg="#080b10", highlightthickness=0); self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.create_text(30, 30, anchor="nw", fill="#8493a7", text="Open a video to start", tags="empty")
        controls = ttk.Frame(viewer, padding=(0, 12, 0, 0)); controls.grid(row=1, column=0, sticky="ew"); controls.columnconfigure(1, weight=1)
        self.play_button = ttk.Button(controls, text="Play", command=self.toggle_play, state="disabled"); self.play_button.grid(row=0, column=0, padx=(0, 8))
        self.seek = ttk.Scale(controls, from_=0, to=1, command=self.seek_video); self.seek.grid(row=0, column=1, sticky="ew")
        self.time_label = ttk.Label(controls, text="00:00.000 / 00:00.000", width=22); self.time_label.grid(row=0, column=2, padx=(8, 0))
        sidebar = ttk.Frame(main); sidebar.grid(row=0, column=1, sticky="nsew"); sidebar.columnconfigure(0, weight=1)
        ttk.Label(sidebar, text="Placement target", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 6))
        pos_frame = ttk.Frame(sidebar); pos_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        for i in range(1, 7): ttk.Radiobutton(pos_frame, text=self.POSITIONS[i], value=i, variable=self.selected_position).grid(row=(i - 1) // 2, column=(i - 1) % 2, sticky="w", padx=(0, 12), pady=2)
        self.record_button = ttk.Button(sidebar, text="Mark placement (Space)", command=self.record_placement, state="disabled"); self.record_button.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        ttk.Label(sidebar, text="Tracking", font=("Segoe UI", 12, "bold")).grid(row=3, column=0, sticky="w", pady=(0, 6))
        ttk.Checkbutton(sidebar, text="Detect ball", variable=self.tracking).grid(row=4, column=0, sticky="w"); ttk.Checkbutton(sidebar, text="Show trail", variable=self.show_overlay).grid(row=5, column=0, sticky="w", pady=(0, 7))
        ttk.Label(sidebar, text="Minimum / maximum radius").grid(row=6, column=0, sticky="w")
        radius = ttk.Frame(sidebar); radius.grid(row=7, column=0, sticky="ew")
        ttk.Spinbox(radius, from_=2, to=100, textvariable=self.min_radius, width=6).pack(side="left"); ttk.Label(radius, text=" - ").pack(side="left"); ttk.Spinbox(radius, from_=5, to=150, textvariable=self.max_radius, width=6).pack(side="left")
        ttk.Button(sidebar, text="Clear trail", command=self.clear_trail).grid(row=8, column=0, sticky="ew", pady=(10, 4)); ttk.Button(sidebar, text="Export CSV", command=self.export_csv).grid(row=9, column=0, sticky="ew", pady=(0, 14))
        ttk.Label(sidebar, text="Registered timings", font=("Segoe UI", 12, "bold")).grid(row=10, column=0, sticky="w", pady=(0, 6))
        self.table = ttk.Treeview(sidebar, columns=("n", "position", "time", "interval"), show="headings", height=12); self.table.grid(row=11, column=0, sticky="nsew"); sidebar.rowconfigure(11, weight=1)
        for column, title, width in (("n", "#", 35), ("position", "Target", 105), ("time", "Video", 75), ("interval", "Delta", 75)): self.table.heading(column, text=title); self.table.column(column, width=width, anchor="center")
        self.status = ttk.Label(sidebar, text="Ready. Open a video.", foreground="#94a5ba", wraplength=300); self.status.grid(row=12, column=0, sticky="sw", pady=(10, 0))

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
            self.trail.clear(); self.placements.clear()
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
        if self.cap and not self.playing and not self.updating_seek: self.frame_index = int(float(value)); self.show_frame()

    def show_frame(self) -> None:
        if not self.cap: return
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_index); ok, frame = self.cap.read()
        if not ok: raise RuntimeError(f"Could not decode frame {self.frame_index}.")
        if self.tracking.get():
            point = self.detect_ball(frame)
            if point: self.trail.append(point)
        if self.show_overlay.get(): self.draw_overlay(frame)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB); image = Image.fromarray(rgb); image.thumbnail((self.canvas.winfo_width() or 900, self.canvas.winfo_height() or 600), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(image); self.canvas.delete("all"); self.canvas.create_image(self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2, image=self.photo, anchor="center")
        self.updating_seek = True
        try: self.seek.set(self.frame_index)
        finally: self.updating_seek = False
        now = self.frame_index / self.fps; self.time_label.configure(text=f"{self.format_time(now)} / {self.format_time(self.frame_count / self.fps)}")

    def detect_ball(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV); mask = cv2.inRange(hsv, (0, self.saturation.get(), self.value.get()), (180, 255, 255)); mask = cv2.medianBlur(mask, 5)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); best, best_score = None, 0.0
        for contour in contours:
            area, perimeter = cv2.contourArea(contour), cv2.arcLength(contour, True)
            if perimeter == 0: continue
            radius, circularity = math.sqrt(area / math.pi), 4 * math.pi * area / (perimeter * perimeter)
            if self.min_radius.get() <= radius <= self.max_radius.get() and circularity >= 0.35 and circularity * radius > best_score:
                (x, y), _ = cv2.minEnclosingCircle(contour); best, best_score = (int(x), int(y)), circularity * radius
        return best

    def draw_overlay(self, frame) -> None:
        for first, second in zip(self.trail, self.trail[1:]): cv2.line(frame, first, second, (71, 220, 196), 3, cv2.LINE_AA)
        if self.trail: cv2.circle(frame, self.trail[-1], 8, (30, 240, 255), 2, cv2.LINE_AA)

    def record_placement(self) -> None:
        if not self.cap: return
        timestamp = self.frame_index / self.fps; interval = timestamp - self.placements[-1].timestamp if self.placements else None
        placement = Placement(len(self.placements) + 1, self.POSITIONS[self.selected_position.get()], timestamp, interval); self.placements.append(placement)
        self.table.insert("", "end", values=(placement.number, placement.position, self.format_time(timestamp), "-" if interval is None else f"{interval:.3f} s")); self.status.configure(text=f"Marked {placement.position} at {self.format_time(timestamp)}")

    def clear_trail(self) -> None:
        self.trail.clear(); self.show_frame()

    def export_csv(self) -> None:
        if not self.placements: messagebox.showinfo("Export", "No placements have been registered yet."); return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], initialfile="placement_timings.csv")
        if not path: return
        with open(path, "w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle); writer.writerow(["number", "target", "timestamp_s", "interval_s"])
            for item in self.placements: writer.writerow([item.number, item.position, f"{item.timestamp:.3f}", "" if item.interval is None else f"{item.interval:.3f}"])
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
