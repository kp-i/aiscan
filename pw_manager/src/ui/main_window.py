"""Main application window."""
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from pathlib import Path
import subprocess
import sys

from src.ui import theme as T
from src.ui.entry_dialog import EntryDialog
from src.vault import Vault, Entry


class MainWindow(tk.Frame):
    """Main window frame containing sidebar + detail panel."""

    def __init__(self, master: tk.Tk, vault: Vault, vault_path: Path):
        super().__init__(master, bg=T.BG)
        self.pack(fill="both", expand=True)
        self._vault = vault
        self._vault_path = vault_path
        self._selected: Entry | None = None

        master.title(f"VaultKey — {vault_path.name}")
        master.minsize(780, 500)

        self._build_menu(master)
        self._build_ui()
        self._refresh_list()

    # ── menu ──────────────────────────────────────────────────────

    def _build_menu(self, root: tk.Tk):
        menubar = tk.Menu(root, bg=T.BG2, fg=T.FG, activebackground=T.ACCENT,
                          activeforeground="white", relief="flat")
        root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0, bg=T.BG2, fg=T.FG,
                            activebackground=T.ACCENT, activeforeground="white")
        file_menu.add_command(label="Vaultをエクスポート", command=self._export)
        file_menu.add_command(label="Vaultをインポート / 別のVaultを開く",
                              command=self._import)
        file_menu.add_separator()
        file_menu.add_command(label="マスターパスワードを変更",
                              command=self._change_password)
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=root.destroy)
        menubar.add_cascade(label="ファイル", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0, bg=T.BG2, fg=T.FG,
                            activebackground=T.ACCENT, activeforeground="white")
        help_menu.add_command(label="VaultKeyについて", command=self._about)
        menubar.add_cascade(label="ヘルプ", menu=help_menu)

    # ── layout ────────────────────────────────────────────────────

    def _build_ui(self):
        # toolbar
        toolbar = tk.Frame(self, bg=T.BG2, pady=6)
        toolbar.pack(fill="x", side="top")

        tk.Button(toolbar, text="＋ 追加", font=T.FONT_BOLD,
                  bg=T.ACCENT, fg="white",
                  activebackground=T.ACCENT2, activeforeground="white",
                  relief="flat", cursor="hand2", padx=12, pady=4,
                  command=self._add_entry).pack(side="left", padx=(T.PAD, 4))

        # search
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._refresh_list())
        tk.Entry(
            toolbar, textvariable=self._search_var,
            font=T.FONT_MAIN, bg=T.BG3, fg=T.FG,
            insertbackground=T.FG, relief="flat",
            bd=1, highlightthickness=1, highlightbackground=T.BORDER,
            highlightcolor=T.ACCENT, width=28,
        ).pack(side="left", ipady=4, padx=4)

        # category filter
        self._cat_var = tk.StringVar(value="すべて")
        self._cat_var.trace_add("write", lambda *_: self._refresh_list())
        self._cat_menu = tk.OptionMenu(toolbar, self._cat_var, "すべて")
        self._cat_menu.config(
            font=T.FONT_SMALL, bg=T.BG3, fg=T.FG,
            activebackground=T.ACCENT2, activeforeground="white",
            relief="flat", cursor="hand2", bd=0,
            highlightthickness=0,
        )
        self._cat_menu["menu"].config(bg=T.BG2, fg=T.FG,
                                      activebackground=T.ACCENT,
                                      activeforeground="white")
        self._cat_menu.pack(side="left", padx=4)

        # count label (right)
        self._count_var = tk.StringVar(value="0 件")
        tk.Label(toolbar, textvariable=self._count_var,
                 font=T.FONT_SMALL, bg=T.BG2, fg=T.FG2).pack(side="right", padx=T.PAD)

        # paned split: list | detail
        pane = tk.PanedWindow(self, orient="horizontal",
                              bg=T.BORDER, sashwidth=3,
                              sashrelief="flat")
        pane.pack(fill="both", expand=True)

        # ── left: entry list ──────────────────────────────────────
        left = tk.Frame(pane, bg=T.BG, width=280)
        pane.add(left, minsize=220)

        self._listbox = tk.Listbox(
            left, font=T.FONT_MAIN,
            bg=T.BG, fg=T.FG, selectbackground=T.ACCENT,
            selectforeground="white", activestyle="none",
            relief="flat", bd=0, highlightthickness=0,
        )
        self._listbox.pack(fill="both", expand=True, side="left")
        self._listbox.bind("<<ListboxSelect>>", self._on_select)
        self._listbox.bind("<Double-Button-1>", lambda _: self._edit_entry())
        self._listbox.bind("<Delete>", lambda _: self._delete_entry())

        sb = tk.Scrollbar(left, orient="vertical", command=self._listbox.yview,
                          bg=T.BG3, troughcolor=T.BG, relief="flat", bd=0)
        sb.pack(fill="y", side="right")
        self._listbox.config(yscrollcommand=sb.set)

        # ── right: detail panel ───────────────────────────────────
        right = tk.Frame(pane, bg=T.BG2)
        pane.add(right, minsize=320)

        self._detail = DetailPanel(right, on_edit=self._edit_entry,
                                   on_delete=self._delete_entry)
        self._detail.pack(fill="both", expand=True)

        self._entries_shown: list[Entry] = []

    # ── list management ───────────────────────────────────────────

    def _refresh_list(self):
        query = self._search_var.get()
        cat = self._cat_var.get()
        results = self._vault.search(query, category=cat)

        # update category dropdown
        cats = ["すべて"] + self._vault.categories()
        menu = self._cat_menu["menu"]
        menu.delete(0, "end")
        for c in cats:
            menu.add_command(label=c,
                             command=lambda v=c: self._cat_var.set(v))

        self._entries_shown = results
        self._listbox.delete(0, "end")
        for e in results:
            icon = _category_icon(e.category)
            self._listbox.insert("end", f"  {icon}  {e.title}")
        self._count_var.set(f"{len(results)} 件")

        # re-select previously selected item if still present
        if self._selected:
            for i, e in enumerate(results):
                if e.id == self._selected.id:
                    self._listbox.selection_set(i)
                    self._listbox.see(i)
                    self._detail.show(e)
                    return
        self._detail.clear()

    def _on_select(self, _event=None):
        sel = self._listbox.curselection()
        if not sel:
            return
        entry = self._entries_shown[sel[0]]
        self._selected = entry
        self._detail.show(entry)

    # ── CRUD ─────────────────────────────────────────────────────

    def _add_entry(self):
        def save(entry: Entry):
            self._vault.add(entry)
            self._selected = entry
            self._refresh_list()
        EntryDialog(self, on_save=save)

    def _edit_entry(self):
        if not self._selected:
            return
        entry = self._vault.get(self._selected.id)
        if not entry:
            return
        def save(updated: Entry):
            self._vault.update(updated)
            self._selected = updated
            self._refresh_list()
        EntryDialog(self, entry=entry, on_save=save)

    def _delete_entry(self):
        if not self._selected:
            return
        ok = messagebox.askyesno(
            "削除確認",
            f"「{self._selected.title}」を削除しますか？\nこの操作は元に戻せません。",
            parent=self,
        )
        if ok:
            self._vault.delete(self._selected.id)
            self._selected = None
            self._refresh_list()

    # ── file operations ──────────────────────────────────────────

    def _export(self):
        path = filedialog.asksaveasfilename(
            title="Vaultをエクスポート",
            defaultextension=".vkey",
            filetypes=[("VaultKey files", "*.vkey")],
        )
        if not path:
            return
        pw = simpledialog.askstring(
            "エクスポートパスワード",
            "エクスポートファイルのパスワード\n(空白: 現在のパスワードを使用)",
            show="●", parent=self,
        )
        try:
            self._vault.export_to(Path(path), pw if pw else None)
            messagebox.showinfo("完了", f"エクスポートしました:\n{path}", parent=self)
        except Exception as e:
            messagebox.showerror("エラー", str(e), parent=self)

    def _import(self):
        messagebox.showinfo(
            "ヒント",
            "別のVaultファイルを開くには、アプリを再起動して\n"
            "ログイン画面でファイルを指定してください。",
            parent=self,
        )

    def _change_password(self):
        from src.ui.change_pw import ChangePwDialog
        ChangePwDialog(self, self._vault)

    def _about(self):
        messagebox.showinfo(
            "VaultKeyについて",
            "VaultKey v1.0\n\n"
            "AES-256-GCM 暗号化によるローカルパスワードマネージャー\n"
            "PBKDF2-HMAC-SHA256 (600,000回) でキー導出\n\n"
            "データはすべてローカルに保存されます。",
            parent=self,
        )


