import os
import sys
import math
import tkinter as tk
from tkinter import filedialog, messagebox

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCREEN_W = 256
SCREEN_H = 224

BG_COLOR = "#000000"
TEXT_COLOR = "#3399FF"
PANEL_BG = "#050515"
ACCENT_COLOR = "#0055FF"


def _load_cython_core():
    if SCRIPT_DIR not in sys.path:
        sys.path.insert(0, SCRIPT_DIR)
    build_dir = os.path.join(SCRIPT_DIR, ".pyxbld")
    os.makedirs(build_dir, exist_ok=True)
    try:
        import pyximport
        pyximport.install(
            build_dir=build_dir,
            setup_args={"include_dirs": []},
        )
        import snes_cython_core
        return snes_cython_core
    except Exception as exc:
        print("Error compiling Cython core. Install Cython and a C compiler (clang/gcc).")
        print(f"Details: {exc}")
        sys.exit(1)


snes_cython_core = _load_cython_core()


def framebuffer_to_photoimage(frame_rgb: bytes) -> tk.PhotoImage:
    """Build a tk PhotoImage from raw 256x224 RGB bytes (PPM P6)."""
    header = f"P6 {SCREEN_W} {SCREEN_H} 255 ".encode("ascii")
    return tk.PhotoImage(width=SCREEN_W, height=SCREEN_H, data=header + frame_rgb, format="PPM")


class SNESEmulatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ac's snes emu 0.1a")
        self.root.geometry("600x480")
        self.root.configure(bg=BG_COLOR)

        self.core = snes_cython_core.SNESCore()
        self.rom_loaded = False
        self._photo = None

        self.build_ui()

    def build_ui(self):
        menubar = tk.Menu(self.root, bg=BG_COLOR, fg=TEXT_COLOR)
        filemenu = tk.Menu(menubar, tearoff=0, bg=BG_COLOR, fg=TEXT_COLOR)
        filemenu.add_command(label="Open ROM File", command=self.open_rom)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        self.root.config(menu=menubar)

        frame = tk.Frame(self.root, bg=BG_COLOR)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.header = tk.Label(
            frame,
            text="--- SNES CYTHON CORE (256x224) ---",
            font=("Courier", 14, "bold"),
            bg=BG_COLOR,
            fg=TEXT_COLOR,
        )
        self.header.pack(pady=5)

        self.display_screen = tk.Frame(
            frame,
            width=SCREEN_W,
            height=SCREEN_H,
            bg=PANEL_BG,
            highlightbackground=ACCENT_COLOR,
            highlightthickness=2,
        )
        self.display_screen.pack(pady=15)
        self.display_screen.pack_propagate(False)

        self.screen_canvas = tk.Label(
            self.display_screen,
            bg=PANEL_BG,
            fg=TEXT_COLOR,
            font=("Courier", 9),
            text="SYSTEM READY\n\nLOAD A VALID .SFC OR .SMC ROM",
        )
        self.screen_canvas.pack(expand=True)

        self.run_btn = tk.Button(
            frame,
            text="RUN CORE FRAMESTEP",
            command=self.execute_frame,
            state=tk.DISABLED,
            bg=PANEL_BG,
            fg=TEXT_COLOR,
            activebackground=ACCENT_COLOR,
            activeforeground=BG_COLOR,
        )
        self.run_btn.pack(pady=5)

        self.status_text = tk.StringVar(
            value=f"Status: Cython core ready. math.pi testing: {math.pi:.2f}"
        )
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_text,
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg=PANEL_BG,
            fg=TEXT_COLOR,
            font=("Courier", 9),
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _present_framebuffer(self):
        rgb = self.core.get_framebuffer()
        self._photo = framebuffer_to_photoimage(rgb)
        self.screen_canvas.config(image=self._photo, text="")

    def open_rom(self):
        file_path = filedialog.askopenfilename(
            initialdir=SCRIPT_DIR,
            filetypes=[
                ("SNES ROMs", "*.sfc *.smc"),
                ("Super Famicom ROM", "*.sfc"),
                ("Super NES ROM", "*.smc"),
                ("All Files", "*.*"),
            ],
        )
        if not file_path:
            return
        try:
            with open(file_path, "rb") as rom_file:
                rom_data = rom_file.read()

            if len(rom_data) % 1024 == 512:
                rom_data = rom_data[512:]

            core_msg = self.core.load_rom_bytes(rom_data)
            self.rom_loaded = True
            self.run_btn.config(state=tk.NORMAL)
            rom_name = os.path.basename(file_path)
            self.status_text.set(f"Loaded: {rom_name} — {core_msg}")
            self._present_framebuffer()
        except (OSError, ValueError) as exc:
            messagebox.showerror("Error Reading ROM", str(exc))

    def execute_frame(self):
        if not self.rom_loaded:
            return
        core_response = self.core.step_frame()
        self.status_text.set(f"Execution: {core_response}")
        self._present_framebuffer()


if __name__ == "__main__":
    root = tk.Tk()
    app = SNESEmulatorGUI(root)
    root.mainloop()
