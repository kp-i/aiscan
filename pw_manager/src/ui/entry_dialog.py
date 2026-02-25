"""Add / Edit entry dialog."""
import tkinter as tk
from tkinter import messagebox
from typing import Optional

from src.ui import theme as T
from src.vault import Entry, DEFAULT_CATEGORIES
from src.generator import generate, estimate_strength


class EntryDialog(tk.Toplevel):
    """Modal dialog for creating or editing a vault entry."""

    def __init__(self, master, entry: Optional[Entry] = None, on_save=None):
        super().__init__(master)
        self._entry = entry
        self._on_save = on_save
        self._result: Optional[Entry] = None

        title = "エントリを編集" if entry else "エントリを追加"
        self.title(title)
        self.configure(bg=T.BG)
        self.resizable(False, False)
        self._center(500, 620)
        self.grab_set()

        self._build()
        if entry:
            self._populate(entry)

    def _center(self, w: int, h: int):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _labeled_entry(self, parent, label: str, show: str = "") -> tk.StringVar:
        tk.Label(parent, text=label, font=T.FONT_SMALL, bg=T.BG, fg=T.FG2).pack(anchor="w")
        var = tk.StringVar()
        tk.Entry(
            parent, textvariable=var, show=show,
            font=T.FONT_MAIN, bg=T.BG2, fg=T.FG,
            insertbackground=T.FG, relief="flat",
            bd=1, highlightthickness=1, highlightbackground=T.BORDER,
            highlightcolor=T.ACCENT,
        ).pack(fill="x", ipady=4, pady=(0, T.PAD))
        return var

    def _build(self):
        pad = T.PAD * 2

        container = tk.Frame(self, bg=T.BG)
        container.pack(fill="both", expand=True, padx=pad, pady=pad)

        self._title_var = self._labeled_entry(container, "タイトル *")
        self._url_var   = self._labeled_entry(container, "URL")
        self._user_var  = self._labeled_entry(container, "ユーザー名 / メール")

        # password row
        tk.Label(container, text="パスワード *", font=T.FONT_SMALL,
                 bg=T.BG, fg=T.FG2).pack(anchor="w")
        pw_row = tk.Frame(container, bg=T.BG)
        pw_row.pack(fill="x", pady=(0, 2))

        self._pw_var = tk.StringVar()
        self._pw_show = tk.BooleanVar(value=False)
        self._pw_entry = tk.Entry(
            pw_row, textvariable=self._pw_var, show="●",
            font=T.FONT_MONO, bg=T.BG2, fg=T.FG,
            insertbackground=T.FG, relief="flat",
            bd=1, highlightthickness=1, highlightbackground=T.BORDER,
            highlightcolor=T.ACCENT,
        )
        self._pw_entry.pack(side="left", fill="x", expand=True, ipady=4)
        self._pw_entry.bind("<KeyRelease>", lambda _: self._update_strength())

        tk.Button(pw_row, text="👁", font=T.FONT_SMALL,
                  bg=T.BG3, fg=T.FG, relief="flat", cursor="hand2", padx=4,
                  command=self._toggle_pw).pack(side="left", padx=2)
        tk.Button(pw_row, text="生成", font=T.FONT_SMALL,
                  bg=T.BG3, fg=T.FG, activebackground=T.ACCENT2, activeforeground=T.FG,
                  relief="flat", cursor="hand2", padx=6,
                  command=self._generate_pw).pack(side="left")

        # strength bar
        self._strength_var = tk.StringVar(value="")
        self._strength_lbl = tk.Label(container, textvariable=self._strength_var,
                                      font=T.FONT_SMALL, bg=T.BG, fg=T.FG2, anchor="w")
        self._strength_lbl.pack(fill="x", pady=(0, T.PAD))

        # category
        tk.Label(container, text="カテゴリ", font=T.FONT_SMALL,
                 bg=T.BG, fg=T.FG2).pack(anchor="w")
        self._cat_var = tk.StringVar(value="その他")
        cat_frame = tk.Frame(container, bg=T.BG)
        cat_frame.pack(fill="x", pady=(0, T.PAD))
        for cat in DEFAULT_CATEGORIES:
            tk.Radiobutton(
                cat_frame, text=cat, variable=self._cat_var, value=cat,
                font=T.FONT_SMALL, bg=T.BG, fg=T.FG,
                selectcolor=T.BG3, activebackground=T.BG,
                indicatoron=False, relief="flat", padx=6, pady=3,
                cursor="hand2",
            ).pack(side="left", padx=2)

        # tags
        self._tags_var = self._labeled_entry(container, "タグ (カンマ区切り)")

        # notes
        tk.Label(container, text="メモ", font=T.FONT_SMALL,
                 bg=T.BG, fg=T.FG2).pack(anchor="w")
        self._notes = tk.Text(
            container, height=3, font=T.FONT_MAIN,
            bg=T.BG2, fg=T.FG, insertbackground=T.FG,
            relief="flat", bd=1, wrap="word",
        )
        self._notes.pack(fill="x", pady=(0, T.PAD))

        # save / cancel
        btn_row = tk.Frame(container, bg=T.BG)
        btn_row.pack(fill="x", pady=(T.PAD, 0))
        tk.Button(btn_row, text="保存", font=T.FONT_BOLD,
                  bg=T.ACCENT, fg="white",
                  activebackground=T.ACCENT2, activeforeground="white",
                  relief="flat", cursor="hand2", padx=16, pady=6,
                  command=self._save).pack(side="right")
        tk.Button(btn_row, text="キャンセル", font=T.FONT_MAIN,
                  bg=T.BG3, fg=T.FG, relief="flat", cursor="hand2",
                  padx=12, pady=6,
                  command=self.destroy).pack(side="right", padx=(0, 6))

    def _populate(self, e: Entry):
        self._title_var.set(e.title)
        self._url_var.set(e.url)
        self._user_var.set(e.username)
        self._pw_var.set(e.password)
        self._cat_var.set(e.category)
        self._tags_var.set(", ".join(e.tags))
        self._notes.insert("1.0", e.notes)
        self._update_strength()

    def _toggle_pw(self):
        if self._pw_entry.cget("show") == "●":
            self._pw_entry.config(show="")
        else:
            self._pw_entry.config(show="●")

    def _generate_pw(self):
        pw = generate(length=20)
        self._pw_var.set(pw)
        self._pw_entry.config(show="")
        self._update_strength()

    def _update_strength(self):
        pw = self._pw_var.get()
        if not pw:
            self._strength_var.set("")
            return
        score, label = estimate_strength(pw)
        colors = {"強い": T.SUCCESS, "普通": T.WARNING, "弱い": T.DANGER, "非常に弱い": T.DANGER}
        color = colors.get(label, T.FG2)
        bar = "█" * (score // 10)
        self._strength_var.set(f"強度: {label}  {bar}")
        self._strength_lbl.config(fg=color)

    def _save(self):
        title = self._title_var.get().strip()
        pw = self._pw_var.get()
        if not title:
            messagebox.showerror("入力エラー", "タイトルは必須です。", parent=self)
            return
        if not pw:
            messagebox.showerror("入力エラー", "パスワードは必須です。", parent=self)
            return

        tags_raw = self._tags_var.get()
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        notes = self._notes.get("1.0", "end-1c")

        if self._entry:
            self._entry.title    = title
            self._entry.url      = self._url_var.get().strip()
            self._entry.username = self._user_var.get().strip()
            self._entry.password = pw
            self._entry.category = self._cat_var.get()
            self._entry.tags     = tags
            self._entry.notes    = notes
            result = self._entry
        else:
            result = Entry(
                title=title,
                url=self._url_var.get().strip(),
                username=self._user_var.get().strip(),
                password=pw,
                category=self._cat_var.get(),
                tags=tags,
                notes=notes,
            )

        if self._on_save:
            self._on_save(result)
        self.destroy()
