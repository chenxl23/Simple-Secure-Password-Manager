import json
import os
import base64
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

DATA_FILE = "my_passwords.json"

class CryptoCore:
    def __init__(self):
        self.key = None
        self.fernet = None

    def get_key_from_pwd(self, pwd: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
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


class PasswordManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("安全密码管理器 Pro")
        self.root.geometry("600x500")
        
        self.crypto = CryptoCore()
        # 数据结构新增 recovery_salt 和 recovery_payload
        self.db = {"salt": "", "verify_token": "", "recovery_salt": "", "recovery_payload": "", "accounts": []}
        
        self.setup_login_ui()

    def load_db(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                self.db = json.load(f)
            return True
        return False

    def save_db(self):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.db, f, indent=4)

    def setup_login_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        main_frame = tb.Frame(self.root, padding=40)
        main_frame.place(relx=0.5, rely=0.5, anchor="center")

        tb.Label(main_frame, text="🛡️ 密码金库", font=("Microsoft YaHei UI", 24, "bold")).pack(pady=(0, 30))
        
        is_first_time = not self.load_db()
        label_text = "首次使用，请设置主密码:" if is_first_time else "请输入主密码解锁金库:"
        
        tb.Label(main_frame, text=label_text, font=("Microsoft YaHei UI", 12)).pack(pady=5)
        
        self.pwd_entry = tb.Entry(main_frame, show="●", width=30, font=("Arial", 14))
        self.pwd_entry.pack(pady=10)
        self.pwd_entry.focus()
        
        self.root.bind('<Return>', lambda event: self.login(is_first_time))
        
        btn_text = "🚀 初始化金库" if is_first_time else "🔓 解锁"
        tb.Button(main_frame, text=btn_text, bootstyle=PRIMARY, width=20, command=lambda: self.login(is_first_time)).pack(pady=15)

        # 仅在非首次且有恢复码数据时显示“忘记密码”
        if not is_first_time and self.db.get("recovery_payload"):
            tb.Button(main_frame, text="忘记密码？使用恢复码重置", bootstyle=(LINK, SECONDARY), command=self.recover_password).pack(pady=5)

    def login(self, is_first_time):
        master_pwd = self.pwd_entry.get()
        if not master_pwd:
            messagebox.showwarning("提示", "密码不能为空！")
            return

        if is_first_time:
            # 1. 设置主密码与核心密钥
            salt = os.urandom(16)
            self.db["salt"] = base64.b64encode(salt).decode()
            self.crypto.derive_and_set_key(master_pwd, salt)
            self.db["verify_token"] = self.crypto.encrypt("AUTH_SUCCESS")
            
            # 2. 生成安全恢复码
            recovery_key = "RM-" + os.urandom(6).hex().upper()
            recovery_salt = os.urandom(16)
            self.db["recovery_salt"] = base64.b64encode(recovery_salt).decode()
            
            rec_enc_key = self.crypto.get_key_from_pwd(recovery_key, recovery_salt)
            f_rec = Fernet(rec_enc_key)
            self.db["recovery_payload"] = f_rec.encrypt(self.crypto.key).decode()
            
            self.save_db()
            
            msg = (
                "初始化成功！\n\n"
                "【重要】你的安全恢复码是：\n"
                f"{recovery_key}\n\n"
                "这是你忘记主密码时的【唯一】找回凭证！\n"
                "请将它抄写在纸上或保存在手机备忘录里。"
            )
            messagebox.showwarning("⚠️ 请立刻备份恢复码", msg)
            
            self.root.unbind('<Return>')
            self.setup_main_ui()
        else:
            salt = base64.b64decode(self.db.get("salt", ""))
            self.crypto.derive_and_set_key(master_pwd, salt)
            try:
                if self.crypto.decrypt(self.db.get("verify_token", "")) == "AUTH_SUCCESS":
                    self.root.unbind('<Return>')
                    self.setup_main_ui()
                else:
                    raise InvalidToken
            except Exception:
                messagebox.showerror("错误", "密码错误，拒绝访问！")
                self.pwd_entry.delete(0, 'end')

    def recover_password(self):
        rec_key = simpledialog.askstring("恢复密码", "请输入以 RM- 开头的安全恢复码：", parent=self.root)
        if not rec_key: return
        
        new_pwd = simpledialog.askstring("重置密码", "验证成功后，请输入新的主密码：", parent=self.root, show="*")
        if not new_pwd: return
        
        try:
            recovery_salt = base64.b64decode(self.db.get("recovery_salt", ""))
            rec_enc_key = self.crypto.get_key_from_pwd(rec_key, recovery_salt)
            f_rec = Fernet(rec_enc_key)
            old_master_key = f_rec.decrypt(self.db.get("recovery_payload", "").encode())
            
            old_fernet = Fernet(old_master_key)
            decrypted_accounts = []
            for acc in self.db["accounts"]:
                decrypted_accounts.append({
                    "title": acc["title"],
                    "username": acc["username"],
                    "password": old_fernet.decrypt(acc["password"].encode()).decode()
                })
                
            new_salt = os.urandom(16)
            self.db["salt"] = base64.b64encode(new_salt).decode()
            self.crypto.derive_and_set_key(new_pwd, new_salt)
            self.db["verify_token"] = self.crypto.encrypt("AUTH_SUCCESS")
            
            self.db["accounts"] = []
            for acc in decrypted_accounts:
                self.db["accounts"].append({
                    "title": acc["title"],
                    "username": acc["username"],
                    "password": self.crypto.encrypt(acc["password"])
                })
                
            self.db["recovery_payload"] = f_rec.encrypt(self.crypto.key).decode()
            
            self.save_db()
            messagebox.showinfo("成功", "密码重置成功！所有数据已使用新密码重新加密。")
            self.setup_login_ui()
            
        except Exception:
            messagebox.showerror("错误", "恢复码不正确或数据已损坏！")

    def setup_main_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        main_frame = tb.Frame(self.root, padding=15)
        main_frame.pack(fill=BOTH, expand=True)

        # 顶部搜索
        search_frame = tb.Frame(main_frame)
        search_frame.pack(fill=X, pady=(0, 15))
        
        tb.Label(search_frame, text="🔍 搜索:", font=("Microsoft YaHei UI", 10)).pack(side=LEFT)
        self.search_var = tb.StringVar()
        self.search_var.trace("w", self.on_search)
        search_entry = tb.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=LEFT, padx=10)
        
        tb.Button(search_frame, text="🔒 锁定金库", bootstyle=DANGER, command=self.setup_login_ui).pack(side=RIGHT)

        # 中间列表
        self.tree = tb.Treeview(main_frame, columns=("Title", "Username"), show="headings", bootstyle=PRIMARY)
        self.tree.heading("Title", text="平台名称")
        self.tree.heading("Username", text="账号 / 邮箱")
        self.tree.column("Title", width=150)
        self.tree.column("Username", width=250)
        self.tree.pack(side=TOP, fill=BOTH, expand=True)
        
        self.tree.bind("<Double-1>", lambda e: self.view_password())

        self.refresh_list()

        # 底部按钮
        btn_frame = tb.Frame(main_frame)
        btn_frame.pack(fill=X, pady=(15, 0))
        
        tb.Button(btn_frame, text="➕ 添加", bootstyle=SUCCESS, command=self.add_account).pack(side=LEFT, padx=(0, 5))
        tb.Button(btn_frame, text="👁️ 查看", bootstyle=INFO, command=self.view_password).pack(side=LEFT, padx=5)
        tb.Button(btn_frame, text="✏️ 修改", bootstyle=WARNING, command=self.edit_account).pack(side=LEFT, padx=5)
        tb.Button(btn_frame, text="🗑️ 删除", bootstyle=DANGER, command=self.delete_account).pack(side=RIGHT)

    def on_search(self, *args):
        keyword = self.search_var.get().lower()
        self.refresh_list(keyword)

    def refresh_list(self, keyword=""):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, acc in enumerate(self.db["accounts"]):
            if keyword and keyword not in acc["title"].lower() and keyword not in acc["username"].lower():
                continue
            self.tree.insert("", "end", iid=idx, values=(acc["title"], acc["username"]))

    def add_account(self):
        title = simpledialog.askstring("添加", "平台名称:", parent=self.root)
        if not title: return
        username = simpledialog.askstring("添加", "账号:", parent=self.root)
        if not username: return
        password = simpledialog.askstring("添加", "密码:", parent=self.root)
        if not password: return

        self.db["accounts"].append({
            "title": title,
            "username": username,
            "password": self.crypto.encrypt(password)
        })
        self.save_db()
        self.refresh_list(self.search_var.get())

    def delete_account(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要删除的账号！")
            return
            
        if messagebox.askyesno("确认", "确定要删除选中的账号吗？"):
            del self.db["accounts"][int(selected[0])]
            self.save_db()
            self.refresh_list(self.search_var.get())

    def view_password(self):
        selected = self.tree.selection()
        if not selected: return
        
        acc = self.db["accounts"][int(selected[0])]
        
        try:
            pwd = self.crypto.decrypt(acc["password"])
            
            pwd_win = tb.Toplevel(self.root)
            pwd_win.title("查看凭证")
            pwd_win.geometry("350x200")
            pwd_win.transient(self.root)
            pwd_win.grab_set()
            
            frame = tb.Frame(pwd_win, padding=20)
            frame.pack(fill=BOTH, expand=True)
            
            tb.Label(frame, text=acc['title'], font=("Microsoft YaHei UI", 14, "bold")).pack(pady=(0,5))
            tb.Label(frame, text=acc['username']).pack(pady=5)
            
            entry = tb.Entry(frame, font=("Consolas", 14), justify="center")
            entry.insert(0, pwd)
            entry.config(state="readonly")
            entry.pack(pady=10, fill=X)
            
        except Exception:
            messagebox.showerror("错误", "解密失败！")

    def edit_account(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要修改的账号！")
            return
            
        idx = int(selected[0])
        acc = self.db["accounts"][idx]
        
        try:
            current_pwd = self.crypto.decrypt(acc["password"])
        except Exception:
            messagebox.showerror("错误", "密码解密失败，无法修改！")
            return
            
        edit_win = tb.Toplevel(self.root)
        edit_win.title("修改账号")
        edit_win.geometry("350x350")
        edit_win.transient(self.root)
        edit_win.grab_set()
        
        frame = tb.Frame(edit_win, padding=20)
        frame.pack(fill=BOTH, expand=True)
        
        tb.Label(frame, text="平台名称:").pack(anchor="w", pady=(0, 5))
        title_entry = tb.Entry(frame)
        title_entry.insert(0, acc["title"])
        title_entry.pack(fill=X, pady=(0, 10))
        
        tb.Label(frame, text="账号 / 邮箱:").pack(anchor="w", pady=(0, 5))
        user_entry = tb.Entry(frame)
        user_entry.insert(0, acc["username"])
        user_entry.pack(fill=X, pady=(0, 10))
        
        tb.Label(frame, text="密码:").pack(anchor="w", pady=(0, 5))
        pwd_entry = tb.Entry(frame)
        pwd_entry.insert(0, current_pwd)
        pwd_entry.pack(fill=X, pady=(0, 15))
        
        def save_changes():
            new_title = title_entry.get()
            new_user = user_entry.get()
            new_pwd = pwd_entry.get()
            
            if not new_title or not new_user or not new_pwd:
                messagebox.showwarning("提示", "所有字段都不能为空！", parent=edit_win)
                return
                
            self.db["accounts"][idx]["title"] = new_title
            self.db["accounts"][idx]["username"] = new_user
            self.db["accounts"][idx]["password"] = self.crypto.encrypt(new_pwd)
            
            self.save_db()
            self.refresh_list(self.search_var.get())
            edit_win.destroy()
            messagebox.showinfo("成功", "账号修改成功！")
            
        tb.Button(frame, text="💾 保存修改", bootstyle=SUCCESS, command=save_changes).pack(fill=X)

if __name__ == "__main__":
    # 使用 litera (明亮整洁) 主题
    root = tb.Window(themename="litera")
    app = PasswordManagerGUI(root)
    root.mainloop()
