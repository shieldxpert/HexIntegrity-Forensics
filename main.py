import os
import platform

if platform.system() != "Windows":
    os.environ["GDK_BACKEND"] = "x11"
    os.environ["LIBGL_ALWAYS_SOFTWARE"] = "1"
    os.environ["QT_QPA_PLATFORM"] = "xcb"

import sys
import ctypes
import shutil
import hashlib
import random
import threading
import datetime
import time
import re
import subprocess
from tkinter import filedialog, Toplevel
import customtkinter
from PIL import Image, ImageTk

customtkinter.set_appearance_mode("dark")

def _resolve_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class HexIntegrityApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("HexIntegrity System - Forensics Edition")
        self.geometry("920x460") 
        
        if platform.system() == "Windows":
            self.overrideredirect(True)
        else:
            self.resizable(True, True)
        
        self.configure(fg_color="#000000")

        self.pos_x = 0
        self.pos_y = 0
        self.app_icon_img = None
        
        self.audit_file = _resolve_path("HEX_SESSION_AUDIT.log")
        self._log_audit("SESSION_START", "HexIntegrity Forensics Engine Initialized")

        self._initialize_icons()
        self._initialize_ui()
        
        threading.Thread(target=self._async_usb_scanner, daemon=True).start()

        if platform.system() != "Windows":
            self.update_idletasks()
            self.deiconify()

    def _log_audit(self, action, details):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.audit_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] [{action}] -> {details}\n")
        except Exception as e:
            self.log_to_console(f"[CRITICAL] AUDIT LOG FAILURE: {str(e)}")

    def _apply_window_icon(self, window):
        try:
            if platform.system() == "Windows":
                window.iconbitmap(_resolve_path("icono.ico"))
            else:
                if getattr(self, "app_icon_img", None) is None:
                    img = Image.open(_resolve_path("icono.png"))
                    self.app_icon_img = ImageTk.PhotoImage(img)
                window.wm_iconphoto(True, self.app_icon_img)
        except Exception as e:
            self._log_audit("ICON_LOAD_ERROR", str(e))

    def _initialize_icons(self):
        if platform.system() == "Windows":
            try:
                myappid = 'core.hexintegrity.forensic.2'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except Exception as e:
                self._log_audit("WIN_APP_ID_ERROR", str(e))

        self._apply_window_icon(self)

        try:
            if platform.system() == "Windows":
                bg_img = Image.open(_resolve_path("interfaz_win.png"))
            else:
                bg_img = Image.open(_resolve_path("interfaz_lin.png"))
            self.bg_ctk = customtkinter.CTkImage(light_image=bg_img, dark_image=bg_img, size=(920, 460))
        except Exception as e:
            self._log_audit("BACKGROUND_LOAD_WARNING", f"Falling back to default. Error: {str(e)}")
            try:
                bg_img = Image.open(_resolve_path("interfaz.png"))
                self.bg_ctk = customtkinter.CTkImage(light_image=bg_img, dark_image=bg_img, size=(920, 460))
            except Exception as e2:
                self._log_audit("BACKGROUND_LOAD_CRITICAL", str(e2))
                self.bg_ctk = None

        def load_icon(filename):
            try: 
                return customtkinter.CTkImage(Image.open(_resolve_path(filename)), size=(50, 50))
            except Exception as e:
                self._log_audit("ICON_LOAD_ERROR", f"File: {filename} - {str(e)}")
                return None

        self.img_min_off = load_icon("btn_min_off.png")
        self.img_min_on = load_icon("btn_min_on.png")
        self.img_close_off = load_icon("btn_cerrar_off.png")
        self.img_close_on = load_icon("btn_cerrar_on.png")

    def _initialize_ui(self):
        self.main_container = customtkinter.CTkFrame(self, width=920, height=460, fg_color="#000000", corner_radius=0)
        self.main_container.place(relx=0.5, rely=0.5, anchor="center")

        self.master_layer = customtkinter.CTkLabel(self.main_container, text="", image=self.bg_ctk)
        self.master_layer.place(x=0, y=0, relwidth=1, relheight=1)

        self.master_layer.bind("<ButtonPress-1>", self.start_drag)
        self.master_layer.bind("<B1-Motion>", self.drag_window)

        if platform.system() == "Windows":
            self.btn_min = customtkinter.CTkButton(self.master_layer, text="", image=self.img_min_off, width=50, height=50, fg_color="#000000", bg_color="#000000", hover=False, corner_radius=0, command=self.minimize_window)
            self.btn_min.place(x=785, y=20)
            self.btn_close = customtkinter.CTkButton(self.master_layer, text="", image=self.img_close_off, width=50, height=50, fg_color="#000000", bg_color="#000000", hover=False, corner_radius=0, command=self.close_application)
            self.btn_close.place(x=840, y=20)
            self.btn_min.bind("<Enter>", lambda e: self.btn_min.configure(image=self.img_min_on))
            self.btn_min.bind("<Leave>", lambda e: self.btn_min.configure(image=self.img_min_off))
            self.btn_close.bind("<Enter>", lambda e: self.btn_close.configure(image=self.img_close_on))
            self.btn_close.bind("<Leave>", lambda e: self.btn_close.configure(image=self.img_close_off))

        self.drive_var = customtkinter.StringVar(value="INITIALIZING...")
        self.combo_drives = customtkinter.CTkOptionMenu(self.master_layer, values=["INITIALIZING..."], variable=self.drive_var, width=120, height=30, fg_color="#000000", bg_color="#000000", corner_radius=0, button_color="#000000", button_hover_color="#0a1a1f", text_color="#00ff00", font=("Courier", 13, "bold"), command=self._log_drive_selection)
        self.combo_drives.place(x=470, y=65)

        self.lbl_drive = customtkinter.CTkLabel(self.master_layer, text="TARGET DRIVE:", font=("Courier", 14, "bold"), text_color="#28788b", bg_color="#000000")
        self.lbl_drive.place(x=340, y=65)

        self.console = customtkinter.CTkTextbox(self.master_layer, width=540, height=260, fg_color="#020505", text_color="#00ff41", border_width=1, border_color="#113333", corner_radius=0, font=("Courier", 12))
        self.console.place(x=340, y=110)
        self.console.insert("0.0", ">>> HEXINTEGRITY SYSTEM FORENSICS\n")
        self.console.configure(state="disabled")

        btn_config = {"master": self.master_layer, "width": 105, "height": 35, "fg_color": "transparent", "bg_color": "#000000", "border_width": 1, "corner_radius": 0, "font": ("Courier", 10, "bold")}
        
        self.btn_recover = customtkinter.CTkButton(**btn_config, text="RECOVER", text_color="#6c8b28", border_color="#6c8b28", command=self.recover_data_action)
        self.btn_recover.place(x=340, y=390)
        
        self.btn_delete_file = customtkinter.CTkButton(**btn_config, text="WIPE FILE", text_color="#a31f1f", border_color="#a31f1f", command=self.delete_files_action)
        self.btn_delete_file.place(x=450, y=390)
        
        self.btn_delete_drive = customtkinter.CTkButton(**btn_config, text="WIPE DRIVE", text_color="#a31f1f", border_color="#a31f1f", command=self.delete_drive_action)
        self.btn_delete_drive.place(x=560, y=390)
        
        self.btn_integrity = customtkinter.CTkButton(**btn_config, text="INTEGRITY", text_color="#28788b", border_color="#28788b", command=self.file_integrity_action)
        self.btn_integrity.place(x=670, y=390)

        self.btn_logs = customtkinter.CTkButton(**btn_config, text="LOG ANALYSIS", text_color="#d4af37", border_color="#d4af37", command=self.log_analysis_action)
        self.btn_logs.place(x=780, y=390)

    def _log_drive_selection(self, choice):
        self._log_audit("TARGET_DRIVE_CHANGED", choice)

    def _async_usb_scanner(self):
        while True:
            new_drives = []
            if platform.system() == "Windows":
                import string
                new_drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
            else:
                new_drives = ["/"]
                for mount_dir in ["/mnt", "/media", "/run/media"]:
                    if os.path.exists(mount_dir):
                        try:
                            for entry in os.listdir(mount_dir):
                                if entry not in ["wsl", "wslg"]: 
                                    full_path = os.path.join(mount_dir, entry)
                                    if os.path.isdir(full_path):
                                        new_drives.append(full_path)
                        except Exception as e:
                            self._log_audit("SCAN_MOUNT_WARNING", f"Dir: {mount_dir} - {str(e)}")
            
            self.after(0, lambda d=new_drives: self._update_drives_ui(d))
            time.sleep(3)

    def _update_drives_ui(self, new_drives):
        try:
            current_drives = list(self.combo_drives.cget("values"))
            if "INITIALIZING..." in current_drives:
                self.combo_drives.configure(values=new_drives)
                if new_drives:
                    self.drive_var.set(new_drives[0])
            elif set(new_drives) != set(current_drives):
                added = [d for d in new_drives if d not in current_drives]
                self.combo_drives.configure(values=new_drives)
                if added:
                    for drive in added:
                        self.log_to_console(f"NEW DRIVE DETECTED: {drive}")
                        self._log_audit("DRIVE_DETECTED", drive)
                if self.drive_var.get() not in new_drives and new_drives:
                    self.drive_var.set(new_drives[0])
        except Exception as e:
             self._log_audit("UI_DRIVE_UPDATE_ERROR", str(e))

    def log_to_console(self, text):
        def update_ui():
            self.console.configure(state="normal")
            self.console.insert("end", f">>> {text}\n")
            self.console.see("end")
            self.console.configure(state="disabled")
        self.after(0, update_ui)

    def start_drag(self, event): 
        self._offsetx = event.x
        self._offsety = event.y

    def drag_window(self, event): 
        if platform.system() == "Windows":
            x = self.winfo_pointerx() - self._offsetx
            y = self.winfo_pointery() - self._offsety
            self.geometry(f"+{x}+{y}")

    def minimize_window(self):
        if platform.system() == "Windows":
            self.overrideredirect(False)
        self.iconify()
        self.bind("<Map>", self.restore_window)

    def restore_window(self, event):
        if event.widget is self and self.state() == "normal":
            if platform.system() == "Windows":
                self.overrideredirect(True)
            self.unbind("<Map>")

    def close_application(self): 
        self._log_audit("SESSION_END", "Application terminated by user.")
        try:
            self.quit()
        except:
            pass
        os._exit(0)

    def _safe_dialog(self, func, dialog_window=None, *args, **kwargs):
        if platform.system() != "Windows":
            try:
                if func == filedialog.askdirectory:
                    proc = subprocess.run(['zenity', '--file-selection', '--directory', '--title=SELECT DIRECTORY'], capture_output=True, text=True)
                    return proc.stdout.strip() if proc.returncode == 0 else None
                elif func == filedialog.askopenfilenames:
                    proc = subprocess.run(['zenity', '--file-selection', '--multiple', '--separator=|', '--title=SELECT FILES'], capture_output=True, text=True)
                    return proc.stdout.strip().split('|') if proc.returncode == 0 and proc.stdout else ""
                elif func == filedialog.askopenfilename:
                    proc = subprocess.run(['zenity', '--file-selection', '--title=SELECT FILE'], capture_output=True, text=True)
                    return proc.stdout.strip() if proc.returncode == 0 else None
            except FileNotFoundError:
                self.log_to_console("ERROR: Install Zenity on Linux -> sudo apt install zenity")
                self._log_audit("DIALOG_ERROR", "Zenity not found.")
                return None
            except Exception as e:
                self.log_to_console(f"DIALOG ERROR: {str(e)}")
                self._log_audit("DIALOG_ERROR", str(e))
                return None
        else:
            kwargs['parent'] = dialog_window if dialog_window else self
            try:
                res = func(*args, **kwargs)
            except Exception as e:
                self._log_audit("WINDOWS_DIALOG_ERROR", str(e))
                res = None
            return res

    def _create_popup(self, title, width=500, height=200):
        dialog = Toplevel(self)
        dialog.title(title)
        dialog.geometry(f"{width}x{height}")
        dialog.configure(bg="#000000")
        dialog.resizable(False, False)
        
        if platform.system() == "Windows":
            dialog.transient(self)
            dialog.attributes("-topmost", True)
            
        self._apply_window_icon(dialog)
        x = self.winfo_x() + (self.winfo_width() // 2) - (width // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (height // 2)
        dialog.geometry(f"+{x}+{y}")
        return dialog

    def _staged_execution_menu(self, title, label_text, color, func_target, needs_file=False):
        dialog = self._create_popup(title, width=550, height=250)
        dialog.stage_src = None
        dialog.stage_dst = None
        
        customtkinter.CTkLabel(dialog, text=label_text, font=("Courier", 14, "bold"), text_color=color).pack(pady=10)
        lbl_s = customtkinter.CTkLabel(dialog, text="TARGET: [NOT SELECTED]", font=("Courier", 10), text_color="#aaaaaa")
        lbl_s.pack(pady=5)
        lbl_d = customtkinter.CTkLabel(dialog, text="DEST:   [NOT SELECTED]", font=("Courier", 10), text_color="#aaaaaa")
        lbl_d.pack(pady=5)
        
        def sel_src():
            p = self._safe_dialog(filedialog.askopenfilename if needs_file else filedialog.askdirectory, dialog_window=dialog)
            if p:
                dialog.stage_src = p
                lbl_s.configure(text=f"TARGET: {os.path.basename(p)}", text_color="#00ff00")
                self._log_audit("MENU_SELECTION", f"Target selected: {p}")
                
        def sel_dst():
            p = self._safe_dialog(filedialog.askdirectory, dialog_window=dialog)
            if p:
                dialog.stage_dst = p
                lbl_d.configure(text=f"DEST:   {os.path.basename(p)}", text_color="#00ff00")
                self._log_audit("MENU_SELECTION", f"Destination selected: {p}")
                
        def execute():
            if dialog.stage_src and dialog.stage_dst:
                src = dialog.stage_src
                dst = dialog.stage_dst
                dialog.destroy()
                self._log_audit("MENU_EXECUTION", f"Initiating {title} from {src} to {dst}")
                threading.Thread(target=func_target, args=(src, dst), daemon=True).start()
            else:
                self.log_to_console("ERROR: MUST SELECT BOTH PATHS.")
                self._log_audit("MENU_WARNING", f"Execution failed: missing paths in {title}")
                
        f = customtkinter.CTkFrame(dialog, fg_color="transparent")
        f.pack(pady=15)
        customtkinter.CTkButton(f, text="1. SELECT TARGET", command=sel_src, width=120, fg_color="#000000", border_color=color, border_width=1).pack(side="left", padx=5)
        customtkinter.CTkButton(f, text="2. SELECT DEST", command=sel_dst, width=120, fg_color="#000000", border_color=color, border_width=1).pack(side="left", padx=5)
        customtkinter.CTkButton(f, text="3. EXECUTE", command=execute, width=100, fg_color="#000000", border_color="#00ff00", border_width=1, text_color="#00ff00").pack(side="left", padx=5)

    def file_integrity_action(self):
        self._log_audit("ACTION_CLICK", "File Integrity Hashing opened")
        self._staged_execution_menu("PROTOCOL: INTEGRITY", "FILE INTEGRITY HASHING", "#28788b", self._integrity_engine, needs_file=True)

    def _integrity_engine(self, path, save_dir):
        try:
            filename = os.path.basename(path)
            h_sha256 = hashlib.sha256()
            file_size = os.path.getsize(path)
            processed = 0
            
            self.log_to_console(f"CALCULATING SHA256 FOR: {filename}")
            
            with open(path, "rb") as f:
                while chunk := f.read(8192):
                    h_sha256.update(chunk)
                    processed += len(chunk)
                    if random.randint(1, 1000) == 1: 
                        percent = (processed / file_size) * 100
                        self.log_to_console(f"HASHING PROGRESS: {percent:.1f}%")
            
            final_hash = h_sha256.hexdigest()
            report_path = os.path.join(save_dir, f"HEX_REPORT_{random.randint(1000,9999)}.txt")
            with open(report_path, "w") as rep:
                rep.write(f"HEXINTEGRITY FORENSIC REPORT\nTARGET: {filename}\nSHA256: {final_hash}\nDATE: {datetime.datetime.now()}")
            
            self.log_to_console(f"INTEGRITY SEALED: {os.path.basename(report_path)}")
            self.log_to_console("HASHING COMPLETE 100%")
            self._log_audit("INTEGRITY_SUCCESS", f"File: {path} | Hash: {final_hash}")
            
        except Exception as e:
            self.log_to_console(f"INTEGRITY ERROR: {str(e)}")
            self._log_audit("INTEGRITY_ERROR", f"File: {path} | Error: {str(e)}")

    def recover_data_action(self):
        self._log_audit("ACTION_CLICK", "Recovery Menu opened")
        dialog = self._create_popup("PROTOCOL: RECOVERY", width=400, height=180)
        customtkinter.CTkLabel(dialog, text="RECOVERY MODE", font=("Courier", 14, "bold"), text_color="#28788b", bg_color="#000000").pack(pady=20)
        
        def launch_logical():
            dialog.destroy()
            self._log_audit("RECOVERY_SELECT", "Logical mode selected")
            self._staged_execution_menu("LOGICAL RECOVERY", "LOGICAL SCAN CONFIGURATION", "#28788b", self._logical_recovery_engine, needs_file=False)

        def launch_raw():
            dialog.destroy()
            self._log_audit("RECOVERY_SELECT", "RAW Carving mode selected")
            dst = self._safe_dialog(filedialog.askdirectory, dialog_window=None)
            if dst:
                self._log_audit("RAW_EXECUTION", f"Initiating RAW carve on {self.drive_var.get()} saving to {dst}")
                threading.Thread(target=self._raw_recovery_engine, args=(self.drive_var.get(), dst), daemon=True).start()

        f = customtkinter.CTkFrame(dialog, fg_color="transparent")
        f.pack(pady=10)
        customtkinter.CTkButton(f, text="LOGICAL", command=launch_logical, width=100, fg_color="#000000", border_color="#28788b", border_width=1).pack(side="left", padx=10)
        customtkinter.CTkButton(f, text="RAW", command=launch_raw, width=100, fg_color="#000000", border_color="#6c8b28", border_width=1, text_color="#00ff00").pack(side="right", padx=10)

    def _logical_recovery_engine(self, source, dest):
        self.log_to_console(f"LOGICAL SCAN START: {source}")
        self._log_audit("LOGICAL_SCAN_START", f"Source: {source} | Dest: {dest}")
        count = 0
        error_count = 0
        try:
            for root, _, files in os.walk(source):
                for file in files:
                    src_file = os.path.join(root, file)
                    try:
                        shutil.copy2(src_file, dest)
                        count += 1
                        if count % 100 == 0:
                            self.log_to_console(f"PROGRESS: {count} FILES SECURED...")
                    except PermissionError:
                        self.log_to_console(f"[WARNING] ACCESS DENIED: {src_file}")
                        self._log_audit("LOGICAL_PERMISSION_DENIED", src_file)
                        error_count += 1
                    except Exception as e:
                         self._log_audit("LOGICAL_COPY_ERROR", f"File: {src_file} | Error: {str(e)}")
                         error_count += 1
                         
            self.log_to_console(f"LOGICAL COMPLETE: {count} SECURED | {error_count} SKIPPED.")
            self._log_audit("LOGICAL_SCAN_COMPLETE", f"Secured: {count} | Skipped: {error_count}")
        except Exception as e:
            self.log_to_console(f"RECOVERY FAULT: {str(e)}")
            self._log_audit("LOGICAL_SCAN_CRITICAL_ERROR", str(e))

    def _get_raw_block_device(self, logical_path):
        if platform.system() == "Windows":
            return f"\\\\.\\{logical_path[0]}:"
        else:
            try:
                out = subprocess.check_output(['findmnt', '-n', '-o', 'SOURCE', logical_path]).decode().strip()
                return out if out else logical_path
            except Exception as e:
                self._log_audit("FINDMNT_ERROR", str(e))
                return logical_path

    def _raw_recovery_engine(self, drive, save_dir):
        raw_path = self._get_raw_block_device(drive)
        self.log_to_console(f"RAW CARVING INITIATED ON: {raw_path}")
        self._log_audit("RAW_ENGINE_START", f"Device: {raw_path}")
        chunk_size = 1024 * 1024
        
        signatures = {
            "jpg": {"head": b'\xff\xd8\xff', "foot": b'\xff\xd9'},
            "pdf": {"head": b'%PDF-', "foot": b'%%EOF'},
            "png": {"head": b'\x89PNG\r\n\x1a\n', "foot": b'IEND\xaeB`\x82'},
            "zip_docx": {"head": b'PK\x03\x04', "foot": b'PK\x05\x06'}
        }
        
        try:
            if platform.system() == "Windows":
                f = open(raw_path, 'rb')
            else:
                proc = subprocess.Popen(['sudo', 'dd', f'if={raw_path}', 'bs=1M', 'count=500'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                f = proc.stdout

            carving_state = None 
            file_count = {"jpg": 0, "pdf": 0, "png": 0, "zip_docx": 0}
            buffer = b''
            mb_read = 0
            
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                buffer += chunk
                mb_read += 1
                
                if mb_read % 50 == 0:
                    self.log_to_console(f"RAW PROGRESS: {mb_read} MB ANALYZED...")
                
                while True:
                    if not carving_state:
                        earliest_idx = -1
                        found_type = None
                        
                        for ext, sigs in signatures.items():
                            idx = buffer.find(sigs["head"])
                            if idx != -1 and (earliest_idx == -1 or idx < earliest_idx):
                                earliest_idx = idx
                                found_type = ext
                        
                        if earliest_idx == -1:
                            buffer = buffer[-20:] 
                            break
                        
                        carving_state = found_type
                        buffer = buffer[earliest_idx:]
                        
                    if carving_state:
                        foot_sig = signatures[carving_state]["foot"]
                        end_idx = buffer.find(foot_sig)
                        
                        if end_idx == -1:
                            if len(buffer) > 20 * 1024 * 1024: 
                                self._log_audit("RAW_CARVE_ABORT", f"File size limit exceeded for {carving_state}")
                                carving_state = None
                                buffer = buffer[len(signatures[carving_state]["head"]):] if carving_state else buffer[20:]
                            break
                        else:
                            file_count[carving_state] += 1
                            ext_map = {"zip_docx": "zip"}
                            final_ext = ext_map.get(carving_state, carving_state)
                            out_path = os.path.join(save_dir, f"CARVED_{carving_state.upper()}_{random.randint(1000,9999)}.{final_ext}")
                            
                            try:
                                with open(out_path, 'wb') as out:
                                    out.write(buffer[:end_idx + len(foot_sig)])
                                self.log_to_console(f"CARVED [{carving_state.upper()}]: {os.path.basename(out_path)}")
                            except Exception as e:
                                self._log_audit("RAW_WRITE_ERROR", str(e))
                                
                            buffer = buffer[end_idx + len(foot_sig):]
                            carving_state = None
                            
            total_recovered = sum(file_count.values())
            self.log_to_console(f"RAW ANALYSIS TERMINATED. {total_recovered} FILES RECOVERED.")
            self._log_audit("RAW_ENGINE_COMPLETE", f"Recovered: {file_count}")
            
        except PermissionError:
            self.log_to_console("[CRITICAL] ADMIN/ROOT PRIVILEGES REQUIRED FOR RAW BLOCK ACCESS.")
            self._log_audit("RAW_ERROR", "Permission Denied for Block Device")
        except Exception as e:
            self.log_to_console(f"RAW CARVE ERROR: {str(e)}")
            self._log_audit("RAW_CRITICAL_ERROR", str(e))

    def delete_files_action(self):
        self._log_audit("ACTION_CLICK", "Wipe File opened")
        targets = self._safe_dialog(filedialog.askopenfilenames, dialog_window=None)
        if targets:
            threading.Thread(target=lambda: [self._secure_wipe(f) for f in targets], daemon=True).start()

    def _secure_wipe(self, path):
        self._log_audit("WIPE_FILE_INIT", path)
        try:
            size = os.path.getsize(path)
            self.log_to_console(f"WIPING ({size} bytes): {os.path.basename(path)}")
            
            with open(path, "ba+", buffering=0) as f:
                for pass_num in range(1, 4):
                    f.seek(0)
                    f.write(os.urandom(size))
                    self.log_to_console(f"  -> PASS {pass_num}/3 COMPLETE")
            os.remove(path)
            self.log_to_console(f"FILE PURGED AND UNLINKED: {os.path.basename(path)}")
            self._log_audit("WIPE_FILE_SUCCESS", path)
        except PermissionError:
            self.log_to_console(f"[WARNING] WIPE FAILED (IN USE OR LOCKED): {os.path.basename(path)}")
            self._log_audit("WIPE_FILE_DENIED", path)
        except Exception as e:
            self.log_to_console(f"WIPE ERROR: {str(e)}")
            self._log_audit("WIPE_FILE_ERROR", f"{path} - {str(e)}")

    def delete_drive_action(self):
        self._log_audit("ACTION_CLICK", "Wipe Drive opened")
        drive = self.drive_var.get()
        sys_drive = os.environ.get('SystemDrive', 'C:') + '\\'
        
        if platform.system() == "Windows" and drive.startswith(sys_drive):
            self.log_to_console("[CRITICAL] CANNOT WIPE SYSTEM OS DRIVE.")
            self._log_audit("WIPE_DRIVE_BLOCKED", "Attempted to wipe system drive")
            return
        if platform.system() != "Windows" and drive == "/":
            self.log_to_console("[CRITICAL] CANNOT WIPE ROOT (/) OS DIRECTORY.")
            self._log_audit("WIPE_DRIVE_BLOCKED", "Attempted to wipe root directory")
            return

        dialog = self._create_popup("PROTOCOL: ANNIHILATION", width=400, height=180)
        customtkinter.CTkLabel(dialog, text=f"WIPE DRIVE {drive}?", text_color="#a31f1f", bg_color="#000000", font=("Courier", 12, "bold")).pack(pady=20)
        
        def confirm():
            dialog.destroy()
            self._log_audit("WIPE_DRIVE_CONFIRMED", drive)
            threading.Thread(target=self._drive_wipe_engine, args=(drive,), daemon=True).start()
            
        customtkinter.CTkButton(dialog, text="CONFIRM DESTRUCTION", fg_color="#000000", border_color="#a31f1f", border_width=1, text_color="#a31f1f", command=confirm).pack(pady=10)

    def _drive_wipe_engine(self, drive):
        self.log_to_console(f"INITIATING FORENSIC WIPE ON: {drive}")
        self.log_to_console("PHASE 1: LOGICAL DESTRUCTION...")
        files_wiped = 0
        dirs_removed = 0
        try:
            for root, dirs, files in os.walk(drive, topdown=False):
                for name in files:
                    try:
                        file_path = os.path.join(root, name)
                        size = os.path.getsize(file_path)
                        with open(file_path, "ba+", buffering=0) as f:
                            f.seek(0)
                            f.write(os.urandom(size))
                        os.remove(file_path)
                        files_wiped += 1
                        if files_wiped % 500 == 0:
                            self.log_to_console(f"  -> {files_wiped} FILES OVERWRITTEN...")
                    except PermissionError:
                         self._log_audit("WIPE_DRIVE_FILE_DENIED", file_path)
                    except Exception:
                        pass
                for name in dirs:
                    try:
                        os.rmdir(os.path.join(root, name))
                        dirs_removed += 1
                    except Exception:
                        pass
            
            self._log_audit("WIPE_DRIVE_PHASE_1", f"Files wiped: {files_wiped}, Dirs removed: {dirs_removed}")
            self.log_to_console("PHASE 2: OVERWRITING FREE SPACE (ALLOCATION)...")
            wipe_file = os.path.join(drive, f"HEX_ZERO_{random.randint(1000,9999)}.tmp")
            gb_written = 0
            
            try:
                with open(wipe_file, 'wb') as f:
                    chunk = os.urandom(1024 * 1024 * 10) 
                    while True:
                        f.write(chunk)
                        gb_written += 10
                        if gb_written % 1000 == 0:
                             self.log_to_console(f"  -> {gb_written // 1000} GB FREE SPACE OVERWRITTEN...")
            except OSError as e:
                if e.errno == 28: 
                    self.log_to_console("  -> FREE SPACE SATURATED 100%")
                    self._log_audit("WIPE_DRIVE_PHASE_2", "Free space filled successfully")
                else:
                    self._log_audit("WIPE_DRIVE_PHASE_2_ERROR", str(e))
            try:
                os.remove(wipe_file)
            except Exception as e:
                 self._log_audit("WIPE_DRIVE_CLEANUP_ERROR", str(e))
            
            self.log_to_console(f"VOLUME {drive} SECURELY SANITIZED.")
            self._log_audit("WIPE_DRIVE_COMPLETE", drive)
        except Exception as e:
            self.log_to_console(f"WIPE ERROR: {str(e)}")
            self._log_audit("WIPE_DRIVE_CRITICAL_ERROR", str(e))

    def log_analysis_action(self):
        self._log_audit("ACTION_CLICK", "Log Analysis Menu opened")
        dialog = self._create_popup("PROTOCOL: LOG ANALYSIS", width=400, height=180)
        customtkinter.CTkLabel(dialog, text="SELECT ANALYSIS MODE", text_color="#d4af37", bg_color="#000000", font=("Courier", 12, "bold")).pack(pady=20)
        
        def folder_mode():
            dialog.destroy()
            self._log_audit("LOG_ANALYSIS_SELECT", "Folder Mode")
            self._staged_execution_menu("FOLDER LOG ANALYSIS", "SELECT LOG SOURCE & DESTINATION", "#d4af37", lambda s, d: self._log_engine(s, d, "FOLDER"), needs_file=False)

        def drive_mode():
            dialog.destroy()
            self._log_audit("LOG_ANALYSIS_SELECT", "Drive Mode")
            dst = self._safe_dialog(filedialog.askdirectory, dialog_window=None)
            if dst:
                self._log_audit("LOG_EXECUTION", f"Initiating Drive Log scan on {self.drive_var.get()} saving to {dst}")
                threading.Thread(target=self._log_engine, args=(self.drive_var.get(), dst, "DRIVE"), daemon=True).start()

        f = customtkinter.CTkFrame(dialog, fg_color="transparent")
        f.pack(pady=10)
        customtkinter.CTkButton(f, text="FOLDER SCAN", command=folder_mode, fg_color="#000000", border_color="#d4af37", border_width=1, text_color="#d4af37").pack(side="left", padx=10)
        customtkinter.CTkButton(f, text="FULL DRIVE", command=drive_mode, fg_color="#000000", border_color="#a31f1f", border_width=1, text_color="#a31f1f").pack(side="right", padx=10)

    def _log_engine(self, source, save_dir, mode):
        self.log_to_console(f"LOG ANALYSIS START: {mode} MODE ON {source}")
        patterns = {
            "IPv4": re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
            "Email": re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'),
            "Critical/Error": re.compile(r'(?i)\b(error|critical|failed|fatal|exception)\b'),
            "Auth/Password": re.compile(r'(?i)\b(password|passwd|pwd|login|unauthorized)\b')
        }
        report_path = os.path.join(save_dir, f"HEX_LOG_REPORT_{random.randint(1000,9999)}.txt")
        findings_count = {k: 0 for k in patterns}
        files_scanned = 0
        
        try:
            with open(report_path, "w", encoding="utf-8") as rep:
                rep.write(f"HEXINTEGRITY LOG ANALYSIS REPORT\nSOURCE: {source}\nDATE: {datetime.datetime.now()}\n{'='*50}\n\n")
                for root, _, files in os.walk(source):
                    for file in files:
                        if file.endswith(('.txt', '.log', '.csv', '.xml', '.json', '.ini', '.conf')):
                            file_path = os.path.join(root, file)
                            files_scanned += 1
                            if files_scanned % 50 == 0:
                                self.log_to_console(f"SCANNING LOG FILES: {files_scanned} PROCESSED...")
                            try:
                                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                                    content = f.read()
                                    for category, regex in patterns.items():
                                        matches = set(regex.findall(content))
                                        if matches:
                                            rep.write(f"[{category}] IN FILE: {file_path}\n")
                                            for match in matches:
                                                rep.write(f"  -> {match}\n")
                                            findings_count[category] += len(matches)
                                            rep.write("\n")
                            except PermissionError:
                                 self._log_audit("LOG_SCAN_DENIED", file_path)
                            except Exception as e:
                                 self._log_audit("LOG_SCAN_ERROR", f"{file_path} - {str(e)}")
                                 
                rep.write(f"\n{'='*50}\nSUMMARY OF FINDINGS:\n")
                for k, v in findings_count.items():
                    rep.write(f"{k}: {v} unique matches\n")
                    
            self.log_to_console(f"ANALYSIS COMPLETE. REPORT SAVED: {os.path.basename(report_path)}")
            self._log_audit("LOG_ANALYSIS_COMPLETE", f"Files Scanned: {files_scanned} | Findings: {findings_count}")
        except Exception as e:
            self.log_to_console(f"LOG ANALYSIS ERROR: {str(e)}")
            self._log_audit("LOG_ANALYSIS_CRITICAL_ERROR", str(e))

if __name__ == "__main__":
    if platform.system() == "Windows":
        if not getattr(sys, 'frozen', False):
            exe_name = "HexIntegrity_forensics.exe"
            if not os.path.exists(exe_name):
                print("\n>>> [HEXINTEGRITY] INITIATING AUTO-ASSEMBLY FUNCTION...")
                print(">>> [1/3] Installing dependencies in the background...")
                subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller", "customtkinter", "pillow"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(">>> [2/3] Compiling forensic engine (Please wait 1-2 minutes)...")
                script_path = os.path.abspath(sys.argv[0])
                
                build_cmd = [
                    sys.executable, "-m", "PyInstaller", 
                    "--noconfirm", "--noconsole", "--onefile"
                ]
                
                if os.path.exists("icono.ico"):
                    build_cmd.append("--icon=icono.ico")
                    
                for res in ["icono.ico", "icono.png", "interfaz_win.png", "interfaz_lin.png", "btn_min_off.png", "btn_min_on.png", "btn_cerrar_off.png", "btn_cerrar_on.png"]:
                    if os.path.exists(res):
                        build_cmd.extend(["--add-data", f"{res};."])
                        
                build_cmd.append(script_path)
                
                proc = subprocess.run(build_cmd, capture_output=True, text=True)
                
                if proc.returncode != 0:
                    print("\n>>> [CRITICAL] COMPILATION FAILED. REASON:")
                    print(proc.stderr)
                    sys.exit(1)
                    
                print(">>> [3/3] Extracting final executable and cleaning up traces...")
                try:
                    compiled_file = os.path.join("dist", os.path.basename(script_path).replace(".py", ".exe"))
                    if os.path.exists(compiled_file):
                        shutil.move(compiled_file, exe_name)
                    shutil.rmtree("build", ignore_errors=True)
                    shutil.rmtree("dist", ignore_errors=True)
                    spec_file = os.path.basename(script_path).replace(".py", ".spec")
                    if os.path.exists(spec_file):
                        os.remove(spec_file)
                except Exception:
                    pass
                print("\n=========================================================")
                print(f" COMPILATION FINISHED: {exe_name} HAS BEEN CREATED")
                print(" -> CLOSE THIS TERMINAL AND DOUBLE CLICK THE .EXE")
                print("=========================================================\n")
                sys.exit(0)

        try:
            if not ctypes.windll.shell32.IsUserAnAdmin():
                if getattr(sys, 'frozen', False):
                    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv[1:]), None, 1)
                else:
                    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{sys.argv[0]}"', None, 1)
                sys.exit()
        except Exception: 
            pass

    app = HexIntegrityApp()
    app.mainloop()