import json
import os
import base64
import tkinter as tk
from tkinter import messagebox, simpledialog
import customtkinter as ctk
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# ── 依赖安装提示 ──────────────────────────────────────────────
# pip install customtkinter cryptography

DATA_FILE = "my_passwords.json"

# ── 颜色系统 ─────────────────────────────────────────────────
COLORS = {
    # 背景层
    "bg_deep":        "#0f1628",   # 最深底色
    "bg_sidebar":     "#141d35",   # 侧边栏
    "bg_card":        "#1a2444",   # 卡片背景
    "bg_card_hover":  "#1f2d55",   # 卡片悬停
    "bg_card_sel":    "#1e3060",   # 卡片选中
    "bg_input":       "#111827",   # 输入框
    "bg_btn_sec":     "#1e2a45",   # 次级按钮

    # 强调色
    "accent":         "#5b8fff",   # 主蓝
    "accent_dark":    "#3d6fe8",
    "accent2":        "#a78bfa",   # 紫色
    "success":        "#34d399",   # 绿
    "warning":        "#fbbf24",   # 琥珀
    "danger":         "#f87171",   # 红

    # 文字
    "text_primary":   "#e8eaf6",
    "text_secondary": "#7986a8",
    "text_muted":     "#4a5578",

    # 边框
    "border":         "#243058",
    "border_accent":  "#3d5a9e",
}

# ── 加密核心 ─────────────────────────────────────────────────
class CryptoCore:
    def __init__(self):
        self.key = None
        self.fernet = None

    def get_key_from_pwd(self, pwd: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
                         salt=salt, iterations=480000)
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


# ── 自定义组件 ────────────────────────────────────────────────
class GlassFrame(ctk.CTkFrame):
    """带边框的半透明卡片"""
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", COLORS["bg_card"])
        kwargs.setdefault("border_color", COLORS["border"])
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("corner_radius", 14)
        super().__init__(master, **kwargs)


class GradientButton(ctk.CTkButton):
    """渐变主按钮"""
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", COLORS["accent"])
        kwargs.setdefault("hover_color", COLORS["accent_dark"])
        kwargs.setdefault("corner_radius", 10)
        kwargs.setdefault("font", ctk.CTkFont(size=13, weight="bold"))
        kwargs.setdefault("text_color", "#ffffff")
        super().__init__(master, **kwargs)


class SecondaryButton(ctk.CTkButton):
    """次级按钮"""
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", COLORS["bg_btn_sec"])
        kwargs.setdefault("hover_color", COLORS["bg_card_hover"])
        kwargs.setdefault("border_color", COLORS["border_accent"])
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("corner_radius", 10)
        kwargs.setdefault("font", ctk.CTkFont(size=12))
        kwargs.setdefault("text_color", COLORS["text_secondary"])
        super().__init__(master, **kwargs)


class IconButton(ctk.CTkButton):
    """小图标按钮"""
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", COLORS["bg_btn_sec"])
        kwargs.setdefault("hover_color", COLORS["bg_card_hover"])
        kwargs.setdefault("corner_radius", 8)
        kwargs.setdefault("width", 32)
        kwargs.setdefault("height", 32)
        kwargs.setdefault("font", ctk.CTkFont(size=13))
        kwargs.setdefault("text_color", COLORS["text_secondary"])
        super().__init__(master, **kwargs)


class StyledEntry(ctk.CTkEntry):
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", COLORS["bg_input"])
        kwargs.setdefault("border_color", COLORS["border"])
        kwargs.setdefault("text_color", COLORS["text_primary"])
        kwargs.setdefault("placeholder_text_color", COLORS["text_muted"])
        kwargs.setdefault("corner_radius", 10)
        kwargs.setdefault("font", ctk.CTkFont(size=13))
        super().__init__(master, **kwargs)


class TagLabel(ctk.CTkLabel):
    """小标签/分类标注"""
    def __init__(self, master, text, color_key="accent", **kwargs):
        c = COLORS[color_key]
        super().__init__(master, text=text,
                         fg_color=c + "33",
                         text_color=c,
                         corner_radius=6,
                         font=ctk.CTkFont(size=10),
                         **kwargs)


