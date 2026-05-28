import json
import os
import base64
import gc
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

DATA_FILE = "my_passwords.json"

# ── 字体与颜色系统 (macOS 浅色风格) ──────────────────────────────
APP_FONT = "Microsoft YaHei"  # 全局统一无衬线字体，消除中英文割裂感

COLORS = {
    "bg_deep":        "#F5F5F7",   # 苹果经典浅灰底色
    "bg_sidebar":     "#EAEBEE",   # 侧边栏微深灰
    "bg_card":        "#FFFFFF",   # 卡片纯白背景
    "bg_card_hover":  "#F2F2F7",   # 卡片悬停浅灰
    "bg_card_sel":    "#E6F0FF",   # 选中时的浅蓝色背景
    "bg_input":       "#FFFFFF",   # 输入框纯白
    "bg_btn_sec":     "#E5E5EA",   # 次级按钮底色

    "accent":         "#007AFF",   # 苹果蓝
    "accent_dark":    "#0056B3",
    "accent2":        "#AF52DE",   # 苹果紫
    "success":        "#34C759",   # 苹果绿
    "warning":        "#FF9500",   # 苹果橙
    "danger":         "#FF3B30",   # 苹果红

    "text_primary":   "#1D1D1F",   # 主文本极深灰
    "text_secondary": "#86868B",   # 次级文本浅灰
    "text_muted":     "#A1A1A6",   # 暗纹提示灰

    "border":         "#D1D1D6",   # 浅色边框线
    "border_accent":  "#80BDFF",   # 蓝色强调边框
}

# ── 加密核心 ─────────────────────────────────────────────────
class CryptoCore:
    def __init__(self):
        self.key = None
        self.fernet = None

    def get_key_from_pwd(self, pwd: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000)
        return base64.urlsafe_b64encode(kdf.derive(pwd.encode()))

    def set_key(self, key: bytes):
        self.key = key
        self.fernet = Fernet(self.key)

    def derive_and_set_key(self, master_password: str, salt: bytes):
        self.set_key(self.get_key_from_pwd(master_password, salt))

    def encrypt(self, text: str) -> str:
        return self.fernet.encrypt(text.encode()).decode()

    def decrypt(self, encrypted_text: str) -> str:
        return self.fernet.decrypt(encrypted_text.encode()).decode()


# ── 自定义基础组件 ──────────────────────────────────────────────
class GlassFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", COLORS["bg_card"])
        kwargs.setdefault("border_color", COLORS["border"])
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("corner_radius", 14)
        super().__init__(master, **kwargs)

class GradientButton(ctk.CTkButton):
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", COLORS["accent"])
        kwargs.setdefault("hover_color", COLORS["accent_dark"])
        kwargs.setdefault("corner_radius", 10)
        kwargs.setdefault("font", ctk.CTkFont(family=APP_FONT, size=13, weight="bold"))
        kwargs.setdefault("text_color", "#ffffff")
        super().__init__(master, **kwargs)

class SecondaryButton(ctk.CTkButton):
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", COLORS["bg_btn_sec"])
        kwargs.setdefault("hover_color", COLORS["bg_card_hover"])
        kwargs.setdefault("border_color", COLORS["border_accent"])
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("corner_radius", 10)
        kwargs.setdefault("font", ctk.CTkFont(family=APP_FONT, size=12))
        kwargs.setdefault("text_color", COLORS["text_secondary"])
        super().__init__(master, **kwargs)

class IconButton(ctk.CTkButton):
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", COLORS["bg_btn_sec"])
        kwargs.setdefault("hover_color", COLORS["bg_card_hover"])
        kwargs.setdefault("corner_radius", 8)
        kwargs.setdefault("width", 32)
        kwargs.setdefault("height", 32)
        kwargs.setdefault("font", ctk.CTkFont(family=APP_FONT, size=13))
        kwargs.setdefault("text_color", COLORS["text_secondary"])
        super().__init__(master, **kwargs)

class StyledEntry(ctk.CTkEntry):
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", COLORS["bg_input"])
        kwargs.setdefault("border_color", COLORS["border"])
        kwargs.setdefault("text_color", COLORS["text_primary"])
        kwargs.setdefault("placeholder_text_color", COLORS["text_muted"])
        kwargs.setdefault("corner_radius", 10)
        kwargs.setdefault("font", ctk.CTkFont(family=APP_FONT, size=13))
        super().__init__(master, **kwargs)


# ── 账号行卡片 ────────────────────────────────────────────────
LOGO_COLORS = {
    "Google": ("#FF3B30", "#FFEBEA"), "GitHub": ("#86868B", "#F2F2F7"),
    "Twitter": ("#007AFF", "#E6F0FF"), "Amazon": ("#FF9500", "#FFF4E6"),
    "Netflix": ("#FF3B30", "#FFEBEA"), "Steam": ("#0056B3", "#E6F0FF"),
}

