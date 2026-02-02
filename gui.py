import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import steganography
from PIL import Image

# Configuration
ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class SteganographyApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title("StegoCrypt - Modern Steganography")
        self.geometry("700x550")
        self.resizable(False, False)

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self.header_frame = ctk.CTkFrame(self, corner_radius=0)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        
        self.header_label = ctk.CTkLabel(self.header_frame, text="StegoCrypt", font=("Roboto Medium", 24))
        self.header_label.pack(pady=15)

        # Tabview
        self.tabview = ctk.CTkTabview(self, width=650, height=450)
        self.tabview.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")
        
        self.tab_encode = self.tabview.add("Приховати (Encode)")
        self.tab_decode = self.tabview.add("Відкрити (Decode)")

        self.setup_encode_tab()
        self.setup_decode_tab()

    def setup_encode_tab(self):
        # Image Selection
        self.enc_frame_top = ctk.CTkFrame(self.tab_encode, fg_color="transparent")
        self.enc_frame_top.pack(fill="x", pady=10)

        self.enc_btn_select = ctk.CTkButton(self.enc_frame_top, text="Вибрати зображення", command=self.select_image_encode)
        self.enc_btn_select.pack(side="left", padx=10)

        self.enc_lbl_path = ctk.CTkLabel(self.enc_frame_top, text="Файл не обрано", text_color="gray")
        self.enc_lbl_path.pack(side="left", padx=10)

        # Message Input
        self.enc_lbl_msg = ctk.CTkLabel(self.tab_encode, text="Секретне повідомлення:", anchor="w")
        self.enc_lbl_msg.pack(fill="x", padx=10, pady=(10, 0))

        self.enc_txt_message = ctk.CTkTextbox(self.tab_encode, height=150)
        self.enc_txt_message.pack(fill="both", padx=10, pady=5, expand=True)

        # Action logic
        self.enc_btn_action = ctk.CTkButton(self.tab_encode, text="Зашифрувати та Зберегти", command=self.process_encode, height=40, font=("Roboto", 14))
        self.enc_btn_action.pack(pady=20, padx=10, fill="x")

        self.encode_image_path = None

    def setup_decode_tab(self):
        # Image Selection
        self.dec_frame_top = ctk.CTkFrame(self.tab_decode, fg_color="transparent")
        self.dec_frame_top.pack(fill="x", pady=10)

        self.dec_btn_select = ctk.CTkButton(self.dec_frame_top, text="Вибрати зображення", command=self.select_image_decode)
        self.dec_btn_select.pack(side="left", padx=10)

        self.dec_lbl_path = ctk.CTkLabel(self.dec_frame_top, text="Файл не обрано", text_color="gray")
        self.dec_lbl_path.pack(side="left", padx=10)

        # Message Output
        self.dec_lbl_msg = ctk.CTkLabel(self.tab_decode, text="Знайдене повідомлення:", anchor="w")
        self.dec_lbl_msg.pack(fill="x", padx=10, pady=(10, 0))

        self.dec_txt_output = ctk.CTkTextbox(self.tab_decode, height=150, state="disabled")
        self.dec_txt_output.pack(fill="both", padx=10, pady=5, expand=True)

        # Action logic
        self.dec_btn_action = ctk.CTkButton(self.tab_decode, text="Розшифрувати", command=self.process_decode, height=40, fg_color="green", hover_color="darkgreen", font=("Roboto", 14))
        self.dec_btn_action.pack(pady=20, padx=10, fill="x")

        self.decode_image_path = None

    def select_image_encode(self):
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp")])
        if file_path:
            self.encode_image_path = file_path
            self.enc_lbl_path.configure(text=os.path.basename(file_path), text_color=("black", "white"))

    def select_image_decode(self):
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp")])
        if file_path:
            self.decode_image_path = file_path
            self.dec_lbl_path.configure(text=os.path.basename(file_path), text_color=("black", "white"))

    def process_encode(self):
        if not self.encode_image_path:
            messagebox.showwarning("Помилка", "Будь ласка, оберіть зображення.")
            return
        
        message = self.enc_txt_message.get("1.0", "end-1c").strip()
        if not message:
            messagebox.showwarning("Помилка", "Введіть повідомлення для приховування.")
            return

        file_type = [("PNG Image", "*.png")]
        output_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=file_type)
        
        if output_path:
            try:
                final_path = steganography.encode_image(self.encode_image_path, message, output_path)
                messagebox.showinfo("Успіх", f"Повідомлення збережено у:\n{final_path}")
            except Exception as e:
                messagebox.showerror("Помилка", f"Не вдалося приховати повідомлення:\n{str(e)}")

    def process_decode(self):
        if not self.decode_image_path:
            messagebox.showwarning("Помилка", "Будь ласка, оберіть зображення для сканування.")
            return

        try:
            hidden_message = steganography.decode_image(self.decode_image_path)
            
            self.dec_txt_output.configure(state="normal")
            self.dec_txt_output.delete("1.0", "end")
            self.dec_txt_output.insert("1.0", hidden_message)
            self.dec_txt_output.configure(state="disabled")
            
            if "не знайдено" in hidden_message:
                 messagebox.showinfo("Результат", "Приховане повідомлення не знайдено.")
            else:
                 messagebox.showinfo("Успіх", "Повідомлення успішно вилучено!")

        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка при читанні:\n{str(e)}")

if __name__ == "__main__":
    app = SteganographyApp()
    app.mainloop()
