import win32con
import ctypes
from ctypes import wintypes, POINTER, c_void_p, c_long, c_longlong, c_ulong, c_ulonglong
import atexit
import os
import sys
import logging
import orthy

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.OrthyPlugin_Interface import OrthyPlugin

# Define ULONG_PTR if not available
if not hasattr(wintypes, 'ULONG_PTR'):
    if ctypes.sizeof(c_void_p) == ctypes.sizeof(c_ulonglong):
        wintypes.ULONG_PTR = c_ulonglong
    else:
        wintypes.ULONG_PTR = c_ulong

# Define LRESULT if not available
if not hasattr(wintypes, 'LRESULT'):
    if ctypes.sizeof(c_void_p) == ctypes.sizeof(c_longlong):
        wintypes.LRESULT = c_longlong
    else:
        wintypes.LRESULT = c_long

# Define HHOOK, HINSTANCE, and HMODULE if not available
if not hasattr(wintypes, 'HHOOK'):
    wintypes.HHOOK = wintypes.HANDLE
if not hasattr(wintypes, 'HINSTANCE'):
    wintypes.HINSTANCE = wintypes.HANDLE
if not hasattr(wintypes, 'HMODULE'):
    wintypes.HMODULE = wintypes.HANDLE

# Structure used by the keyboard hook callback
class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode",   wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags",    wintypes.DWORD),
        ("time",     wintypes.DWORD),
        ("dwExtraInfo", wintypes.ULONG_PTR)
    ]