# ── 账号行卡片 ────────────────────────────────────────────────
LOGO_COLORS = {
    "Google":   ("#f87171", "#1e1818"),
    "GitHub":   ("#c9d1d9", "#1a1f2e"),
    "Twitter":  ("#60a5fa", "#0d1b2e"),
    "Amazon":   ("#fbbf24", "#1e1800"),
    "Netflix":  ("#f87171", "#1e1010"),
    "Steam":    ("#7dd3fc", "#0a1a2e"),
}

def logo_colors(title: str):
    for key, (fg, bg) in LOGO_COLORS.items():
        if key.lower() in title.lower():
            return fg, bg
    return COLORS["accent2"], COLORS["bg_card"]


class AccountRow(ctk.CTkFrame):
    def __init__(self, master, acc_data: dict, idx: int,
                 on_select, on_copy, on_view, on_edit, on_delete, **kwargs):
        super().__init__(master,
                         fg_color=COLORS["bg_card"],
                         border_color=COLORS["border"],
                         border_width=1,
                         corner_radius=12, **kwargs)
        self.idx = idx
        self.acc = acc_data
        self.selected = False
        self._on_select = on_select
        self.configure(cursor="hand2")

        # ── Logo 圆圈
        fg, bg = logo_colors(acc_data["title"])
        logo_frame = ctk.CTkFrame(self, width=42, height=42,
                                  fg_color=bg, corner_radius=10)
        logo_frame.pack(side="left", padx=(14, 10), pady=10)
        logo_frame.pack_propagate(False)
        initials = acc_data["title"][0].upper()
        ctk.CTkLabel(logo_frame, text=initials,
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=fg).place(relx=0.5, rely=0.5, anchor="center")

        # ── 账号信息
        info = ctk.CTkFrame(self, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, pady=8)
        ctk.CTkLabel(info, text=acc_data["title"],
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=COLORS["text_primary"],
                     anchor="w").pack(fill="x")
        ctk.CTkLabel(info, text=acc_data["username"],
                     font=ctk.CTkFont(size=11),
                     text_color=COLORS["text_secondary"],
                     anchor="w").pack(fill="x")

        # ── 密码点点
        ctk.CTkLabel(self, text="●●●●●●●●",
                     font=ctk.CTkFont(size=9),
                     text_color=COLORS["text_muted"]).pack(side="left", padx=10)

        # ── 操作按钮
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side="right", padx=10, pady=8)
        IconButton(btn_frame, text="⎘", width=30, height=28,
                   command=lambda: on_copy(idx)).pack(side="left", padx=2)
        IconButton(btn_frame, text="👁", width=30, height=28,
                   command=lambda: on_view(idx)).pack(side="left", padx=2)
        IconButton(btn_frame, text="✏", width=30, height=28,
                   command=lambda: on_edit(idx)).pack(side="left", padx=2)
        IconButton(btn_frame, text="✕", width=30, height=28,
                   fg_color=COLORS["bg_btn_sec"],
                   hover_color="#3d1818",
                   text_color=COLORS["danger"],
                   command=lambda: on_delete(idx)).pack(side="left", padx=2)

        # 点击整行选中
        for w in [self, info, logo_frame]:
            w.bind("<Button-1>", lambda e, i=idx: on_select(i))

    def set_selected(self, selected: bool):
        self.selected = selected
        color = COLORS["bg_card_sel"] if selected else COLORS["bg_card"]
        border = COLORS["border_accent"] if selected else COLORS["border"]
        self.configure(fg_color=color, border_color=border)


