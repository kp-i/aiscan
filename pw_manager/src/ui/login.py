"""Login / vault-setup window."""
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Optional, Callable

from src.ui import theme as T
from src.vault import Vault


class LoginWindow(tk.Toplevel):
    """Modal window that opens/creates a vault and returns a ready Vault."""

    def __init__(self, master: tk.Tk, on_success: Callable[[Vault, Path], None]):
        super().__init__(master)
        self.on_success = on_success
        self.vault: Optional[Vault] = None

        self.title("VaultKey - ログイン")
        self.configure(bg=T.BG)
        self.resizable(False, False)
        self._center(420, 460)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", master.destroy)

        self._build()

    def _center(self, w: int, h: int):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self):
        pad = T.PAD * 2

        # title
        tk.Label(self, text="🔐 VaultKey", font=T.FONT_TITLE,
                 bg=T.BG, fg=T.ACCENT).pack(pady=(pad * 2, pad))
        tk.Label(self, text="ローカル暗号化パスワードマネージャー",
                 font=T.FONT_SMALL, bg=T.BG, fg=T.FG2).pack(pady=(0, pad * 2))

        # vault path
        path_frame = tk.Frame(self, bg=T.BG)
        path_frame.pack(fill="x", padx=pad, pady=(0, T.PAD))

        tk.Label(path_frame, text="Vaultファイル", font=T.FONT_SMALL,
                 bg=T.BG, fg=T.FG2).pack(anchor="w")
        inner = tk.Frame(path_frame, bg=T.BG)
        inner.pack(fill="x")
        self._path_var = tk.StringVar(value="")
        self._path_entry = tk.Entry(
            inner, textvariable=self._path_var,
            font=T.FONT_MONO, bg=T.BG2, fg=T.FG,
            insertbackground=T.FG, relief="flat",
            bd=1, highlightthickness=1, highlightbackground=T.BORDER,
            highlightcolor=T.ACCENT,
        )
        self._path_entry.pack(side="left", fill="x", expand=True, ipady=4)
        tk.Button(
            inner, text="参照", font=T.FONT_SMALL,
            bg=T.BG3, fg=T.FG, activebackground=T.ACCENT2, activeforeground=T.FG,
            relief="flat", cursor="hand2", padx=8,
            command=self._browse,
        ).pack(side="left", padx=(4, 0))

        # password
        pw_frame = tk.Frame(self, bg=T.BG)
        pw_frame.pack(fill="x", padx=pad, pady=(0, T.PAD))

        tk.Label(pw_frame, text="マスターパスワード", font=T.FONT_SMALL,
                 bg=T.BG, fg=T.FG2).pack(anchor="w")
        self._pw_var = tk.StringVar()
        self._pw_entry = tk.Entry(
            pw_frame, textvariable=self._pw_var,
            show="●", font=T.FONT_MONO, bg=T.BG2, fg=T.FG,
            insertbackground=T.FG, relief="flat",
            bd=1, highlightthickness=1, highlightbackground=T.BORDER,
            highlightcolor=T.ACCENT,
        )
        self._pw_entry.pack(fill="x", ipady=5)
        self._pw_entry.bind("<Return>", lambda _: self._open())

        # confirm (shown only for new vault)
        self._confirm_frame = tk.Frame(self, bg=T.BG)
        self._confirm_frame.pack(fill="x", padx=pad, pady=(0, T.PAD))
        tk.Label(self._confirm_frame, text="パスワード確認 (新規作成時)", font=T.FONT_SMALL,
                 bg=T.BG, fg=T.FG2).pack(anchor="w")
        self._confirm_var = tk.StringVar()
        self._confirm_entry = tk.Entry(
            self._confirm_frame, textvariable=self._confirm_var,
            show="●", font=T.FONT_MONO, bg=T.BG2, fg=T.FG,
            insertbackground=T.FG, relief="flat",
            bd=1, highlightthickness=1, highlightbackground=T.BORDER,
            highlightcolor=T.ACCENT,
        )
        self._confirm_entry.pack(fill="x", ipady=5)
        self._confirm_entry.bind("<Return>", lambda _: self._open())

        # buttons
        btn_frame = tk.Frame(self, bg=T.BG)
        btn_frame.pack(fill="x", padx=pad, pady=(T.PAD, 0))

        tk.Button(
            btn_frame, text="開く / 作成",
            font=T.FONT_BOLD, bg=T.ACCENT, fg="white",
            activebackground=T.ACCENT2, activeforeground="white",
            relief="flat", cursor="hand2", pady=8,
            command=self._open,
        ).pack(fill="x")

        tk.Label(self, text="ファイルが存在しない場合は新規作成されます",
                 font=T.FONT_SMALL, bg=T.BG, fg=T.FG2).pack(pady=(T.PAD, 0))

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Vaultファイルを選択",
            filetypes=[("VaultKey files", "*.vkey"), ("All files", "*.*")],
        )
        if path:
            self._path_var.set(path)

    def _open(self):
        path_str = self._path_var.get().strip()
        pw = self._pw_var.get()
        confirm = self._confirm_var.get()

        if not path_str:
            messagebox.showerror("エラー", "Vaultファイルのパスを指定してください。", parent=self)
            return
        if not pw:
            messagebox.showerror("エラー", "マスターパスワードを入力してください。", parent=self)
            return

        path = Path(path_str)
        if not path.suffix:
            path = path.with_suffix(".vkey")

        vault = Vault()
        try:
            if path.exists():
                vault.load(path, pw)
            else:
                if pw != confirm:
                    messagebox.showerror("エラー", "パスワードが一致しません。", parent=self)
                    return
                if len(pw) < 8:
                    messagebox.showerror("エラー", "パスワードは8文字以上にしてください。", parent=self)
                    return
                vault.new(path, pw)
        except ValueError as e:
            messagebox.showerror("認証エラー", str(e), parent=self)
            return
        except Exception as e:
            messagebox.showerror("エラー", f"Vaultを開けませんでした:\n{e}", parent=self)
            return

        self.destroy()
        self.on_success(vault, path)