def logo_colors(title: str):
    for key, (fg, bg) in LOGO_COLORS.items():
        if key.lower() in title.lower(): return fg, bg
    return COLORS["accent2"], COLORS["bg_btn_sec"]

class AccountRow(ctk.CTkFrame):
    def __init__(self, master, acc_data: dict, idx: int, on_select, on_view, on_edit, on_delete, **kwargs):
        super().__init__(master, fg_color=COLORS["bg_card"], border_color=COLORS["border"], border_width=1, corner_radius=12, **kwargs)
        self.idx = idx
        self.acc = acc_data
        self.selected = False

        fg, bg = logo_colors(acc_data["title"])
        logo_frame = ctk.CTkFrame(self, width=42, height=42, fg_color=bg, corner_radius=10)
        logo_frame.pack(side="left", padx=(14, 10), pady=10)
        logo_frame.pack_propagate(False)
        initials = acc_data["title"][0].upper()
        ctk.CTkLabel(logo_frame, text=initials, font=ctk.CTkFont(family=APP_FONT, size=16, weight="bold"), text_color=fg).place(relx=0.5, rely=0.5, anchor="center")

        info = ctk.CTkFrame(self, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, pady=8)
        
        title_row = ctk.CTkFrame(info, fg_color="transparent")
        title_row.pack(fill="x", anchor="w")
        ctk.CTkLabel(title_row, text=acc_data["title"], font=ctk.CTkFont(family=APP_FONT, size=13, weight="bold"), text_color=COLORS["text_primary"], anchor="w").pack(side="left")
        
        cat_text = acc_data.get("category", "默认")
        cat_lbl = ctk.CTkLabel(title_row, text=cat_text, font=ctk.CTkFont(family=APP_FONT, size=10), text_color=COLORS["accent2"], fg_color=COLORS["bg_sidebar"], corner_radius=4, height=16, width=40)
        cat_lbl.pack(side="left", padx=8)

        ctk.CTkLabel(info, text=acc_data["username"], font=ctk.CTkFont(family=APP_FONT, size=11), text_color=COLORS["text_secondary"], anchor="w").pack(fill="x")
        ctk.CTkLabel(self, text="●●●●●●●●", font=ctk.CTkFont(family="Consolas", size=9), text_color=COLORS["text_muted"]).pack(side="left", padx=10)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side="right", padx=10, pady=8)
        IconButton(btn_frame, text="👁", command=lambda: on_view(idx)).pack(side="left", padx=2)
        IconButton(btn_frame, text="✏", command=lambda: on_edit(idx)).pack(side="left", padx=2)
        IconButton(btn_frame, text="✕", fg_color=COLORS["bg_btn_sec"], hover_color="#FFEBEA", text_color=COLORS["danger"], command=lambda: on_delete(idx)).pack(side="left", padx=2)

        def bind_row_clicks(widget):
            widget.bind("<Button-1>", lambda e, i=idx: on_select(i))
            try: widget.configure(cursor="hand2")
            except Exception: pass
            for child in widget.winfo_children():
                if child != btn_frame: bind_row_clicks(child)
                    
        bind_row_clicks(self)

    def set_selected(self, selected: bool):
        self.selected = selected
        self.configure(fg_color=COLORS["bg_card_sel"] if selected else COLORS["bg_card"],
                       border_color=COLORS["border_accent"] if selected else COLORS["border"])

class NavItem(ctk.CTkFrame):
    def __init__(self, master, icon: str, label: str, active=False, badge=None, command=None, **kwargs):
        super().__init__(master, fg_color="transparent", corner_radius=10, **kwargs)
        self._command = command
        self.inner = ctk.CTkFrame(self, fg_color=COLORS["bg_card"] if active else "transparent", corner_radius=10)
        self.inner.pack(fill="x", padx=4, pady=1)

        row = ctk.CTkFrame(self.inner, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=7)

        ctk.CTkLabel(row, text=icon, font=ctk.CTkFont(family=APP_FONT, size=15), text_color=COLORS["accent"] if active else COLORS["text_secondary"], width=22).pack(side="left")
        ctk.CTkLabel(row, text=label, font=ctk.CTkFont(family=APP_FONT, size=13, weight="bold" if active else "normal"), text_color=COLORS["text_primary"] if active else COLORS["text_secondary"], anchor="w").pack(side="left", padx=6, fill="x", expand=True)

        if badge is not None:
            self.badge_lbl = ctk.CTkLabel(row, text=str(badge), fg_color=COLORS["bg_deep"], text_color=COLORS["accent"], corner_radius=8, font=ctk.CTkFont(family=APP_FONT, size=10), width=28, height=18)
            self.badge_lbl.pack(side="right")

        def bind_all_clicks(widget):
            widget.bind("<Button-1>", self._click)
            try: widget.configure(cursor="hand2") 
            except Exception: pass
            for child in widget.winfo_children(): bind_all_clicks(child)
                
        bind_all_clicks(self.inner)

    def _click(self, event=None):
        if self._command: self._command()