# ── 侧边栏导航项 ──────────────────────────────────────────────
class NavItem(ctk.CTkFrame):
    def __init__(self, master, icon: str, label: str,
                 active=False, badge=None, command=None, **kwargs):
        super().__init__(master, fg_color="transparent",
                         corner_radius=10, **kwargs)
        self._command = command
        self._active = active

        self.inner = ctk.CTkFrame(self,
                                  fg_color=COLORS["bg_card"] if active else "transparent",
                                  corner_radius=10)
        self.inner.pack(fill="x", padx=4, pady=1)

        row = ctk.CTkFrame(self.inner, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=7)

        ctk.CTkLabel(row, text=icon, font=ctk.CTkFont(size=15),
                     text_color=COLORS["accent"] if active else COLORS["text_secondary"],
                     width=22).pack(side="left")
        ctk.CTkLabel(row, text=label,
                     font=ctk.CTkFont(size=13,
                                      weight="bold" if active else "normal"),
                     text_color=COLORS["text_primary"] if active else COLORS["text_secondary"],
                     anchor="w").pack(side="left", padx=6, fill="x", expand=True)

        if badge:
            ctk.CTkLabel(row, text=str(badge),
                         fg_color=COLORS["accent"] + "33",
                         text_color=COLORS["accent"],
                         corner_radius=8,
                         font=ctk.CTkFont(size=10),
                         width=28, height=18).pack(side="right")

        self.inner.bind("<Button-1>", self._click)
        for child in self.inner.winfo_children():
            child.bind("<Button-1>", self._click)
        self.inner.configure(cursor="hand2")

    def _click(self, event=None):
        if self._command:
            self._command()


# ── 统计卡片 ─────────────────────────────────────────────────
class StatCard(GlassFrame):
    def __init__(self, master, icon, value, label, accent, **kwargs):
        super().__init__(master, **kwargs)
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=12)

        # 图标圆圈
        icon_frame = ctk.CTkFrame(inner, width=36, height=36,
                                  fg_color=accent + "33",
                                  corner_radius=10)
        icon_frame.pack(anchor="w")
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(icon_frame, text=icon,
                     font=ctk.CTkFont(size=16),
                     text_color=accent).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(inner, text=str(value),
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=COLORS["text_primary"]).pack(anchor="w", pady=(6, 0))
        ctk.CTkLabel(inner, text=label,
                     font=ctk.CTkFont(size=11),
                     text_color=COLORS["text_muted"]).pack(anchor="w")


