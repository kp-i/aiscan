"""VaultKey — entry point."""
import sys
import tkinter as tk
from pathlib import Path

# When frozen by PyInstaller, sys.path needs adjustment
if getattr(sys, "frozen", False):
    import os
    os.chdir(Path(sys.executable).parent)
    sys.path.insert(0, str(Path(sys.executable).parent))

from src.ui import theme as T
from src.ui.login import LoginWindow
from src.ui.main_window import MainWindow
from src.vault import Vault


def main():
    root = tk.Tk()
    root.withdraw()  # hide until login completes
    root.configure(bg=T.BG)

    # Windows: use DPI-aware mode for crisp rendering
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    def on_login(vault: Vault, path: Path):
        root.deiconify()
        root.geometry("900x580")
        MainWindow(root, vault, path)

    LoginWindow(root, on_success=on_login)
    root.mainloop()


if __name__ == "__main__":
    main()