# ── 专属密码输入模态弹窗 ──────────────
class CustomPasswordDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, prompt):
        super().__init__(parent)
        self.title(title)
        self.geometry("380x220")
        self.configure(fg_color=COLORS["bg_deep"])
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.result = None

        card = GlassFrame(self)
        card.pack(fill="both", expand=True, padx=16, pady=16)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(inner, text=prompt, font=ctk.CTkFont(family=APP_FONT, size=13, weight="bold"), text_color=COLORS["text_primary"], anchor="w").pack(fill="x", pady=(0, 12))
        
        self.entry = StyledEntry(inner, width=300, height=38, show="●")
        self.entry.pack(fill="x", pady=(0, 16))
        self.entry.focus()

        def confirm():
            self.result = self.entry.get().strip()
            self.destroy()

        def cancel():
            self.destroy()

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x")
        SecondaryButton(btn_row, text="取消", width=80, command=cancel).pack(side="right", padx=(8, 0))
        GradientButton(btn_row, text="确认", width=80, command=confirm).pack(side="right")

        self.bind("<Return>", lambda e: confirm())
        self.bind("<Escape>", lambda e: cancel())
        self.wait_window()


# ── 独立登录窗口 ──────────────────────────────────────────
class LoginWindow(ctk.CTkToplevel):
    def __init__(self, app_instance):
        super().__init__()
        self.app = app_instance
        self.title("安全验证")
        self.geometry("420x520")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_deep"])
        
        self.transient(self.app)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.app.quit)

        outer = ctk.CTkFrame(self, fg_color=COLORS["bg_deep"])
        outer.place(relx=0.5, rely=0.5, anchor="center", relwidth=1.0, relheight=1.0)

        card = GlassFrame(outer, width=340, height=400)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.85, relheight=0.9)

        logo_bg = ctk.CTkFrame(inner, width=64, height=64, fg_color=COLORS["bg_input"], border_color=COLORS["accent"], border_width=1, corner_radius=18)
        logo_bg.pack(pady=(10, 0))
        logo_bg.pack_propagate(False)
        ctk.CTkLabel(logo_bg, text="🛡", font=ctk.CTkFont(family=APP_FONT, size=28)).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(inner, text="密码金库", font=ctk.CTkFont(family=APP_FONT, size=22, weight="bold"), text_color=COLORS["text_primary"]).pack(pady=(12, 2))

        self.is_first = not self.app._load_db()
        hint = "首次使用，请设置主密码" if self.is_first else "输入主密码以解锁金库"
        ctk.CTkLabel(inner, text=hint, font=ctk.CTkFont(family=APP_FONT, size=12), text_color=COLORS["text_muted"]).pack(pady=(0, 18))

        self.pwd_entry = StyledEntry(inner, width=240, height=42, show="●", placeholder_text="主密码")
        self.pwd_entry.pack(pady=(0, 16))
        self.pwd_entry.focus()
        
        self.bind("<Return>", lambda e: self._attempt_login())

        btn_text = "  初始化金库  " if self.is_first else "  解锁金库  "
        GradientButton(inner, text=btn_text, height=42, width=240, command=self._attempt_login).pack()

        if not self.is_first and self.app.db.get("recovery_payload"):
            ctk.CTkButton(inner, text="忘记密码？使用恢复码重置", fg_color="transparent", hover_color=COLORS["bg_card"], text_color=COLORS["text_muted"], font=ctk.CTkFont(family=APP_FONT, size=11), command=self._recover).pack(pady=(12, 0))

    def _attempt_login(self):
        master_pwd = self.pwd_entry.get()
        if not master_pwd:
            messagebox.showwarning("提示", "密码不能为空！")
            return

        if self.is_first:
            dialog = CustomPasswordDialog(self, "二次确认", "请再次输入主密码以防手误：")
            confirm_pwd = dialog.result
            
            if master_pwd != confirm_pwd:
                messagebox.showerror("错误", "两次输入的密码不一致，请重新输入！")
                self.pwd_entry.delete(0, "end")
                master_pwd = confirm_pwd = None
                del master_pwd, confirm_pwd
                gc.collect()
                return

            salt = os.urandom(16)
            self.app.db["salt"] = base64.b64encode(salt).decode()
            self.app.crypto.derive_and_set_key(master_pwd, salt)
            self.app.db["verify_token"] = self.app.crypto.encrypt("AUTH_SUCCESS")
            self.app.db["categories"] = ["默认", "社交", "金融", "开发"]

            recovery_key = "RM-" + os.urandom(6).hex().upper()
            recovery_salt = os.urandom(16)
            self.app.db["recovery_salt"] = base64.b64encode(recovery_salt).decode()
            rec_enc_key = self.app.crypto.get_key_from_pwd(recovery_key, recovery_salt)
            f_rec = Fernet(rec_enc_key)
            self.app.db["recovery_payload"] = f_rec.encrypt(self.app.crypto.key).decode()
            self.app._save_db()

            try:
                with open("安全恢复码备份.txt", "w", encoding="utf-8") as f:
                    f.write(f"你的安全恢复码是：{recovery_key}\n请妥善保管，切勿泄露给他人。")
                extra_msg = f"\n\n恢复码已同步保存在同目录下【安全恢复码备份.txt】中！"
            except Exception: extra_msg = ""

            msg = f"初始化成功！\n\n【重要】你的安全恢复码是：\n{recovery_key}\n\n这是忘记主密码时的唯一找回凭证，请妥善保存！{extra_msg}"
            messagebox.showwarning("⚠️ 请立刻备份恢复码", msg)
            
            master_pwd = confirm_pwd = None
            del master_pwd, confirm_pwd
            gc.collect()
            self._unlock_success()
        else:
            salt = base64.b64decode(self.app.db.get("salt", ""))
            self.app.crypto.derive_and_set_key(master_pwd, salt)
            try:
                if self.app.crypto.decrypt(self.app.db.get("verify_token", "")) == "AUTH_SUCCESS":
                    master_pwd = None
                    del master_pwd
                    gc.collect()
                    self._unlock_success()
                else:
                    raise InvalidToken
            except Exception:
                messagebox.showerror("错误", "密码错误，拒绝访问！")
                self.pwd_entry.delete(0, "end")
                master_pwd = None
                del master_pwd
                gc.collect()

    def _unlock_success(self):
        self.grab_release()
        self.destroy()
        self.app.unlock_app()

    def _recover(self):
        self.app._recover_password(self)


