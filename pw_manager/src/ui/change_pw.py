"""Change master password dialog."""
import tkinter as tk
from tkinter import messagebox
from src.ui import theme as T
from src.vault import Vault


class ChangePwDialog(tk.Toplevel):
    def __init__(self, master, vault: Vault):
        super().__init__(master)
        self._vault = vault
        self.title("マスターパスワードを変更")
        self.configure(bg=T.BG)
        self.resizable(False, False)
        self._center(380, 280)
        self.grab_set()
        self._build()

    def _center(self, w, h):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build(self):
        pad = T.PAD * 2
        container = tk.Frame(self, bg=T.BG)
        container.pack(fill="both", expand=True, padx=pad, pady=pad)

        def entry(label, show="●"):
            tk.Label(container, text=label, font=T.FONT_SMALL,
                     bg=T.BG, fg=T.FG2).pack(anchor="w")
            var = tk.StringVar()
            tk.Entry(
                container, textvariable=var, show=show,
                font=T.FONT_MONO, bg=T.BG2, fg=T.FG,
                insertbackground=T.FG, relief="flat",
                bd=1, highlightthickness=1,
                highlightbackground=T.BORDER, highlightcolor=T.ACCENT,
            ).pack(fill="x", ipady=4, pady=(0, T.PAD))
            return var

        self._new_var     = entry("新しいパスワード")
        self._confirm_var = entry("確認")

        btn_row = tk.Frame(container, bg=T.BG)
        btn_row.pack(fill="x", pady=(T.PAD, 0))
        tk.Button(btn_row, text="変更", font=T.FONT_BOLD,
                  bg=T.ACCENT, fg="white",
                  activebackground=T.ACCENT2, activeforeground="white",
                  relief="flat", cursor="hand2", padx=14, pady=6,
                  command=self._apply).pack(side="right")
        tk.Button(btn_row, text="キャンセル", font=T.FONT_MAIN,
                  bg=T.BG3, fg=T.FG, relief="flat", cursor="hand2",
                  padx=10, pady=6,
                  command=self.destroy).pack(side="right", padx=(0, 6))

    def _apply(self):
        pw = self._new_var.get()
        confirm = self._confirm_var.get()
        if not pw:
            messagebox.showerror("エラー", "パスワードを入力してください。", parent=self)
            return
        if len(pw) < 8:
            messagebox.showerror("エラー", "パスワードは8文字以上にしてください。", parent=self)
            return
        if pw != confirm:
            messagebox.showerror("エラー", "パスワードが一致しません。", parent=self)
            return
        try:
            self._vault.change_password(pw)
            messagebox.showinfo("完了", "パスワードを変更しました。", parent=self)
            self.destroy()
        except Exception as e:
            messagebox.showerror("エラー", str(e), parent=self)
