import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import steganography
from PIL import Image, ImageTk, ImageOps

# Configuration
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
        
        # Grid layout 1x2
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # UI state
        self.encode_path = None
        self.decode_path = None

        self.setup_sidebar()
        self.setup_main_frames()
        
        # Default view
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

        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Тема:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Dark", "Light", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 20))

    def setup_main_frames(self):
        # --- ENCODE FRAME ---
        self.encode_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.encode_frame.grid_columnconfigure(0, weight=1)
        self.encode_frame.grid_rowconfigure(2, weight=1)

        # Header
        self.enc_header = ctk.CTkLabel(self.encode_frame, text="Приховати повідомлення в зображення", 
                                      font=ctk.CTkFont(size=20, weight="bold"))
        self.enc_header.grid(row=0, column=0, padx=30, pady=(30, 20), sticky="w")

        # Top section (Selection + Preview)
        self.enc_top_container = ctk.CTkFrame(self.encode_frame, fg_color="gray15", corner_radius=15)
        self.enc_top_container.grid(row=1, column=0, padx=30, pady=10, sticky="ew")
        
        self.enc_btn_select = ctk.CTkButton(self.enc_top_container, text="Оберіть файл", 
                                           command=self.select_encode_image, 
                                           width=150, height=40, corner_radius=10)
        self.enc_btn_select.pack(side="left", padx=20, pady=20)

        self.enc_info_lbl = ctk.CTkLabel(self.enc_top_container, text="PNG / JPG / BMP", text_color="gray50")
        self.enc_info_lbl.pack(side="left", padx=10)

        self.enc_preview_label = ctk.CTkLabel(self.enc_top_container, text="", width=100, height=60)
        self.enc_preview_label.pack(side="right", padx=20)

        # Message Section
        self.enc_msg_container = ctk.CTkFrame(self.encode_frame, fg_color="transparent")
        self.enc_msg_container.grid(row=2, column=0, padx=30, pady=10, sticky="nsew")
        self.enc_msg_container.grid_columnconfigure(0, weight=1)
        self.enc_msg_container.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.enc_msg_container, text="Ваше секретне повідомлення:", font=ctk.CTkFont(size=13)).grid(row=0, column=0, sticky="w", pady=(5, 5))
        
        self.enc_textbox = ctk.CTkTextbox(self.enc_msg_container, corner_radius=10, border_width=1, border_color="gray30")
        self.enc_textbox.grid(row=1, column=0, sticky="nsew")

        # Action Button
        self.enc_go_btn = ctk.CTkButton(self.encode_frame, text="ЗАШИФРУВАТИ ТА ЗБЕРЕГТИ", 
                                       command=self.run_encode, height=50, corner_radius=10,
                                       font=ctk.CTkFont(size=14, weight="bold"),
                                       fg_color="#3B8ED0", hover_color="#2B6EA0")
        self.enc_go_btn.grid(row=3, column=0, padx=30, pady=30, sticky="ew")

        # --- DECODE FRAME ---
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

        self.dec_go_btn = ctk.CTkButton(self.decode_frame, text="РОЗШИФРУВАТИ", 
                                       command=self.run_decode, height=50, corner_radius=10,
                                       font=ctk.CTkFont(size=14, weight="bold"),
                                       fg_color="#24A148", hover_color="#1B7A36")
        self.dec_go_btn.grid(row=3, column=0, padx=30, pady=30, sticky="ew")

    def select_frame_by_name(self, name):
        # Update button colors
        self.btn_encode.configure(fg_color=("gray75", "gray25") if name == "encode" else "transparent")
        self.btn_decode.configure(fg_color=("gray75", "gray25") if name == "decode" else "transparent")

        # Show/Hide frames
        if name == "encode":
            self.encode_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.encode_frame.grid_forget()
            
        if name == "decode":
            self.decode_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.decode_frame.grid_forget()

    def update_preview(self, path, label_widget):
        try:
            img = Image.open(path)
            img = ImageOps.exif_transpose(img)
            # Create thumbnail
            img.thumbnail((120, 120))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
            label_widget.configure(image=ctk_img, text="")
        except:
            label_widget.configure(text="Preview Error", image=None)

    def select_encode_image(self):
        filename = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")])
        if filename:
            self.encode_path = filename
            self.enc_info_lbl.configure(text=os.path.basename(filename), text_color="white")
            self.update_preview(filename, self.enc_preview_label)

    def select_decode_image(self):
        filename = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")])
        if filename:
            self.decode_path = filename
            self.update_preview(filename, self.dec_preview_label)

    def run_encode(self):
        if not self.encode_path:
            messagebox.showerror("Error", "Оберіть зображення!")
            return
        
        msg = self.enc_textbox.get("1.0", "end-1c").strip()
        if not msg:
            messagebox.showerror("Error", "Введіть текст!")
            return
        
        out_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png")])
        if out_path:
            try:
                final_path = steganography.encode_image(self.encode_path, msg, out_path)
                messagebox.showinfo("Success", f"Готово!\nФайл збережено: {final_path}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def run_decode(self):
        if not self.decode_path:
            messagebox.showerror("Error", "Оберіть зображення!")
            return
        
        try:
            msg = steganography.decode_image(self.decode_path)
            self.dec_textbox.configure(state="normal")
            self.dec_textbox.delete("1.0", "end")
            self.dec_textbox.insert("1.0", msg)
            self.dec_textbox.configure(state="disabled")
            
            if "не знайдено" in msg:
                messagebox.showwarning("Warning", "Прихований текст не знайдено.")
            else:
                messagebox.showinfo("Success", "Повідомлення успішно вилучено!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

if __name__ == "__main__":
    app = SteganoGUI()
    app.mainloop()