class DetailPanel(tk.Frame):
    """Right-hand detail / preview panel."""

    def __init__(self, master, on_edit=None, on_delete=None):
        super().__init__(master, bg=T.BG2)
        self._on_edit = on_edit
        self._on_delete = on_delete
        self._pw_visible = False
        self._current: Entry | None = None
        self._build()

    def _build(self):
        self._placeholder = tk.Label(
            self, text="エントリを選択してください",
            font=T.FONT_MAIN, bg=T.BG2, fg=T.FG2,
        )
        self._placeholder.pack(expand=True)

        self._content = tk.Frame(self, bg=T.BG2)

        pad = T.PAD * 2

        # header
        header = tk.Frame(self._content, bg=T.BG2)
        header.pack(fill="x", padx=pad, pady=(pad, T.PAD))
        self._title_lbl = tk.Label(header, text="", font=T.FONT_TITLE,
                                   bg=T.BG2, fg=T.FG, anchor="w")
        self._title_lbl.pack(side="left", fill="x", expand=True)

        btn_frame = tk.Frame(header, bg=T.BG2)
        btn_frame.pack(side="right")
        tk.Button(btn_frame, text="編集", font=T.FONT_SMALL,
                  bg=T.ACCENT, fg="white",
                  activebackground=T.ACCENT2, activeforeground="white",
                  relief="flat", cursor="hand2", padx=10, pady=3,
                  command=lambda: self._on_edit and self._on_edit(),
                  ).pack(side="left", padx=(0, 4))
        tk.Button(btn_frame, text="削除", font=T.FONT_SMALL,
                  bg=T.DANGER, fg="white",
                  activebackground="#cc4466", activeforeground="white",
                  relief="flat", cursor="hand2", padx=10, pady=3,
                  command=lambda: self._on_delete and self._on_delete(),
                  ).pack(side="left")

        sep = tk.Frame(self._content, bg=T.BORDER, height=1)
        sep.pack(fill="x", padx=pad, pady=T.PAD)

        form = tk.Frame(self._content, bg=T.BG2)
        form.pack(fill="x", padx=pad)

        self._url_var  = tk.StringVar()
        self._user_var = tk.StringVar()
        self._pw_var   = tk.StringVar()
        self._cat_var  = tk.StringVar()
        self._tags_var = tk.StringVar()

        self._url_lbl  = self._row(form, "URL",          self._url_var,  copyable=True)
        self._user_lbl = self._row(form, "ユーザー名",   self._user_var, copyable=True)

        # password row (special: toggle + copy)
        r = tk.Frame(form, bg=T.BG2)
        r.pack(fill="x", pady=2)
        tk.Label(r, text="パスワード", font=T.FONT_SMALL, bg=T.BG2,
                 fg=T.FG2, width=12, anchor="w").pack(side="left")
        self._pw_disp_var = tk.StringVar(value="●●●●●●●●")
        tk.Label(r, textvariable=self._pw_disp_var,
                 font=T.FONT_MONO, bg=T.BG2, fg=T.FG, anchor="w").pack(side="left")
        tk.Button(r, text="👁", font=T.FONT_SMALL,
                  bg=T.BG3, fg=T.FG, relief="flat", cursor="hand2", padx=3,
                  command=self._toggle_pw).pack(side="left", padx=4)
        tk.Button(r, text="コピー", font=T.FONT_SMALL,
                  bg=T.BG3, fg=T.FG, relief="flat", cursor="hand2", padx=6,
                  command=self._copy_pw).pack(side="left")

        self._row(form, "カテゴリ", self._cat_var)
        self._row(form, "タグ",     self._tags_var)

        sep2 = tk.Frame(self._content, bg=T.BORDER, height=1)
        sep2.pack(fill="x", padx=pad, pady=T.PAD)

        tk.Label(self._content, text="メモ", font=T.FONT_SMALL,
                 bg=T.BG2, fg=T.FG2).pack(anchor="w", padx=pad)
        self._notes_text = tk.Text(
            self._content, height=5, font=T.FONT_MAIN,
            bg=T.BG3, fg=T.FG, insertbackground=T.FG,
            relief="flat", bd=0, state="disabled", wrap="word",
        )
        self._notes_text.pack(fill="x", padx=pad, pady=(2, T.PAD))

        tk.Label(self._content, text="", font=T.FONT_SMALL,
                 bg=T.BG2, fg=T.FG2).pack(anchor="w", padx=pad)
        self._meta_var = tk.StringVar()
        tk.Label(self._content, textvariable=self._meta_var,
                 font=T.FONT_SMALL, bg=T.BG2, fg=T.FG2, anchor="w").pack(
                     fill="x", padx=pad, pady=(0, pad))

    def _row(self, parent, label: str, var: tk.StringVar, copyable=False) -> tk.Label:
        r = tk.Frame(parent, bg=T.BG2)
        r.pack(fill="x", pady=2)
        tk.Label(r, text=label, font=T.FONT_SMALL, bg=T.BG2,
                 fg=T.FG2, width=12, anchor="w").pack(side="left")
        lbl = tk.Label(r, textvariable=var, font=T.FONT_MAIN,
                       bg=T.BG2, fg=T.FG, anchor="w")
        lbl.pack(side="left", fill="x", expand=True)
        if copyable:
            tk.Button(r, text="コピー", font=T.FONT_SMALL,
                      bg=T.BG3, fg=T.FG, relief="flat", cursor="hand2", padx=6,
                      command=lambda v=var: self._copy(v.get())).pack(side="right")
        return lbl

    def show(self, entry: Entry):
        self._current = entry
        self._pw_visible = False
        self._placeholder.pack_forget()
        self._content.pack(fill="both", expand=True)

        self._title_lbl.config(text=entry.title)
        self._url_var.set(entry.url or "—")
        self._user_var.set(entry.username or "—")
        self._pw_var.set(entry.password)
        self._pw_disp_var.set("●" * min(len(entry.password), 16))
        self._cat_var.set(entry.category)
        self._tags_var.set(", ".join(entry.tags) if entry.tags else "—")

        self._notes_text.config(state="normal")
        self._notes_text.delete("1.0", "end")
        self._notes_text.insert("1.0", entry.notes or "")
        self._notes_text.config(state="disabled")

        self._meta_var.set(
            f"作成: {entry.created_at}   更新: {entry.updated_at}"
        )

    def clear(self):
        self._current = None
        self._content.pack_forget()
        self._placeholder.pack(expand=True)

    def _toggle_pw(self):
        if not self._current:
            return
        self._pw_visible = not self._pw_visible
        if self._pw_visible:
            self._pw_disp_var.set(self._current.password)
        else:
            self._pw_disp_var.set("●" * min(len(self._current.password), 16))

    def _copy_pw(self):
        if self._current:
            self._copy(self._current.password)

    def _copy(self, text: str):
        self.clipboard_clear()
        self.clipboard_append(text)


def _category_icon(cat: str) -> str:
    icons = {
        "仕事":       "💼",
        "プライベート": "🏠",
        "開発":       "💻",
        "金融":       "💳",
        "SNS":        "📱",
        "ショッピング": "🛒",
        "その他":     "📁",
    }
    return icons.get(cat, "📁")
