import logging
import os
import ctypes
from ctypes import wintypes
from tkinter import messagebox, filedialog, Toplevel, Label, Frame, Button, Radiobutton, StringVar
from pynput import keyboard, mouse
from pynput.keyboard import Key
from core.OrthyPlugin_Interface import OrthyPlugin
from Test_py_files.ButtonFactory import ButtonFactory

class MaestroControlsPlugin(OrthyPlugin):
    def __init__(self):
        self.app = None  # Reference to the main app
        self.full_control_mode = False
        self.full_control_hotkey_listener = None
        self.maestro_version = None
        self.maestro_location = None
        self.ghost_click_positions = {}
        self.space_pressed = False  # replaces alt_pressed
        self.ctrl_pressed = False
        self.coords_loaded = False
        self.registered = False

    def initialize(self, app_instance):
        self.app = app_instance

    def get_name(self):
        return "Maestro Controls"

    def get_btn_configs(self):
        return [{
            'text': 'Maestro Controls',
            'command': self.toggle_full_control,
            'grid': {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 2, 'sticky': 'ew'},
            'width': 10,
            'variable_name': 'btn_toggle_full_control_maestro',
            'bg': 'red',
            'fg': 'white'
        }]

    def toggle_full_control(self):
        if not self.registered:
            self.app.register_plugin_sentinels(self.get_name(), self.full_control_mode)
            self.registered = True

        if not self.full_control_mode:
            # Enabling full control mode
            if self.maestro_version is not None and self.coords_loaded is True:
                self.full_control_mode = True
                self.start_full_control_hotkeys()
                keyboard_remapper = self.app.plugin_loader.get_plugin('LowLevelKeyboardRemapper')
                if keyboard_remapper is not None:
                    keyboard_remapper.toggle_remap()
                self.update_button()
                logging.info(f"Full Control Mode Resumed for Maestro {self.maestro_version}")
                return

            version, location = self.prompt_maestro_settings()
            if not version or not location:
                return
            self.maestro_version = version
            self.maestro_location = location

            if not self.setup_coordinates():
                return

            self.full_control_mode = True
            keyboard_remapper = self.app.plugin_loader.get_plugin('LowLevelKeyboardRemapper')
            self.start_full_control_hotkeys()
            if keyboard_remapper:
                keyboard_remapper.toggle_remap()
            self.update_button()
            logging.info(f"Full Control Mode Enabled for Maestro {self.maestro_version} {self.maestro_location}")

        else:
            # Disabling full control mode
            self.full_control_mode = False
            keyboard_remapper = self.app.plugin_loader.get_plugin('LowLevelKeyboardRemapper')
            if keyboard_remapper:
                keyboard_remapper.toggle_remap()
            self.stop_full_control_hotkeys()
            self.update_button()
            logging.info("Full Control Mode Disabled")

    def setup_coordinates(self):
        """
        1. Check if coords file for current maestro_version exists.
        2. If yes, load it. If no, prompt user for manual coords or skip.
        """
        coords_file = os.path.join(self.app.base_dir, f'coords_maestro_{self.maestro_version}_{self.maestro_location}.txt')
        print(coords_file)
        if os.path.exists(coords_file):
            logging.info(f"Coordinates file found: {coords_file}")
            if self.load_coords_from_file(coords_file):
                self.coords_loaded = True
                logging.info(f"Coordinates for Maestro {self.maestro_version} loaded from {coords_file} without prompting.")
                return True
            else:
                logging.error("Failed to load existing coords file. Will prompt user.")

        response = messagebox.askyesno(
            "Coordinate Setup",
            "Coordinates file not found.\nClick Yes to select coords manually, No to skip full control setup."
        )
        if response:
            if not self.select_control_coordinates():
                return False
            self.coords_loaded = True
        else:
            logging.info("User skipped coordinate setup. Full control mode not enabled.")
            return False

        return True

    def select_control_coordinates(self):
        controls = [
            'MesialTip', 'DistalTip',
            'MesialRotation', 'DistalRotation',
            'PositiveTorque', 'NegativeTorque',
            'BuccalLinear', 'LingualLinear',
            'Intrusion', "Extrusion",
            'MesialLinear', 'DistalLinear',
            "Occlusion", "Occlusion_Left", "Occlusion_Right",
            "EnFace", "BottomView", "TopView",
            "Play", "GridView",
            'InitialUpper', 'SecondUpper', 'ThirdUpper', 'FinalUpper',
            'InitialLower', 'SecondLower', 'ThirdLower', 'FinalLower',
            'UpperArch', 'LowerArch',
        ]
        self.ghost_click_positions = {}

        for control in controls:
            messagebox.showinfo("Select Control", f"Please click on the '{control}' control on the screen.")
            self.app.root.withdraw()
            self.app.image_window.withdraw()
            pos = self.wait_for_click()
            self.app.root.deiconify()
            self.app.image_window.deiconify()
            if pos is None:
                logging.error(f"Failed to record position for {control}")
                return False
            self.ghost_click_positions[control] = pos

        self.save_coords_to_file(controls)
        return True

    def wait_for_click(self):
        position = [None]

        def on_click(x, y, button, pressed):
            if pressed and button == mouse.Button.left:
                position[0] = (x, y)
                return False  # Stop listener after one click

        with mouse.Listener(on_click=on_click) as listener:
            listener.join()
        return position[0]

    def save_coords_to_file(self, controls):
        coords_file = os.path.join(
            self.app.base_dir,
            f'coords_maestro_{self.maestro_version}_{self.maestro_location}.txt'
        )
        try:
            with open(coords_file, 'w') as f:
                for c in controls:
                    pos = self.ghost_click_positions.get(c)
                    if pos:
                        f.write(f"{c}:{pos[0]},{pos[1]}\n")
            logging.info(f"Coordinates saved to {coords_file}")
            messagebox.showinfo("Coordinates Saved", f"Coordinates saved to {coords_file}")
        except Exception as e:
            logging.error(f"Failed to save coordinates: {e}")
            messagebox.showerror("Save Failed", "Failed to save coordinates")

    def load_coords_from_file(self, filepath):
        try:
            self.ghost_click_positions.clear()
            with open(filepath, 'r') as f:
                for line in f:
                    if ':' not in line:
                        continue
                    control, pos = line.strip().split(':')
                    x_str, y_str = pos.split(',')
                    self.ghost_click_positions[control] = (int(x_str), int(y_str))
            logging.info(f"Coordinates loaded from {filepath}")
            return True
        except Exception as e:
            logging.error(f"Failed to load coordinates from file: {e}")
            messagebox.showerror("Load Failed", "Failed to load coordinates from the file")
            return False

    def prompt_maestro_version(self):
        return self.create_dual_prompt("Maestro 4", "Maestro 6")

    def prompt_maestro_settings(self):
        selected_version = [None]
        selected_location = [None]

        def submit():
            selected_version[0] = version_var.get()
            selected_location[0] = location_var.get()
            top.destroy()

        top = Toplevel(self.app.root)
        top.title("Select Maestro Settings")
        top.attributes('-topmost', True)
        top.grab_set()

        #Add as many versions as needed by adding more Radiobuttons
        Label(top, text="Select Maestro version:").pack(pady=5)
        version_var = StringVar()
        Radiobutton(top, text="Maestro 4", variable=version_var, value="4").pack()
        Radiobutton(top, text="Maestro 6", variable=version_var, value="6").pack()
        Radiobutton(top, text="Maestro 7", variable=version_var, value="7").pack()  # Added option

        Label(top, text="Select Location:").pack(pady=5)
        location_var = StringVar()
        Radiobutton(top, text="Laptop", variable=location_var, value="laptop").pack()
        Radiobutton(top, text="Office", variable=location_var, value="office").pack()
        Radiobutton(top, text="Home",   variable=location_var, value="home").pack()

        Button(top, text="OK", command=submit).pack(pady=10)

        top.update_idletasks()
        w, h = top.winfo_width(), top.winfo_height()
        x = (top.winfo_screenwidth() // 2) - (w // 2)
        y = (top.winfo_screenheight() // 2) - (h // 2)
        top.geometry(f'{w}x{h}+{x}+{y}')
        top.wait_window()

        return selected_version[0], selected_location[0]

    def create_dual_prompt(self, option1, option2):
        selected = [None]

        def select_option(option):
            selected[0] = option
            top.destroy()

        top = self._create_modal_window("Select Maestro Version")
        top.width = 150
        top.height = 150
        self._center_window(top)
        self._add_prompt_controls(top, "Select Maestro version:", option1, option2, select_option)
        top.wait_window()
        return selected[0]

    def start_full_control_hotkeys(self):
        """
        Use SPACE instead of ALT as the modifier. 
        So if space_pressed is True, we do combos. 
        Otherwise, the logic is the same as alt-based combos.
        """
        if self.full_control_hotkey_listener:
            self.stop_full_control_hotkeys()

        def on_press(key):
            if key in (Key.ctrl_l, Key.ctrl_r):
                self.ctrl_pressed = True
            if key == Key.space:
                self.space_pressed = True
            # If space is pressed, handle combos
            if self.space_pressed:
                self.handle_space_combos(key)
            return True

        def on_release(key):
            if key in (Key.ctrl_l, Key.ctrl_r):
                self.ctrl_pressed = False
            if key == Key.space:
                self.space_pressed = False
            return True

        try:
            self.full_control_hotkey_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            self.full_control_hotkey_listener.start()
        except Exception as e:
            logging.error(f"Failed to start hotkeys: {e}")
            messagebox.showerror("Hotkey Error", f"Could not start hotkeys: {e}")

    def handle_space_combos(self, key):
        """
        Replaces handle_alt_combos, but logic is the same:
        If ctrl is pressed along with space, do "ctrl combos" 
        Otherwise do "regular combos." 
        """
        if self.ctrl_pressed:
            if key == Key.up:
                self.perform_ghost_click('BuccalLinear')
            elif key == Key.down:
                self.perform_ghost_click('LingualLinear')
            # Additional ctrl+space combos if needed
        else:
            # Just space
            if key == Key.up:
                self.perform_ghost_click('PositiveTorque')
            elif key == Key.down:
                self.perform_ghost_click('NegativeTorque')
            elif key == Key.right:
                self.perform_ghost_click('MesialLinear')
            elif key == Key.left:
                self.perform_ghost_click('DistalLinear')
            elif hasattr(key, 'char'):
                mapping = {
                    'e': 'MesialTip',
                    'q': 'DistalTip',
                    'z': 'DistalRotation',
                    'c': 'MesialRotation',
                    'x': 'Intrusion',
                    'v': 'Extrusion',
                    '1': 'EnFace',
                    '2': 'BottomView',
                    '3': 'TopView',
                    'r': 'Occlusion',
                    '4': 'GridView',
                    '5': 'InitialUpper',
                    '6': 'SecondUpper',
                    'y': 'ThirdUpper', 
                    't': 'FinalUpper',
                    'g': 'InitialLower',
                    'h': 'SecondLower',
                    'n': 'ThirdLower',
                    'b': 'FinalLower',
                    'k': 'UpperArch',
                    'm': 'LowerArch',
                    'p': 'Occlusion_Left',
                    'o': 'Occlusion_Right',
                    'f': 'Play',
                }
                action = mapping.get(key.char)
                if action:
                    self.perform_ghost_click(action)

    def stop_full_control_hotkeys(self):
        if self.full_control_hotkey_listener:
            self.full_control_hotkey_listener.stop()
            self.full_control_hotkey_listener = None

    def perform_ghost_click(self, action_name):
        pos = self.ghost_click_positions.get(action_name)
        if not pos:
            logging.error(f"No position for '{action_name}'")
            return
        original = self.get_cursor_pos()
        self.ghost_click_at_position(pos)
        self.set_cursor_pos(*original)
        logging.info(f"Performed ghost click on action '{action_name}' at position {pos}.")

    def get_cursor_pos(self):
        pt = wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return (pt.x, pt.y)

    def set_cursor_pos(self, x, y):
        ctypes.windll.user32.SetCursorPos(x, y)

    def ghost_click_at_position(self, pos):
        x, y = pos
        screen_w = ctypes.windll.user32.GetSystemMetrics(0)
        screen_h = ctypes.windll.user32.GetSystemMetrics(1)
        abs_x = int(x * 65536 / screen_w)
        abs_y = int(y * 65536 / screen_h)

        INPUT_MOUSE = 0
        MOUSE_MOVE = 0x0001 | 0x8000
        MOUSE_DOWN = 0x0002
        MOUSE_UP = 0x0004

        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [
                ("dx", ctypes.c_long), 
                ("dy", ctypes.c_long), 
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong), 
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
            ]

        class INPUT(ctypes.Structure):
            _fields_ = [("type", ctypes.c_ulong), ("mi", MOUSEINPUT)]

        def make_input(dx, dy, flags):
            inp = INPUT()
            inp.type = INPUT_MOUSE
            inp.mi = MOUSEINPUT(dx=dx, dy=dy, mouseData=0, dwFlags=flags, time=0, dwExtraInfo=None)
            return inp

        inputs = (
            make_input(abs_x, abs_y, MOUSE_MOVE),
            make_input(0, 0, MOUSE_DOWN),
            make_input(0, 0, MOUSE_UP)
        )

        ctypes.windll.user32.SendInput(len(inputs), (INPUT * len(inputs))(*inputs), ctypes.sizeof(INPUT))

    def cleanup(self):
        if self.full_control_hotkey_listener:
            self.stop_full_control_hotkeys()

    def _create_modal_window(self, title):
        top = Toplevel(self.app.root)
        top.title(title)
        top.attributes('-topmost', True)
        top.grab_set()
        return top

    def _add_prompt_controls(self, parent, prompt_text, option1, option2, callback):
        Label(parent, text=prompt_text).pack(pady=10)
        btn_frame = Frame(parent)
        btn_frame.pack(pady=10)
        Button(btn_frame, text=option1, command=lambda: callback(option1)).pack(side='left', padx=20)
        Button(btn_frame, text=option2, command=lambda: callback(option2)).pack(side='right', padx=20)

    def _center_window(self, window):
        window.update_idletasks()
        w = window.winfo_width()
        h = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (w // 2)
        y = (window.winfo_screenheight() // 2) - (h // 2)
        window.geometry(f'{w}x{h}+{x}+{y}')

    def update_button(self):
        self.app.update_plugin_sentinels(self.get_name(), self.full_control_mode)
        self.app.update_plugin_buttons(self.get_name())
                                                    