# ── 主应用窗口 ────────────────────────────────────────────────
class PasswordManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light") # macOS 浅色模式
        ctk.set_default_color_theme("blue")

        self.title("密码金库  ·  SafeVault Pro")
        self.geometry("960x640")
        self.minsize(800, 520)
        self.configure(fg_color=COLORS["bg_deep"])

        self.crypto = CryptoCore()
        self.db = {"salt": "", "verify_token": "", "recovery_salt": "", "recovery_payload": "", "categories": ["默认"], "accounts": []}
        self._rows = []
        self.current_filter_category = "全部"

        self.withdraw()
        LoginWindow(self)

    def unlock_app(self):
        """解锁成功回调"""
        for w in self.winfo_children(): w.destroy()
        
        root_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_deep"])
        root_frame.pack(fill="both", expand=True)

        # ── 左侧边栏
        self.sidebar = ctk.CTkFrame(root_frame, width=210, fg_color=COLORS["bg_sidebar"], corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=14, pady=(20, 12))
        logo_bg = ctk.CTkFrame(brand, width=38, height=38, fg_color=COLORS["bg_input"], border_color=COLORS["accent"], border_width=1, corner_radius=10)
        logo_bg.pack(side="left")
        logo_bg.pack_propagate(False)
        ctk.CTkLabel(logo_bg, text="🛡", font=ctk.CTkFont(family=APP_FONT, size=18)).place(relx=0.5, rely=0.5, anchor="center")

        brand_text = ctk.CTkFrame(brand, fg_color="transparent")
        brand_text.pack(side="left", padx=8)
        ctk.CTkLabel(brand_text, text="密码金库", font=ctk.CTkFont(family=APP_FONT, size=14, weight="bold"), text_color=COLORS["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(brand_text, text="SafeVault Pro", font=ctk.CTkFont(family=APP_FONT, size=10), text_color=COLORS["text_muted"]).pack(anchor="w")

        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=14, pady=(0, 10))

        self.menu_scroll = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent", scrollbar_button_color=COLORS["border"])
        self.menu_scroll.pack(fill="both", expand=True, padx=4, pady=4)

        self._render_sidebar_menu()

        # ── 右侧内容区
        content = ctk.CTkFrame(root_frame, fg_color=COLORS["bg_deep"], corner_radius=0)
        content.pack(side="left", fill="both", expand=True)

        self.topbar = ctk.CTkFrame(content, fg_color="transparent", height=64)
        self.topbar.pack(fill="x", padx=24, pady=(20, 0))
        self.topbar.pack_propagate(False)
        
        self.title_lbl = ctk.CTkLabel(self.topbar, text="全部账号", font=ctk.CTkFont(family=APP_FONT, size=20, weight="bold"), text_color=COLORS["text_primary"])
        self.title_lbl.pack(side="left", anchor="center")

        search_frame = ctk.CTkFrame(self.topbar, fg_color=COLORS["bg_card"], border_color=COLORS["border"], border_width=1, corner_radius=10, height=38)
        search_frame.pack(side="left", padx=20, anchor="center")
        search_frame.pack_propagate(False)
        ctk.CTkLabel(search_frame, text="🔍", font=ctk.CTkFont(family=APP_FONT, size=13), text_color=COLORS["text_muted"]).pack(side="left", padx=(10, 4))
        
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", self._on_search)
        ctk.CTkEntry(search_frame, textvariable=self.search_var, width=180, height=36, fg_color="transparent", border_width=0, text_color=COLORS["text_primary"], placeholder_text="搜索平台或账号…", placeholder_text_color=COLORS["text_muted"], font=ctk.CTkFont(family=APP_FONT, size=13)).pack(side="left")

        GradientButton(self.topbar, text="＋  添加账号", height=38, width=130, command=self._add_account).pack(side="right", anchor="center")

        filter_bar = ctk.CTkFrame(content, fg_color="transparent")
        filter_bar.pack(fill="x", padx=24, pady=(24, 8))
        ctk.CTkLabel(filter_bar, text="账号列表", font=ctk.CTkFont(family=APP_FONT, size=14, weight="bold"), text_color=COLORS["text_secondary"]).pack(side="left")

        self.list_scroll = ctk.CTkScrollableFrame(content, fg_color="transparent", scrollbar_button_color=COLORS["border"], scrollbar_button_hover_color=COLORS["border_accent"])
        self.list_scroll.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        self._refresh_list()
        self.deiconify()

    def _render_sidebar_menu(self):
        for w in self.menu_scroll.winfo_children(): w.destroy()
        ctk.CTkLabel(self.menu_scroll, text="主菜单", font=ctk.CTkFont(family=APP_FONT, size=10), text_color=COLORS["text_muted"], anchor="w").pack(fill="x", padx=14, pady=(4, 2))
        
        is_all_active = (self.current_filter_category == "全部")
        self.all_acc_nav = NavItem(self.menu_scroll, "  ⊞", "全部账号", active=is_all_active, badge=len(self.db["accounts"]), command=lambda: self._filter_by_category("全部"))
        self.all_acc_nav.pack(fill="x")

        NavItem(self.menu_scroll, "  🔒", "锁定金库", command=self._lock).pack(fill="x")

        ctk.CTkLabel(self.menu_scroll, text="自定义分类", font=ctk.CTkFont(family=APP_FONT, size=10), text_color=COLORS["text_muted"], anchor="w").pack(fill="x", padx=14, pady=(16, 2))
        if "categories" not in self.db: self.db["categories"] = ["默认", "社交", "金融", "开发"]

        for cat in self.db["categories"]:
            cat_count = sum(1 for a in self.db["accounts"] if a.get("category", "默认") == cat)
            is_active = (self.current_filter_category == cat)
            NavItem(self.menu_scroll, "  📁", cat, active=is_active, badge=cat_count, command=lambda c=cat: self._filter_by_category(c)).pack(fill="x")

        ctk.CTkFrame(self.menu_scroll, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=10, pady=10)
        SecondaryButton(self.menu_scroll, text="＋ 新增分类类别", height=32, font=ctk.CTkFont(family=APP_FONT, size=11), command=self._add_new_category).pack(fill="x", padx=4)

    def _add_new_category(self):
        new_cat = simpledialog.askstring("新增类别", "请输入新分类的名称：", parent=self)
        if not new_cat or not new_cat.strip(): return
        new_cat = new_cat.strip()
        if new_cat in self.db["categories"]:
            messagebox.showwarning("提示", "该分类类别已存在！")
            return
        self.db["categories"].append(new_cat)
        self._save_db()
        self._render_sidebar_menu()

    def _filter_by_category(self, category_name):
        self.current_filter_category = category_name
        self.title_lbl.configure(text=f"{category_name} 账号")
        self._render_sidebar_menu()
        self._refresh_list()

    def _lock(self):
        self.withdraw()
        self.crypto = CryptoCore()
        gc.collect()
        LoginWindow(self)

    def _view_password_dialog(self, idx):
        acc = self.db["accounts"][idx]
        try: pwd = self.crypto.decrypt(acc["password"])
        except Exception: messagebox.showerror("错误", "解密失败！"); return

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"查看凭证 — {acc['title']}")
        dialog.geometry("380x260")
        dialog.configure(fg_color=COLORS["bg_deep"])
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)

        card = GlassFrame(dialog)
        card.pack(fill="both", expand=True, padx=14, pady=14)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        fg, _ = logo_colors(acc["title"])
        head = ctk.CTkFrame(inner, fg_color="transparent")
        head.pack(fill="x", pady=(0, 16))

        logo_icon_bg = ctk.CTkFrame(head, width=44, height=44, fg_color=COLORS["bg_input"], border_color=fg, border_width=1, corner_radius=12)
        logo_icon_bg.pack(side="left")
        logo_icon_bg.pack_propagate(False)
        ctk.CTkLabel(logo_icon_bg, text=acc["title"][0].upper(), font=ctk.CTkFont(family=APP_FONT, size=18, weight="bold"), text_color=fg).place(relx=0.5, rely=0.5, anchor="center")

        t = ctk.CTkFrame(head, fg_color="transparent")
        t.pack(side="left", padx=10)
        ctk.CTkLabel(t, text=acc["title"], font=ctk.CTkFont(family=APP_FONT, size=15, weight="bold"), text_color=COLORS["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(t, text=acc["username"], font=ctk.CTkFont(family=APP_FONT, size=12), text_color=COLORS["text_secondary"]).pack(anchor="w")

        ctk.CTkLabel(inner, text="密码", font=ctk.CTkFont(family=APP_FONT, size=11), text_color=COLORS["text_muted"], anchor="w").pack(fill="x")
        pwd_frame = ctk.CTkFrame(inner, fg_color=COLORS["bg_input"], border_color=COLORS["border_accent"], border_width=1, corner_radius=10)
        pwd_frame.pack(fill="x", pady=(4, 12))

        show_var = ctk.BooleanVar(value=False)
        # 使用 Consolas 防止点、下划线被裁剪
        pwd_entry = ctk.CTkEntry(pwd_frame, font=ctk.CTkFont(family="Consolas", size=16, weight="bold"), fg_color="transparent", border_width=0, text_color=COLORS["accent2"], show="●")
        pwd_entry.insert(0, pwd)
        pwd_entry.configure(state="readonly")
        pwd_entry.pack(side="left", fill="x", expand=True, padx=12, pady=8)

        def copy_to_clipboard():
            self.clipboard_clear()
            self.clipboard_append(pwd)
            copy_btn.configure(text="✓ 已复制并提供5秒保护", text_color=COLORS["success"])
            self.after(5000, secure_clear_clipboard)

        def secure_clear_clipboard():
            try:
                if self.clipboard_get() == pwd:
                    self.clipboard_clear()
                    self.clipboard_append(" ")
                    self.clipboard_clear()
            except Exception: pass
            if copy_btn.winfo_exists():
                copy_btn.configure(text="⎘ 复制密码", text_color=COLORS["text_secondary"])

        copy_btn = SecondaryButton(inner, text="⎘ 复制密码", height=36, command=copy_to_clipboard)
        copy_btn.pack(fill="x")
        ctk.CTkCheckBox(pwd_frame, text="显示", variable=show_var, onvalue=True, offvalue=False, command=lambda: pwd_entry.configure(show="" if show_var.get() else "●"), font=ctk.CTkFont(family=APP_FONT, size=11), text_color=COLORS["text_muted"], fg_color=COLORS["accent"], width=60).pack(side="right", padx=8)

        def on_close():
            nonlocal pwd
            pwd = None
            del pwd
            gc.collect()
            dialog.destroy()
        dialog.protocol("WM_DELETE_WINDOW", on_close)

    def _add_account(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("添加账号")
        dialog.geometry("500x520")
        dialog.configure(fg_color=COLORS["bg_deep"])
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)

        card = GlassFrame(dialog)
        card.pack(fill="both", expand=True, padx=20, pady=20)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=32, pady=24)

        ctk.CTkLabel(inner, text="添加新账号凭证", font=ctk.CTkFont(family=APP_FONT, size=18, weight="bold"), text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, 20))

        ctk.CTkLabel(inner, text="平台名称", font=ctk.CTkFont(family=APP_FONT, size=13), text_color=COLORS["text_secondary"]).pack(anchor="w")
        e_title = StyledEntry(inner, width=400, height=40, font=ctk.CTkFont(family=APP_FONT, size=14), placeholder_text="e.g. Google")
        e_title.pack(pady=(4, 12))

        ctk.CTkLabel(inner, text="账号 / 邮箱", font=ctk.CTkFont(family=APP_FONT, size=13), text_color=COLORS["text_secondary"]).pack(anchor="w")
        e_user = StyledEntry(inner, width=400, height=40, font=ctk.CTkFont(family=APP_FONT, size=14), placeholder_text="e.g. user@example.com")
        e_user.pack(pady=(4, 12))

        ctk.CTkLabel(inner, text="密码", font=ctk.CTkFont(family=APP_FONT, size=13), text_color=COLORS["text_secondary"]).pack(anchor="w")
        e_pwd = StyledEntry(inner, width=400, height=40, font=ctk.CTkFont(family=APP_FONT, size=14), show="●", placeholder_text="输入密码")
        e_pwd.pack(pady=(4, 12))

        ctk.CTkLabel(inner, text="账号分类归属", font=ctk.CTkFont(family=APP_FONT, size=13), text_color=COLORS["text_secondary"]).pack(anchor="w")
        cat_options = self.db.get("categories", ["默认"])
        e_cat_menu = ctk.CTkOptionMenu(inner, width=400, height=40, values=cat_options, font=ctk.CTkFont(family=APP_FONT, size=13), fg_color=COLORS["bg_input"], button_color=COLORS["bg_btn_sec"], button_hover_color=COLORS["bg_card_hover"], dropdown_fg_color=COLORS["bg_card"], dropdown_font=ctk.CTkFont(family=APP_FONT, size=13), text_color=COLORS["text_primary"])
        e_cat_menu.pack(pady=(4, 20))
        e_cat_menu.set("默认")

        def save():
            t, u, p, c = e_title.get().strip(), e_user.get().strip(), e_pwd.get().strip(), e_cat_menu.get()
            if not all([t, u, p]): return
            self.db["accounts"].append({"title": t, "username": u, "password": self.crypto.encrypt(p), "category": c})
            self._save_db()
            self._render_sidebar_menu()
            self._refresh_list()
            p = None
            del p
            gc.collect()
            dialog.destroy()

        GradientButton(inner, text="➕ 确认添加", width=400, height=42, font=ctk.CTkFont(family=APP_FONT, size=14, weight="bold"), command=save).pack(fill="x")
        e_title.focus()

    def _edit_dialog(self, idx):
        acc = self.db["accounts"][idx]
        try: cur_pwd = self.crypto.decrypt(acc["password"])
        except Exception: messagebox.showerror("错误", "解密失败！"); return

        dialog = ctk.CTkToplevel(self)
        dialog.title("修改账号")
        dialog.geometry("500x520")
        dialog.configure(fg_color=COLORS["bg_deep"])
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)

        card = GlassFrame(dialog)
        card.pack(fill="both", expand=True, padx=20, pady=20)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=32, pady=24)

        ctk.CTkLabel(inner, text="修改账号凭证", font=ctk.CTkFont(family=APP_FONT, size=18, weight="bold"), text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, 20))

        ctk.CTkLabel(inner, text="平台名称", font=ctk.CTkFont(family=APP_FONT, size=13), text_color=COLORS["text_secondary"]).pack(anchor="w")
        e_title = StyledEntry(inner, width=400, height=40, font=ctk.CTkFont(family=APP_FONT, size=14))
        e_title.insert(0, acc["title"])
        e_title.pack(pady=(4, 12))

        ctk.CTkLabel(inner, text="账号 / 邮箱", font=ctk.CTkFont(family=APP_FONT, size=13), text_color=COLORS["text_secondary"]).pack(anchor="w")
        e_user = StyledEntry(inner, width=400, height=40, font=ctk.CTkFont(family=APP_FONT, size=14))
        e_user.insert(0, acc["username"])
        e_user.pack(pady=(4, 12))

        ctk.CTkLabel(inner, text="密码", font=ctk.CTkFont(family=APP_FONT, size=13), text_color=COLORS["text_secondary"]).pack(anchor="w")
        e_pwd = StyledEntry(inner, width=400, height=40, font=ctk.CTkFont(family=APP_FONT, size=14), show="●")
        e_pwd.insert(0, cur_pwd)
        e_pwd.pack(pady=(4, 12))

        ctk.CTkLabel(inner, text="账号分类归属", font=ctk.CTkFont(family=APP_FONT, size=13), text_color=COLORS["text_secondary"]).pack(anchor="w")
        cat_options = self.db.get("categories", ["默认"])
        e_cat_menu = ctk.CTkOptionMenu(inner, width=400, height=40, values=cat_options, font=ctk.CTkFont(family=APP_FONT, size=13), fg_color=COLORS["bg_input"], button_color=COLORS["bg_btn_sec"], button_hover_color=COLORS["bg_card_hover"], dropdown_fg_color=COLORS["bg_card"], dropdown_font=ctk.CTkFont(family=APP_FONT, size=13), text_color=COLORS["text_primary"])
        e_cat_menu.pack(pady=(4, 20))
        e_cat_menu.set(acc.get("category", "默认"))

        def save():
            vals = [e_title.get().strip(), e_user.get().strip(), e_pwd.get().strip(), e_cat_menu.get()]
            if not all(vals[:3]): return
            self.db["accounts"][idx]["title"], self.db["accounts"][idx]["username"] = vals[0], vals[1]
            self.db["accounts"][idx]["password"] = self.crypto.encrypt(vals[2])
            self.db["accounts"][idx]["category"] = vals[3]
            self._save_db()
            self._render_sidebar_menu()
            self._refresh_list()
            vals[2] = cur_pwd = None
            del vals, cur_pwd
            gc.collect()
            dialog.destroy()

        GradientButton(inner, text="💾  保存修改", width=400, height=42, font=ctk.CTkFont(family=APP_FONT, size=14, weight="bold"), command=save).pack(fill="x")

    def _load_db(self) -> bool:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f: self.db = json.load(f)
            return True
        return False

    def _save_db(self):
        with open(DATA_FILE, 'w', encoding='utf-8') as f: json.dump(self.db, f, indent=4, ensure_ascii=False)

    def _recover_password(self, login_win):
        rec_dialog = CustomPasswordDialog(login_win, "安全验证", "请输入安全恢复码：")
        rec_key = rec_dialog.result
        if not rec_key: return
        
        new_pwd_dialog = CustomPasswordDialog(login_win, "重置密码", "请输入全新的主密码：")
        new_pwd = new_pwd_dialog.result
        if not new_pwd: return
        
        try:
            recovery_salt = base64.b64decode(self.db.get("recovery_salt", ""))
            rec_enc_key = self.crypto.get_key_from_pwd(rec_key, recovery_salt)
            old_master_key = Fernet(rec_enc_key).decrypt(self.db.get("recovery_payload", "").encode())
            old_fernet = Fernet(old_master_key)

            decrypted = [{"title": a["title"], "username": a["username"], "password": old_fernet.decrypt(a["password"].encode()).decode(), "category": a.get("category", "默认")} for a in self.db["accounts"]]
            
            new_salt = os.urandom(16)
            self.db["salt"] = base64.b64encode(new_salt).decode()
            
            self.crypto.derive_and_set_key(new_pwd, new_salt)
            self.db["verify_token"] = self.crypto.encrypt("AUTH_SUCCESS")
            self.db["accounts"] = [{"title": a["title"], "username": a["username"], "password": self.crypto.encrypt(a["password"]), "category": a["category"]} for a in decrypted]

            new_recovery_key = "RM-" + os.urandom(6).hex().upper()
            new_recovery_salt = os.urandom(16)
            self.db["recovery_salt"] = base64.b64encode(new_recovery_salt).decode()
            f_new_rec = Fernet(self.crypto.get_key_from_pwd(new_recovery_key, new_recovery_salt))
            self.db["recovery_payload"] = f_new_rec.encrypt(self.crypto.key).decode()
            self._save_db()

            try:
                with open("安全恢复码备份.txt", "w", encoding="utf-8") as f:
                    f.write(f"你的安全恢复码是：{new_recovery_key}\n请妥善保管，切勿泄露给他人。")
                extra_msg = f"\n\n新恢复码已同步写入到【安全恢复码备份.txt】中！"
            except Exception: extra_msg = ""

            messagebox.showinfo("成功", f"密码重置成功！\n\n新恢复码：{new_recovery_key}\n请立刻核对备份。{extra_msg}")
            
            new_pwd = rec_key = old_master_key = None
            del new_pwd, rec_key, old_master_key
            gc.collect()
            
            login_win.destroy()
            LoginWindow(self)
        except Exception: 
            messagebox.showerror("错误", "恢复码不正确或数据已损坏！")
            new_pwd = rec_key = None
            del new_pwd, rec_key
            gc.collect()

    def _refresh_list(self, keyword=""):
        for w in self.list_scroll.winfo_children(): w.destroy()
        self._rows.clear()
        
        for idx, acc in enumerate(self.db["accounts"]):
            if self.current_filter_category != "全部" and acc.get("category", "默认") != self.current_filter_category: continue
            if keyword and keyword.lower() not in acc["title"].lower() and keyword.lower() not in acc["username"].lower(): continue
                
            row = AccountRow(self.list_scroll, acc, idx, on_select=self._select_row, on_view=self._view_password_dialog, on_edit=self._edit_dialog, on_delete=self._delete_account)
            row.pack(fill="x", pady=4)
            self._rows.append(row)
            
        if not self._rows:
            ctk.CTkLabel(self.list_scroll, text="该分类下空空如也 📭", font=ctk.CTkFont(family=APP_FONT, size=13), text_color=COLORS["text_muted"]).pack(pady=40)

    def _select_row(self, idx):
        for row in self._rows: row.set_selected(row.idx == idx)

    def _delete_account(self, idx):
        if messagebox.askyesno("确认删除", f"确定要删除「{self.db['accounts'][idx]['title']}」的账号吗？"):
            del self.db["accounts"][idx]
            self._save_db()
            self._render_sidebar_menu()
            self._refresh_list()

    def _on_search(self, *args): self._refresh_list(self.search_var.get())

if __name__ == "__main__":
    app = PasswordManagerApp()
    app.mainloop()
