import customtkinter as ctk
import tkinter as tk
import threading
from tkinter import filedialog, messagebox, Menu
import os
import steganography
from PIL import Image, ImageTk, ImageOps

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SideBarButton(ctk.CTkButton):
    def __init__(self, master, **kwargs):
        super().__init__(master, 
                         height=40, 
                         corner_radius=8, 
                         border_spacing=10, 
                         fg_color="transparent", 
                         text_color=("gray10", "gray90"), 
                         hover_color=("gray70", "gray30"),
                         anchor="w",
                         font=ctk.CTkFont(size=14, weight="bold"),
                         **kwargs)

class SteganoGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("StegoCrypt Pro")
        self.geometry("900x600")
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # UI state
        self.encode_path = None
        self.decode_path = None
        self.max_capacity_lsb = 0
        self.max_capacity_dct = 0

        self.setup_sidebar()
        self.setup_main_frames()
        
        self.select_frame_by_name("encode")

    def setup_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="STEGO\nCRYPT", 
                                      font=ctk.CTkFont(size=24, weight="bold"),
                                      text_color="#3B8ED0")
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 40))

        self.btn_encode = SideBarButton(self.sidebar_frame, text="Приховати", 
                                       command=lambda: self.select_frame_by_name("encode"))
        self.btn_encode.grid(row=1, column=0, padx=20, pady=5, sticky="ew")

        self.btn_decode = SideBarButton(self.sidebar_frame, text="Прочитати", 
                                       command=lambda: self.select_frame_by_name("decode"))
        self.btn_decode.grid(row=2, column=0, padx=20, pady=5, sticky="ew")

        self.method_var = ctk.StringVar(value="EOF (Без втрат)")
        self.method_label = ctk.CTkLabel(self.sidebar_frame, text="Метод стеганографії:", anchor="w", text_color="gray70")
        self.method_label.grid(row=3, column=0, padx=20, pady=(20, 0), sticky="w")
        
        self.method_seg = ctk.CTkSegmentedButton(self.sidebar_frame, values=["LSB (Класичний)", "EOF (Без втрат)", "DCT (Частотний)"], variable=self.method_var, command=self.update_char_counter)
        self.method_seg.grid(row=4, column=0, padx=20, pady=(5, 0), sticky="ew")

        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Тема:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Dark", "Light", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 20))

    def setup_main_frames(self):
        # Encode Frame
        self.encode_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.encode_frame.grid_columnconfigure(0, weight=1)
        self.encode_frame.grid_rowconfigure(2, weight=1)
        self.enc_header = ctk.CTkLabel(self.encode_frame, text="Приховати повідомлення", 
                                      font=ctk.CTkFont(size=20, weight="bold"))
        self.enc_header.grid(row=0, column=0, padx=30, pady=(30, 20), sticky="w")

        self.enc_top_container = ctk.CTkFrame(self.encode_frame, fg_color="gray15", corner_radius=15)
        self.enc_top_container.grid(row=1, column=0, padx=30, pady=10, sticky="ew")
        
        self.enc_btn_select = ctk.CTkButton(self.enc_top_container, text="Оберіть файл", 
                                           command=self.select_encode_image, 
                                           width=150, height=40, corner_radius=10)
        self.enc_btn_select.pack(side="left", padx=20, pady=20)

        self.enc_info_lbl = ctk.CTkLabel(self.enc_top_container, text="Файл не обрано", text_color="gray50")
        self.enc_info_lbl.pack(side="left", padx=10)
        
        self.enc_capacity_lbl = ctk.CTkLabel(self.enc_top_container, text="", text_color="#3B8ED0", font=ctk.CTkFont(size=12, weight="bold"))
        self.enc_capacity_lbl.pack(side="left", padx=15)

        self.enc_preview_label = ctk.CTkLabel(self.enc_top_container, text="", width=100, height=60)
        self.enc_preview_label.pack(side="right", padx=20)

        self.enc_msg_container = ctk.CTkFrame(self.encode_frame, fg_color="transparent")
        self.enc_msg_container.grid(row=2, column=0, padx=30, pady=10, sticky="nsew")
        self.enc_msg_container.grid_columnconfigure(0, weight=1)
        self.enc_msg_container.grid_rowconfigure(1, weight=1)

        self.enc_msg_header_frame = ctk.CTkFrame(self.enc_msg_container, fg_color="transparent")
        self.enc_msg_header_frame.grid(row=0, column=0, sticky="ew", pady=(5, 5))
        
        ctk.CTkLabel(self.enc_msg_header_frame, text="Ваше секретне повідомлення:", font=ctk.CTkFont(size=13)).pack(side="left")
        self.enc_char_counter = ctk.CTkLabel(self.enc_msg_header_frame, text="0 символів", font=ctk.CTkFont(size=11), text_color="gray50")
        self.enc_char_counter.pack(side="right")
        
        self.enc_textbox = ctk.CTkTextbox(self.enc_msg_container, corner_radius=10, border_width=1, border_color="gray30")
        self.enc_textbox.grid(row=1, column=0, sticky="nsew")
        self.enc_textbox.bind("<KeyRelease>", self.update_char_counter)
        self.apply_context_menu(self.enc_textbox)

        self.enc_go_btn = ctk.CTkButton(self.encode_frame, text="ЗАШИФРУВАТИ ТА ЗБЕРЕГТИ", 
                                       command=self.run_encode, height=50, corner_radius=10,
                                       font=ctk.CTkFont(size=14, weight="bold"),
                                       fg_color="#3B8ED0", hover_color="#2B6EA0")
        self.enc_go_btn.grid(row=3, column=0, padx=30, pady=30, sticky="ew")

        # Decode Frame
        self.decode_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.decode_frame.grid_columnconfigure(0, weight=1)
        self.decode_frame.grid_rowconfigure(2, weight=1)

        self.dec_header = ctk.CTkLabel(self.decode_frame, text="Прочитати приховане повідомлення", 
                                      font=ctk.CTkFont(size=20, weight="bold"))
        self.dec_header.grid(row=0, column=0, padx=30, pady=(30, 20), sticky="w")

        self.dec_top_container = ctk.CTkFrame(self.decode_frame, fg_color="gray15", corner_radius=15)
        self.dec_top_container.grid(row=1, column=0, padx=30, pady=10, sticky="ew")

        self.dec_btn_select = ctk.CTkButton(self.dec_top_container, text="Оберіть файл", 
                                           command=self.select_decode_image, 
                                           width=150, height=40, corner_radius=10)
        self.dec_btn_select.pack(side="left", padx=20, pady=20)
        
        self.dec_lbl_path = ctk.CTkLabel(self.dec_top_container, text="Файл не обрано", text_color="gray50")
        self.dec_lbl_path.pack(side="left", padx=10)

        self.dec_preview_label = ctk.CTkLabel(self.dec_top_container, text="", width=100, height=60)
        self.dec_preview_label.pack(side="right", padx=20)

        self.dec_msg_container = ctk.CTkFrame(self.decode_frame, fg_color="transparent")
        self.dec_msg_container.grid(row=2, column=0, padx=30, pady=10, sticky="nsew")
        self.dec_msg_container.grid_columnconfigure(0, weight=1)
        self.dec_msg_container.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.dec_msg_container, text="Знайдений текст:", font=ctk.CTkFont(size=13)).grid(row=0, column=0, sticky="w", pady=(5, 5))
        
        self.dec_textbox = ctk.CTkTextbox(self.dec_msg_container, corner_radius=10, border_width=1, border_color="gray30")
        self.dec_textbox.grid(row=1, column=0, sticky="nsew")
        self.dec_textbox.configure(state="disabled")
        self.apply_context_menu(self.dec_textbox)

        self.dec_go_btn = ctk.CTkButton(self.decode_frame, text="РОЗШИФРУВАТИ", 
                                       command=self.run_decode, height=50, corner_radius=10,
                                       font=ctk.CTkFont(size=14, weight="bold"),
                                       fg_color="#24A148", hover_color="#1B7A36")
        self.dec_go_btn.grid(row=3, column=0, padx=30, pady=30, sticky="ew")

    def select_frame_by_name(self, name):
        self.btn_encode.configure(fg_color=("gray75", "gray25") if name == "encode" else "transparent")
        self.btn_decode.configure(fg_color=("gray75", "gray25") if name == "decode" else "transparent")

        self.encode_frame.grid_forget()
        self.decode_frame.grid_forget()

        if name == "encode":
            self.encode_frame.grid(row=0, column=1, sticky="nsew")
        elif name == "decode":
            self.decode_frame.grid(row=0, column=1, sticky="nsew")

    def update_preview(self, path, label_widget):
        try:
            img = Image.open(path)
            img = ImageOps.exif_transpose(img)
            img.thumbnail((120, 120))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
            label_widget.configure(image=ctk_img, text="")
        except:
            label_widget.configure(text="Preview Error", image=None)

    def select_encode_image(self):
        self.select_image("encode")

    def select_decode_image(self):
        self.select_image("decode")

    def select_image(self, target):
        filename = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")])
        if not filename:
            return
            
        if target == "encode":
            self.encode_path = filename
            self.enc_info_lbl.configure(text=os.path.basename(filename), text_color="white")
            self.update_preview(filename, self.enc_preview_label)
            try:
                capacity = steganography.calculate_capacity(filename)
                self.max_capacity_lsb = capacity['max_chars_approx']
                self.max_capacity_dct = capacity.get('freq_max_chars_approx', 0)
                self.update_char_counter()
            except Exception:
                self.enc_capacity_lbl.configure(text="⚠️ Помилка")
        elif target == "decode":
            self.decode_path = filename
            self.dec_lbl_path.configure(text=os.path.basename(filename), text_color="white")
            self.update_preview(filename, self.dec_preview_label)

    def update_char_counter(self, event=None):
        try:
            current_text = self.enc_textbox.get("1.0", "end-1c")
            char_count = len(current_text)
            
            method = self.method_var.get()
            if "EOF" in method:
                self.enc_capacity_lbl.configure(text="📊 Макс: Необмежено (EOF)")
                self.enc_char_counter.configure(text=f"{char_count:,} символів (Безліміт)", text_color="#24A148")
            else:
                max_cap = self.max_capacity_lsb if "LSB" in method else self.max_capacity_dct
                if max_cap > 0:
                    self.enc_capacity_lbl.configure(text=f"📊 Макс: ~{max_cap:,} симв.")
                    percentage = (char_count / max_cap) * 100
                    if percentage > 100:
                        color = "#FF4444"
                    elif percentage > 80:
                        color = "#FFA500"
                    else:
                        color = "#3B8ED0"
                    
                    self.enc_char_counter.configure(
                        text=f"{char_count:,} / ~{max_cap:,} ({percentage:.0f}%)",
                        text_color=color
                    )
                else:
                    self.enc_capacity_lbl.configure(text="")
                    self.enc_char_counter.configure(text=f"{char_count:,} символів")
        except Exception:
            pass

    def apply_context_menu(self, widget):
        menu = Menu(self, tearoff=0, bg="#2b2b2b", fg="white", activebackground="#3B8ED0")
        menu.add_command(label="Копіювати", command=lambda: self.copy_text(widget))
        menu.add_command(label="Вставити", command=lambda: self.paste_text(widget))
        menu.add_command(label="Вирізати", command=lambda: self.cut_text(widget))
        menu.add_separator()
        menu.add_command(label="Виділити все", command=lambda: self.select_all(widget))

        def show_menu(event):
            menu.tk_popup(event.x_root, event.y_root)

        widget.bind("<Button-3>", show_menu)
        
        def handle_ctrl_keys(event):
            try:
                k = str(event.keysym).lower()
                if k in ('v', 'м', 'm', 'v'):  
                    return self.paste_text(widget, event)
                elif k in ('c', 'с'):
                    return self.copy_text(widget, event)
                elif k in ('x', 'х'):
                    return self.cut_text(widget, event)
                elif k in ('a', 'а'):
                    return self.select_all(widget, event)
            except Exception:
                pass
            return None

        widget.bind("<Control-KeyPress>", handle_ctrl_keys)

    def copy_text(self, widget, event=None):
        try:
            text = widget.get("sel.first", "sel.last")
            self.clipboard_clear()
            self.clipboard_append(text)
        except Exception:
            pass
        return "break" if event else None

    def paste_text(self, widget, event=None):
        if widget.cget("state") == "disabled":
            return "break" if event else None
        try:
            text = self.clipboard_get()
            try:
                widget.delete("sel.first", "sel.last")
            except Exception:
                pass
            widget.insert("insert", text)
            self.update_char_counter()
        except Exception:
            pass
        return "break" if event else None

    def cut_text(self, widget, event=None):
        if widget.cget("state") == "disabled":
            return "break" if event else None
        try:
            self.copy_text(widget)
            try:
                widget.delete("sel.first", "sel.last")
            except Exception:
                pass
            self.update_char_counter()
        except Exception:
            pass
        return "break" if event else None

    def select_all(self, widget, event=None):
        try:
            widget.tag_add("sel", "1.0", "end")
        except Exception:
            pass
        return "break" if event else None

    def run_encode(self):
        if not self.encode_path:
            messagebox.showerror("Error", "Оберіть зображення!")
            return
        
        msg = self.enc_textbox.get("1.0", "end-1c").strip()
        if not msg:
            messagebox.showerror("Error", "Введіть текст!")
            return
        
        method = self.method_var.get()
        orig_name, orig_ext = os.path.splitext(os.path.basename(self.encode_path))
        orig_ext_lower = orig_ext.lower()
        
        if "EOF" in method:
            default_ext = orig_ext if orig_ext else ".png"
            out_path = filedialog.asksaveasfilename(
                initialfile=f"{orig_name}_secret{default_ext}",
                defaultextension=default_ext, 
                filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp"), ("All Files", "*.*")]
            )
        elif "DCT" in method:
            default_ext = orig_ext if orig_ext_lower in [".png", ".jpg", ".jpeg", ".bmp"] else ".png"
            file_types = [("PNG Image", "*.png"), ("JPEG Image", "*.jpg;*.jpeg"), ("BMP Image", "*.bmp")]
            if default_ext in [".jpg", ".jpeg"]:
                file_types.insert(0, file_types.pop(1))
            elif default_ext == ".bmp":
                file_types.insert(0, file_types.pop(2))
                
            out_path = filedialog.asksaveasfilename(
                initialfile=f"{orig_name}_stego{default_ext}",
                defaultextension=default_ext, 
                filetypes=file_types
            )
        else: # LSB
            default_ext = orig_ext if orig_ext_lower in [".png", ".bmp"] else ".png"
            file_types = [("PNG Image", "*.png"), ("BMP Image", "*.bmp")]
            if default_ext == ".bmp":
                file_types.insert(0, file_types.pop(1))
                
            out_path = filedialog.asksaveasfilename(
                initialfile=f"{orig_name}_stego{default_ext}",
                defaultextension=default_ext, 
                filetypes=file_types
            )
            
        if out_path:
            self.enc_go_btn.configure(state="disabled", text="Обробка...")
            threading.Thread(target=self._encode_thread, args=(self.encode_path, msg, out_path, method), daemon=True).start()

    def _encode_thread(self, img_path, msg, out_path, method):
        try:
            if "LSB" in method:
                final_path = steganography.encode_image(img_path, msg, out_path)
            elif "DCT" in method:
                final_path = steganography.encode_image_freq(img_path, msg, out_path)
            else:
                final_path = steganography.encode_image_eof(img_path, msg, out_path)
            self.after(0, lambda: messagebox.showinfo("Success", f"Готово!\nМетод: {method}\nФайл збережено: {final_path}"))
        except Exception as e:
            err_msg = str(e)
            self.after(0, lambda m=err_msg: messagebox.showerror("Error", m))
        finally:
            self.after(0, lambda: self.enc_go_btn.configure(state="normal", text="ЗАШИФРУВАТИ ТА ЗБЕРЕГТИ"))

    def run_decode(self):
        if not self.decode_path:
            messagebox.showerror("Error", "Оберіть зображення!")
            return
        
        self.dec_go_btn.configure(state="disabled", text="Читання...")
        method = self.method_var.get()
        threading.Thread(target=self._decode_thread, args=(self.decode_path, method), daemon=True).start()

    def _decode_thread(self, img_path, method):
        try:
            if "LSB" in method:
                msg = steganography.decode_image(img_path)
            elif "DCT" in method:
                msg = steganography.decode_image_freq(img_path)
            else:
                msg = steganography.decode_image_eof(img_path)
            self.after(0, lambda msg_data=msg: self._update_decode_ui(msg_data, method))
        except Exception as e:
            err_msg = str(e)
            self.after(0, lambda m=err_msg: messagebox.showerror("Error", m))
        finally:
             self.after(0, lambda: self.dec_go_btn.configure(state="normal", text="РОЗШИФРУВАТИ"))

    def _update_decode_ui(self, msg, method):
        self.dec_textbox.configure(state="normal")
        self.dec_textbox.delete("1.0", "end")
        self.dec_textbox.insert("1.0", msg)
        self.dec_textbox.configure(state="disabled")
        
        if "не знайдено" in msg:
            messagebox.showwarning("Warning", f"Прихований текст не знайдено ({method}).")
        else:
            messagebox.showinfo("Success", f"Повідомлення успішно вилучено ({method})!")

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

if __name__ == "__main__":
    app = SteganoGUI()
    app.mainloop()