class LowLevelKeyboardRemapper(OrthyPlugin):
    def __init__(self):
        self.app = None
        self.active_mode = False
        self.hook = None
        self.registered = False

        # We'll treat space as "problem" key (like Alt was before)
        self.VK_SPACE = 0x20
        self.space_pressed = False  # track whether space is currently pressed

        # Basic letter keys
        self.VK_W = 0x57
        self.VK_A = 0x41
        self.VK_S = 0x53
        self.VK_D = 0x44
        self.VK_E = 0x45
        self.VK_F = 0x46
        self.VK_V = 0x56
        self.VK_L = 0x4C

        # Arrow keys
        self.VK_UP    = 0x26
        self.VK_DOWN  = 0x28
        self.VK_LEFT  = 0x25
        self.VK_RIGHT = 0x27

        # Plus / Minus (OEM)
        self.VK_PLUS  = 0xBB  # OEM_PLUS
        self.VK_MINUS = 0xBD  # OEM_MINUS

        # Build a two-way mapping:
        #  W <-> Up Arrow, A <-> Left Arrow, S <-> Down Arrow, D <-> Right Arrow
        #  E <-> Plus,      F <-> Minus
        # This means pressing W sends Up, pressing Up sends W, etc.
        # You can expand or tweak as desired.
        self.key_map = {
            # WASD -> Arrows
            self.VK_W:    self.VK_UP,
            self.VK_A:    self.VK_LEFT,
            self.VK_S:    self.VK_DOWN,
            self.VK_D:    self.VK_RIGHT,

            # E/F -> plus/minus
            self.VK_E:    self.VK_PLUS,
            self.VK_F:    self.VK_MINUS,
            self.VK_V:    self.VK_L
        }

        # Build a set of all keys we want to hook
        self.hooked_keys = set(self.key_map.keys())

        atexit.register(self.cleanup)

    def get_name(self):
        return "LowLevelKeyboardRemapper"

    def get_btn_configs(self):
        return [{
            'text': 'WASD Remap',
            'command': self.toggle_remap,
            'grid': {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 2, 'sticky': 'ew'},
            'width': 10,
            'variable_name': 'btn_toggle_low_level_remap',
            'bg': 'red',
            'fg': 'white'
        }]

    def toggle_remap(self):
        """Enable or disable the two-way remapping."""
        logging.debug("[LLRemapper] toggle_remap called.")
        self.set_active_mode(not self.active_mode)

    def set_active_mode(self, state: bool):
        """
        Merge activate/deactivate logic into one method.
        Forcibly release space if turning off.
        """
        logging.debug(f"[LLRemapper] set_active_mode called with state={state}")
        if not self.registered:
            self.app.register_plugin_sentinels(self.get_name(), self.active_mode)
            self.active_mode = state
            self.registered = True

        if self.registered:
            self.active_mode = state
            if state:
                self.update_button()
                logging.info("[LLRemapper] Activated")
            else:
                # If we're turning it off, forcibly release space
                logging.debug("[LLRemapper] Forcibly releasing Space to prevent sticky issues.")
                user32 = ctypes.windll.user32
                user32.keybd_event(self.VK_SPACE, 0, win32con.KEYEVENTF_KEYUP, 0)

                self.update_button()
                logging.info("[LLRemapper] Deactivated")

    def initialize(self, app_instance):
        """Called by the plugin loader to initialize the plugin."""
        self.app = app_instance
        self.start_hook()

    def start_hook(self):
        """Installs a low-level keyboard hook if not already present."""
        if self.hook:
            logging.debug("[LLRemapper] Hook already installed, skipping.")
            return

        logging.debug("[LLRemapper] Installing keyboard hook...")
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        HOOKPROC = ctypes.WINFUNCTYPE(wintypes.LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
        self.pointer = HOOKPROC(self.low_level_handler)

        user32.SetWindowsHookExA.argtypes = [wintypes.INT, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
        user32.SetWindowsHookExA.restype = wintypes.HHOOK

        user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
        user32.CallNextHookEx.restype = wintypes.LRESULT

        user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
        user32.UnhookWindowsHookEx.restype = wintypes.BOOL

        kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
        kernel32.GetModuleHandleW.restype = wintypes.HINSTANCE

        hMod = kernel32.GetModuleHandleW(None)

        self.hook = user32.SetWindowsHookExA(
            win32con.WH_KEYBOARD_LL,
            self.pointer,
            hMod,
            0
        )

        if self.hook:
            logging.info("[LLRemapper] Keyboard hook installed")
        else:
            logging.error("[LLRemapper] Failed to install keyboard hook")

    def low_level_handler(self, nCode, wParam, lParam):
        """
        The low-level keyboard callback. 
        We only do something special if 'active_mode' is True 
        and vkCode is in self.hooked_keys. 
        Otherwise, pass the event to the next hook.
        """
        user32 = ctypes.windll.user32

        if not self.active_mode:
            return user32.CallNextHookEx(self.hook, nCode, wParam, lParam)

        if nCode != win32con.HC_ACTION:
            return user32.CallNextHookEx(self.hook, nCode, wParam, lParam)

        kb_struct = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
        vk_code = kb_struct.vkCode

        # Determine if it's a DOWN or UP event
        if wParam in (win32con.WM_KEYDOWN, win32con.WM_SYSKEYDOWN):
            event_type = "DOWN"
        elif wParam in (win32con.WM_KEYUP, win32con.WM_SYSKEYUP):
            event_type = "UP"
        else:
            event_type = "UNKNOWN"

        logging.debug(f"[LLRemapper] Intercepted vkCode={vk_code}, event={event_type}")

        # Track space usage, but do not block it
        if vk_code == self.VK_SPACE:
            if event_type == "DOWN":
                self.space_pressed = True
                logging.debug("[LLRemapper] Space pressed.")
            elif event_type == "UP":
                self.space_pressed = False
                logging.debug("[LLRemapper] Space released.")
            # Let space pass through
            return user32.CallNextHookEx(self.hook, nCode, wParam, lParam)

        # If key is in the 2-way map, block the original and inject the mapped key
        if vk_code in self.key_map:
            mapped_key = self.key_map[vk_code]
            try:
                if event_type == "DOWN":
                    logging.debug(f"[LLRemapper] Remapping {vk_code} (DOWN) -> {mapped_key}")
                    user32.keybd_event(mapped_key, 0, 0, 0)
                elif event_type == "UP":
                    logging.debug(f"[LLRemapper] Remapping {vk_code} (UP) -> {mapped_key}")
                    user32.keybd_event(mapped_key, 0, win32con.KEYEVENTF_KEYUP, 0)

                # Return -1 to block the original
                return -1
            except Exception as e:
                logging.error(f"[LLRemapper] Error remapping {vk_code}: {e}")
                return user32.CallNextHookEx(self.hook, nCode, wParam, lParam)

        # Otherwise, pass everything else along
        return user32.CallNextHookEx(self.hook, nCode, wParam, lParam)

    def cleanup(self):
        """
        Uninstalls the keyboard hook if present,
        forcibly releases space if it's pressed, then logs cleanup.
        """
        logging.info("[LLRemapper] Cleanup initiated.")
        # 1. Unhook if present
        if self.hook:
            ctypes.windll.user32.UnhookWindowsHookEx(self.hook)
            self.hook = None
            logging.info("[LLRemapper] Keyboard hook removed")

        # 2. If space is stuck, forcibly release it
        if self.space_pressed:
            logging.warning("[LLRemapper] Space is stuck, releasing it now.")
            user32 = ctypes.windll.user32
            user32.keybd_event(self.VK_SPACE, 0, win32con.KEYEVENTF_KEYUP, 0)
            self.space_pressed = False

        logging.info("[LLRemapper] Cleanup complete.")

    def update_button(self):
        """Updates the plugin sentinel and plugin button UI."""
        logging.debug("[LLRemapper] update_button called.")
        self.app.update_plugin_sentinels(self.get_name(), self.active_mode)
        self.app.update_plugin_buttons(self.get_name())