# ── 主应用 ────────────────────────────────────────────────────
class PasswordManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("密码金库  ·  SafeVault Pro")
        self.geometry("900x600")
        self.minsize(800, 520)
        self.configure(fg_color=COLORS["bg_deep"])

        self.crypto = CryptoCore()
        self.db = {"salt": "", "verify_token": "",
                   "recovery_salt": "", "recovery_payload": "",
                   "accounts": []}
        self.selected_idx = None
        self._rows: list[AccountRow] = []

        self.setup_login_ui()

    # ═══════════════════════════════════════════════════════════
    # 登录界面
    # ═══════════════════════════════════════════════════════════
    def setup_login_ui(self):
        self._clear()
        self.geometry("420x520")
        self.resizable(False, False)

        # 渐变背景感：深色外框 + 卡片
        outer = ctk.CTkFrame(self, fg_color=COLORS["bg_deep"])
        outer.place(relx=0.5, rely=0.5, anchor="center",
                    relwidth=1.0, relheight=1.0)

        card = GlassFrame(outer, width=340, height=400)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center",
                    relwidth=0.85, relheight=0.9)

        # Logo
        logo_bg = ctk.CTkFrame(inner, width=64, height=64,
                               fg_color=COLORS["accent"] + "22",
                               corner_radius=18)
        logo_bg.pack(pady=(10, 0))
        logo_bg.pack_propagate(False)
        ctk.CTkLabel(logo_bg, text="🛡",
                     font=ctk.CTkFont(size=28)).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(inner, text="密码金库",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=COLORS["text_primary"]).pack(pady=(12, 2))

        is_first = not self._load_db()
        hint = "首次使用，请设置主密码" if is_first else "输入主密码以解锁金库"
        ctk.CTkLabel(inner, text=hint,
                     font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_muted"]).pack(pady=(0, 18))

        self.pwd_entry = StyledEntry(inner, width=240, height=42,
                                     show="●",
                                     placeholder_text="主密码")
        self.pwd_entry.pack(pady=(0, 16))
        self.pwd_entry.focus()
        self.bind("<Return>", lambda e: self._login(is_first))

        btn_text = "  初始化金库  " if is_first else "  解锁金库  "
        GradientButton(inner, text=btn_text, height=42, width=240,
                       command=lambda: self._login(is_first)).pack()

        if not is_first and self.db.get("recovery_payload"):
            ctk.CTkButton(inner, text="忘记密码？使用恢复码重置",
                          fg_color="transparent",
                          hover_color=COLORS["bg_card"],
                          text_color=COLORS["text_muted"],
                          font=ctk.CTkFont(size=11),
                          command=self._recover_password).pack(pady=(12, 0))

    # ═══════════════════════════════════════════════════════════
    # 主界面
    # ═══════════════════════════════════════════════════════════
    def setup_main_ui(self):
        self._clear()
        self.geometry("960x640")
        self.resizable(True, True)

        root_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_deep"])
        root_frame.pack(fill="both", expand=True)

        # ── 左侧边栏
        sidebar = ctk.CTkFrame(root_frame, width=210,
                               fg_color=COLORS["bg_sidebar"],
                               corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self._build_sidebar(sidebar)

        # ── 右侧内容区
        content = ctk.CTkFrame(root_frame, fg_color=COLORS["bg_deep"],
                               corner_radius=0)
        content.pack(side="left", fill="both", expand=True)
        self._build_content(content)

    def _build_sidebar(self, parent):
        # 品牌区
        brand = ctk.CTkFrame(parent, fg_color="transparent")
        brand.pack(fill="x", padx=14, pady=(20, 12))

        logo_bg = ctk.CTkFrame(brand, width=38, height=38,
                               fg_color=COLORS["accent"] + "33",
                               corner_radius=10)
        logo_bg.pack(side="left")
        logo_bg.pack_propagate(False)
        ctk.CTkLabel(logo_bg, text="🛡",
                     font=ctk.CTkFont(size=18)).place(relx=0.5, rely=0.5, anchor="center")

        brand_text = ctk.CTkFrame(brand, fg_color="transparent")
        brand_text.pack(side="left", padx=8)
        ctk.CTkLabel(brand_text, text="密码金库",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=COLORS["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(brand_text, text="SafeVault Pro",
                     font=ctk.CTkFont(size=10),
                     text_color=COLORS["text_muted"]).pack(anchor="w")

        # 分隔线
        ctk.CTkFrame(parent, height=1,
                     fg_color=COLORS["border"]).pack(fill="x", padx=14, pady=(0, 10))

        # 导航
        count = len(self.db["accounts"])
        nav_items = [
            ("  ⊞", "全部账号", True, count),
            ("  ★", "收藏夹",   False, None),
            ("  ⏱", "最近使用", False, None),
        ]
        self._nav_label(parent, "主菜单")
        for icon, label, active, badge in nav_items:
            NavItem(parent, icon, label, active=active,
                    badge=badge).pack(fill="x", padx=8)

        self._nav_label(parent, "分类")
        for icon, label in [("  ☁", "社交媒体"), ("  💳", "金融账户"), ("  ⌨", "开发工具")]:
            NavItem(parent, icon, label).pack(fill="x", padx=8)

        self._nav_label(parent, "系统")
        NavItem(parent, "  ⚙", "偏好设置").pack(fill="x", padx=8)
        NavItem(parent, "  🔒", "锁定金库",
                command=self._lock).pack(fill="x", padx=8)

        # 底部用户区
        ctk.CTkFrame(parent, height=1,
                     fg_color=COLORS["border"]).pack(fill="x", padx=14, pady=(10, 8), side="bottom")
        user_bar = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"],
                                corner_radius=10, side="bottom")
        user_bar.pack(fill="x", padx=10, pady=(0, 14), side="bottom")
        row = ctk.CTkFrame(user_bar, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=8)

        av = ctk.CTkFrame(row, width=30, height=30,
                          fg_color=COLORS["accent"] + "55",
                          corner_radius=15)
        av.pack(side="left")
        av.pack_propagate(False)
        ctk.CTkLabel(av, text="我", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["accent2"]).place(relx=0.5, rely=0.5, anchor="center")
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", padx=8)
        ctk.CTkLabel(info, text="本地用户",
                     font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(info, text="已加密保护",
                     font=ctk.CTkFont(size=10),
                     text_color=COLORS["success"]).pack(anchor="w")

    def _nav_label(self, parent, text):
        ctk.CTkLabel(parent, text=text,
                     font=ctk.CTkFont(size=10),
                     text_color=COLORS["text_muted"],
                     anchor="w").pack(fill="x", padx=22, pady=(12, 2))

    def _build_content(self, parent):
        # ── 顶部栏
        topbar = ctk.CTkFrame(parent, fg_color="transparent", height=64)
        topbar.pack(fill="x", padx=24, pady=(20, 0))
        topbar.pack_propagate(False)

        ctk.CTkLabel(topbar, text="全部账号",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=COLORS["text_primary"]).pack(side="left", anchor="center")

        # 搜索框
        search_frame = ctk.CTkFrame(topbar, fg_color=COLORS["bg_card"],
                                    border_color=COLORS["border"],
                                    border_width=1,
                                    corner_radius=10, height=38)
        search_frame.pack(side="left", padx=20, anchor="center")
        search_frame.pack_propagate(False)
        ctk.CTkLabel(search_frame, text="🔍",
                     font=ctk.CTkFont(size=13),
                     text_color=COLORS["text_muted"]).pack(side="left", padx=(10, 4))
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", self._on_search)
        ctk.CTkEntry(search_frame,
                     textvariable=self.search_var,
                     width=180, height=36,
                     fg_color="transparent",
                     border_width=0,
                     text_color=COLORS["text_primary"],
                     placeholder_text="搜索平台或账号…",
                     placeholder_text_color=COLORS["text_muted"],
                     font=ctk.CTkFont(size=13)).pack(side="left")

        GradientButton(topbar, text="＋  添加账号",
                       height=38, width=130,
                       command=self._add_account).pack(side="right", anchor="center")

        # ── 统计卡片
        stats_frame = ctk.CTkFrame(parent, fg_color="transparent")
        stats_frame.pack(fill="x", padx=24, pady=(16, 0))

        count = len(self.db["accounts"])
        for icon, val, label, accent, col in [
            ("🔑", count,         "已保存账号",   COLORS["accent"],  0),
            ("🛡", max(count-2,0),"密码强度正常", COLORS["success"], 1),
            ("⚠", min(count,2),  "建议更新",     COLORS["warning"], 2),
        ]:
            c = StatCard(stats_frame, icon, val, label, accent)
            c.grid(row=0, column=col, sticky="nsew", padx=(0, 12 if col < 2 else 0))
        stats_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # ── 筛选标签栏
        filter_bar = ctk.CTkFrame(parent, fg_color="transparent")
        filter_bar.pack(fill="x", padx=24, pady=(16, 8))

        ctk.CTkLabel(filter_bar, text="账号列表",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=COLORS["text_secondary"]).pack(side="left")

        for label, active in [("全部", True), ("社交", False), ("金融", False), ("开发", False)]:
            fg = COLORS["accent"] + "33" if active else COLORS["bg_btn_sec"]
            tc = COLORS["accent"] if active else COLORS["text_muted"]
            ctk.CTkButton(filter_bar, text=label,
                          fg_color=fg, hover_color=COLORS["bg_card_hover"],
                          text_color=tc,
                          font=ctk.CTkFont(size=11),
                          corner_radius=20, height=26, width=52,
                          border_width=1 if active else 0,
                          border_color=COLORS["border_accent"] if active else "transparent"
                          ).pack(side="right", padx=4)

        # ── 账号列表 (可滚动)
        self.list_scroll = ctk.CTkScrollableFrame(
            parent,
            fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["border_accent"]
        )
        self.list_scroll.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        self._refresh_list()

    # ═══════════════════════════════════════════════════════════
    # 弹窗 & 对话框
    # ═══════════════════════════════════════════════════════════
    def _show_dialog(self, title, fields: list[tuple]) -> dict | None:
        """通用弹窗，fields = [(label, placeholder, show_char_or_None)]"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("360x80")
        dialog.configure(fg_color=COLORS["bg_deep"])
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)

        card = GlassFrame(dialog)
        card.pack(fill="both", expand=True, padx=14, pady=14)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(inner, text=title,
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, 14))

        entries = []
        height_extra = 60 * len(fields) + 80
        dialog.geometry(f"360x{height_extra}")

        for label, placeholder, show in fields:
            ctk.CTkLabel(inner, text=label,
                         font=ctk.CTkFont(size=12),
                         text_color=COLORS["text_secondary"]).pack(anchor="w")
            kw = dict(width=300, height=38, placeholder_text=placeholder)
            if show:
                kw["show"] = show
            e = StyledEntry(inner, **kw)
            e.pack(pady=(2, 10))
            entries.append(e)

        result = {}

        def confirm():
            for i, (label, _, _) in enumerate(fields):
                val = entries[i].get().strip()
                if not val:
                    return
                result[label] = val
            dialog.destroy()

        def cancel():
            dialog.destroy()

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x", pady=(4, 0))
        SecondaryButton(btn_row, text="取消", width=80, command=cancel).pack(side="right", padx=(8, 0))
        GradientButton(btn_row, text="确认", width=80, command=confirm).pack(side="right")

        entries[0].focus()
        dialog.bind("<Return>", lambda e: confirm())
        dialog.bind("<Escape>", lambda e: cancel())
        dialog.wait_window()
        return result if result else None

    def _view_password_dialog(self, idx):
        acc = self.db["accounts"][idx]
        try:
            pwd = self.crypto.decrypt(acc["password"])
        except Exception:
            messagebox.showerror("错误", "解密失败！")
            return

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
        ctk.CTkLabel(head, text=acc["title"][0].upper(),
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=fg,
                     width=44, height=44,
                     fg_color=fg + "22",
                     corner_radius=12).pack(side="left")
        t = ctk.CTkFrame(head, fg_color="transparent")
        t.pack(side="left", padx=10)
        ctk.CTkLabel(t, text=acc["title"],
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=COLORS["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(t, text=acc["username"],
                     font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_secondary"]).pack(anchor="w")

        ctk.CTkLabel(inner, text="密码",
                     font=ctk.CTkFont(size=11),
                     text_color=COLORS["text_muted"],
                     anchor="w").pack(fill="x")

        pwd_frame = ctk.CTkFrame(inner, fg_color=COLORS["bg_input"],
                                 border_color=COLORS["border_accent"],
                                 border_width=1, corner_radius=10)
        pwd_frame.pack(fill="x", pady=(4, 12))

        show_var = ctk.BooleanVar(value=False)
        pwd_entry = ctk.CTkEntry(pwd_frame,
                                 font=ctk.CTkFont(family="Courier", size=15),
                                 fg_color="transparent", border_width=0,
                                 text_color=COLORS["accent2"],
                                 show="●")
        pwd_entry.insert(0, pwd)
        pwd_entry.configure(state="readonly")
        pwd_entry.pack(side="left", fill="x", expand=True, padx=12, pady=8)

        def toggle_show():
            if show_var.get():
                pwd_entry.configure(show="")
            else:
                pwd_entry.configure(show="●")

        ctk.CTkCheckBox(pwd_frame, text="显示",
                        variable=show_var,
                        onvalue=True, offvalue=False,
                        command=toggle_show,
                        font=ctk.CTkFont(size=11),
                        text_color=COLORS["text_muted"],
                        fg_color=COLORS["accent"],
                        width=60).pack(side="right", padx=8)

        def copy_pwd():
            self.clipboard_clear()
            self.clipboard_append(pwd)
            copy_btn.configure(text="✓ 已复制", fg_color=COLORS["success"] + "44",
                               text_color=COLORS["success"])
            dialog.after(2000, lambda: copy_btn.configure(
                text="⎘ 复制密码", fg_color=COLORS["bg_btn_sec"],
                text_color=COLORS["text_secondary"]))

        copy_btn = SecondaryButton(inner, text="⎘ 复制密码", height=36,
                                   command=copy_pwd)
        copy_btn.pack(fill="x")

    def _edit_dialog(self, idx):
        acc = self.db["accounts"][idx]
        try:
            cur_pwd = self.crypto.decrypt(acc["password"])
        except Exception:
            messagebox.showerror("错误", "解密失败！")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("修改账号")
        dialog.geometry("380x360")
        dialog.configure(fg_color=COLORS["bg_deep"])
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)

        card = GlassFrame(dialog)
        card.pack(fill="both", expand=True, padx=14, pady=14)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(inner, text="修改账号",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=COLORS["text_primary"]).pack(anchor="w", pady=(0, 16))

        fields_cfg = [("平台名称", acc["title"]), ("账号 / 邮箱", acc["username"]), ("密码", cur_pwd)]
        entries = []
        for label, default in fields_cfg:
            ctk.CTkLabel(inner, text=label,
                         font=ctk.CTkFont(size=12),
                         text_color=COLORS["text_secondary"]).pack(anchor="w")
            e = StyledEntry(inner, width=300, height=36)
            e.insert(0, default)
            e.pack(pady=(2, 10))
            entries.append(e)

        def save():
            vals = [e.get().strip() for e in entries]
            if not all(vals):
                return
            self.db["accounts"][idx]["title"] = vals[0]
            self.db["accounts"][idx]["username"] = vals[1]
            self.db["accounts"][idx]["password"] = self.crypto.encrypt(vals[2])
            self._save_db()
            self._refresh_list()
            dialog.destroy()

        GradientButton(inner, text="💾  保存修改",
                       height=38, command=save).pack(fill="x", pady=(4, 0))

    # ═══════════════════════════════════════════════════════════
    # 数据操作
    # ═══════════════════════════════════════════════════════════
    def _load_db(self) -> bool:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                self.db = json.load(f)
            return True
        return False

    def _save_db(self):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.db, f, indent=4, ensure_ascii=False)

    def _login(self, is_first_time: bool):
        master_pwd = self.pwd_entry.get()
        if not master_pwd:
            messagebox.showwarning("提示", "密码不能为空！")
            return

        if is_first_time:
            salt = os.urandom(16)
            self.db["salt"] = base64.b64encode(salt).decode()
            self.crypto.derive_and_set_key(master_pwd, salt)
            self.db["verify_token"] = self.crypto.encrypt("AUTH_SUCCESS")

            recovery_key = "RM-" + os.urandom(6).hex().upper()
            recovery_salt = os.urandom(16)
            self.db["recovery_salt"] = base64.b64encode(recovery_salt).decode()
            rec_enc_key = self.crypto.get_key_from_pwd(recovery_key, recovery_salt)
            f_rec = Fernet(rec_enc_key)
            self.db["recovery_payload"] = f_rec.encrypt(self.crypto.key).decode()
            self._save_db()

            msg = (f"初始化成功！\n\n【重要】你的安全恢复码是：\n"
                   f"{recovery_key}\n\n"
                   f"这是忘记主密码时的唯一找回凭证，请妥善保存！")
            messagebox.showwarning("⚠️ 请立刻备份恢复码", msg)
            self.unbind("<Return>")
            self.setup_main_ui()
        else:
            salt = base64.b64decode(self.db.get("salt", ""))
            self.crypto.derive_and_set_key(master_pwd, salt)
            try:
                if self.crypto.decrypt(self.db.get("verify_token", "")) == "AUTH_SUCCESS":
                    self.unbind("<Return>")
                    self.setup_main_ui()
                else:
                    raise InvalidToken
            except Exception:
                messagebox.showerror("错误", "密码错误，拒绝访问！")
                self.pwd_entry.delete(0, "end")

    def _lock(self):
        self.crypto = CryptoCore()
        self.setup_login_ui()

    def _recover_password(self):
        rec_key = simpledialog.askstring("恢复密码", "请输入以 RM- 开头的安全恢复码：",
                                         parent=self)
        if not rec_key:
            return
        new_pwd = simpledialog.askstring("重置密码", "请输入新的主密码：",
                                         parent=self, show="*")
        if not new_pwd:
            return
        try:
            recovery_salt = base64.b64decode(self.db.get("recovery_salt", ""))
            rec_enc_key = self.crypto.get_key_from_pwd(rec_key, recovery_salt)
            f_rec = Fernet(rec_enc_key)
            old_master_key = f_rec.decrypt(self.db.get("recovery_payload", "").encode())
            old_fernet = Fernet(old_master_key)

            decrypted = []
            for acc in self.db["accounts"]:
                decrypted.append({
                    "title": acc["title"], "username": acc["username"],
                    "password": old_fernet.decrypt(acc["password"].encode()).decode()
                })

            new_salt = os.urandom(16)
            self.db["salt"] = base64.b64encode(new_salt).decode()
            self.crypto.derive_and_set_key(new_pwd, new_salt)
            self.db["verify_token"] = self.crypto.encrypt("AUTH_SUCCESS")
            self.db["accounts"] = [
                {"title": a["title"], "username": a["username"],
                 "password": self.crypto.encrypt(a["password"])}
                for a in decrypted
            ]

            # 用新恢复码重新生成 payload
            new_recovery_key = "RM-" + os.urandom(6).hex().upper()
            new_recovery_salt = os.urandom(16)
            self.db["recovery_salt"] = base64.b64encode(new_recovery_salt).decode()
            new_rec_enc_key = self.crypto.get_key_from_pwd(new_recovery_key, new_recovery_salt)
            f_new_rec = Fernet(new_rec_enc_key)
            self.db["recovery_payload"] = f_new_rec.encrypt(self.crypto.key).decode()
            self._save_db()

            messagebox.showinfo("成功",
                                f"密码重置成功！\n\n新恢复码：{new_recovery_key}\n请重新备份。")
            self.setup_login_ui()
        except Exception:
            messagebox.showerror("错误", "恢复码不正确或数据已损坏！")

    def _refresh_list(self, keyword=""):
        for w in self.list_scroll.winfo_children():
            w.destroy()
        self._rows.clear()
        self.selected_idx = None

        for idx, acc in enumerate(self.db["accounts"]):
            if keyword and keyword.lower() not in acc["title"].lower() \
                       and keyword.lower() not in acc["username"].lower():
                continue
            row = AccountRow(
                self.list_scroll, acc, idx,
                on_select=self._select_row,
                on_copy=self._copy_password,
                on_view=self._view_password_dialog,
                on_edit=self._edit_dialog,
                on_delete=self._delete_account,
            )
            row.pack(fill="x", pady=4)
            self._rows.append(row)

        if not self.db["accounts"]:
            ctk.CTkLabel(self.list_scroll,
                         text="还没有任何账号，点击右上角「添加账号」开始吧 ✨",
                         font=ctk.CTkFont(size=13),
                         text_color=COLORS["text_muted"]).pack(pady=40)

    def _select_row(self, idx):
        for row in self._rows:
            row.set_selected(row.idx == idx)
        self.selected_idx = idx

    def _copy_password(self, idx):
        try:
            pwd = self.crypto.decrypt(self.db["accounts"][idx]["password"])
            self.clipboard_clear()
            self.clipboard_append(pwd)
        except Exception:
            messagebox.showerror("错误", "复制失败！")

    def _add_account(self):
        result = self._show_dialog("添加账号", [
            ("平台名称", "e.g. Google", None),
            ("账号 / 邮箱", "e.g. user@example.com", None),
            ("密码", "输入密码", "●"),
        ])
        if not result:
            return
        keys = list(result.keys())
        self.db["accounts"].append({
            "title": result[keys[0]],
            "username": result[keys[1]],
            "password": self.crypto.encrypt(result[keys[2]])
        })
        self._save_db()
        self._refresh_list(getattr(self, "search_var", ctk.StringVar()).get())

    def _delete_account(self, idx):
        acc = self.db["accounts"][idx]
        if messagebox.askyesno("确认删除",
                               f"确定要删除「{acc['title']}」的账号吗？\n此操作不可撤销。"):
            del self.db["accounts"][idx]
            self._save_db()
            self._refresh_list()

    def _on_search(self, *args):
        self._refresh_list(self.search_var.get())

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()


# ── 入口 ─────────────────────────────────────────────────────
if __name__ == "__main__":
    app = PasswordManagerApp()
    app.mainloop()
