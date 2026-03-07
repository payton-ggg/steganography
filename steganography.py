from PIL import Image, ImageOps
import numpy as np
import cv2

END_MARKER = "###END###"


def text_to_bits(text: str) -> str:
    """Перетворює текст у бітовий рядок (UTF-8)"""
    return ''.join(format(byte, '08b') for byte in text.encode('utf-8'))


def bits_to_text(bits: str) -> str:
    """Перетворює бітовий рядок назад у текст"""
    bytes_list = [bits[i:i + 8] for i in range(0, len(bits), 8)]
    byte_array = bytearray(int(byte, 2) for byte in bytes_list)
    return byte_array.decode('utf-8', errors='ignore')


def calculate_capacity(image_path: str) -> dict:
    """Обчислює максимальну вместимість зображення для текстових даних
    
    Returns:
        dict: {'max_bytes': int, 'max_chars_approx': int, 'image_size': tuple}
    """
    img = Image.open(image_path)
    img = ImageOps.exif_transpose(img)
    width, height = img.size
    bands = len(img.getbands())
    
    total_bits = width * height * bands
    
    marker_bits = len(text_to_bits(END_MARKER))
    available_bits = total_bits - marker_bits
    
    max_bytes = available_bits // 8
    max_chars_conservative = max_bytes // 2
    
    # Freq capacity
    h_pad = (8 - height % 8) % 8
    w_pad = (8 - width % 8) % 8
    padded_height = height + h_pad
    padded_width = width + w_pad
    freq_coords_len = 20
    freq_total_bits = (padded_height // 8) * (padded_width // 8) * freq_coords_len
    freq_max_bytes = max(0, freq_total_bits - marker_bits) // 8
    freq_max_chars_approx = freq_max_bytes // 2
    
    return {
        'max_bytes': max_bytes,
        'max_chars_approx': max_chars_conservative,
        'freq_max_chars_approx': freq_max_chars_approx,
        'image_size': (width, height)
    }


def encode_image(image_path: str, message: str, output_path: str):
    img = Image.open(image_path)
    icc = img.info.get('icc_profile')
    exif = img.getexif()

    img = ImageOps.exif_transpose(img)
    
    if img.mode not in ('RGB', 'RGBA', 'L'):
        img = img.convert("RGB")
    
    pixels = img.load()

    width, height = img.size
    bands = len(img.getbands())
    message_bits = text_to_bits(message + END_MARKER)
    bit_index = 0
    max_bits = width * height * bands

    if len(message_bits) > max_bits:
        raise ValueError("Повідомлення занадто довге для цього зображення")

    for y in range(height):
        for x in range(width):
            if bit_index >= len(message_bits):
                break

            original_pixel = pixels[x, y]
            if isinstance(original_pixel, int):
                original_pixel = (original_pixel,)
            
            new_colors = []

            for color in original_pixel:
                if bit_index < len(message_bits):
                    new_color = (color & ~1) | int(message_bits[bit_index])
                    bit_index += 1
                else:
                    new_color = color
                new_colors.append(new_color)

            if len(new_colors) == 1:
                pixels[x, y] = new_colors[0]
            else:
                pixels[x, y] = tuple(new_colors)
        if bit_index >= len(message_bits):
            break
    
    if output_path.lower().endswith(".jpg") or output_path.lower().endswith(".jpeg"):
        output_path = output_path.rsplit(".", 1)[0] + ".png"

    save_kwargs = {}
    if output_path.lower().endswith(".png"):
        save_kwargs = {'format': 'PNG'}
    if icc:
        save_kwargs['icc_profile'] = icc
    if exif:
        save_kwargs['exif'] = exif

    img.save(output_path, **save_kwargs)
    return output_path


def decode_image(image_path: str) -> str:
    img = Image.open(image_path)
    
    if img.mode not in ('RGB', 'RGBA', 'L'):
        img = img.convert("RGB")
        
    pixels = img.load()

    width, height = img.size
    bits = ""
    data = bytearray()

    marker_bytes = END_MARKER.encode("utf-8")
    marker_len = len(marker_bytes)

    for y in range(height):
        for x in range(width):
            pixel = pixels[x, y]
            if isinstance(pixel, int):
                pixel = (pixel,)
                
            for color in pixel:
                bits += str(color & 1)

                if len(bits) == 8:
                    data.append(int(bits, 2))
                    bits = ""

                    if len(data) >= marker_len and data[-marker_len:] == marker_bytes:
                        try:
                            return data[:-marker_len].decode("utf-8")
                        except UnicodeDecodeError:
                            pass

    return "Приховане повідомлення не знайдено."


def encode_image_eof(image_path: str, message: str, output_path: str):
    """Приховує повідомлення в кінці файлу (EOF) без зміни пікселів і втрати якості"""
    with open(image_path, 'rb') as f:
        content = f.read()
    
    marker_bytes = END_MARKER.encode('utf-8')
    message_bytes = message.encode('utf-8')
    
    with open(output_path, 'wb') as f:
        f.write(content)
        f.write(marker_bytes)
        f.write(message_bytes)
        
    return output_path


def decode_image_eof(image_path: str) -> str:
    """Дістає повідомлення з кінця файлу (EOF)"""
    with open(image_path, 'rb') as f:
        content = f.read()
        
    marker_bytes = END_MARKER.encode('utf-8')
    idx = content.rfind(marker_bytes)
    
    if idx != -1:
        message_bytes = content[idx + len(marker_bytes):]
        try:
            return message_bytes.decode('utf-8')
        except UnicodeDecodeError:
            pass
            
    return "Приховане повідомлення не знайдено."


def encode_image_freq(image_path: str, message: str, output_path: str):
    """Приховує повідомлення в частотному діапазоні (DCT) зображення."""
    message_bits = text_to_bits(message + END_MARKER)
    
    # Read image using cv2
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Не вдалося прочитати зображення для частотного методу")
        
    # Convert to YCrCb (we will hide data in the Y channel - luminance)
    img_ycc = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    y_channel, cr_channel, cb_channel = cv2.split(img_ycc)
    
    height, width = y_channel.shape
    
    # Needs to be a multiple of 8 for 8x8 blocks
    h_pad = (8 - height % 8) % 8
    w_pad = (8 - width % 8) % 8
    if h_pad != 0 or w_pad != 0:
        y_channel = np.pad(y_channel, ((0, h_pad), (0, w_pad)), mode='edge')
        
    padded_height, padded_width = y_channel.shape
    
    # DCT coefficients indices to modify (mid-frequency)
    coords = [
        (3, 3), (3, 4), (4, 3), (4, 4), (4, 5), (5, 4),
        (2, 4), (2, 5), (3, 2), (3, 5), (4, 2), (5, 2), (5, 3),
        (5, 5), (6, 3), (3, 6), (4, 6), (6, 4), (6, 5), (5, 6)
    ]
    
    max_capacity_bits = (padded_height // 8) * (padded_width // 8) * len(coords)
    if len(message_bits) > max_capacity_bits:
        raise ValueError(f"Повідомлення занадто довге. Максимум для частотного методу: {max_capacity_bits // 8} байт.")
        
    y_channel_float = np.float32(y_channel)
    bit_idx = 0
    message_len = len(message_bits)
    delta = 25  # Quantization step
    
    for row in range(0, padded_height, 8):
        for col in range(0, padded_width, 8):
            if bit_idx >= message_len:
                break
                
            block = y_channel_float[row:row+8, col:col+8]
            dct_block = cv2.dct(block)
            
            for u, v in coords:
                if bit_idx >= message_len:
                    break
                    
                val = dct_block[u, v]
                bit = int(message_bits[bit_idx])
                
                # Quantize
                q = round(val / delta)
                if q % 2 == 0:
                    if bit == 1:
                        q += 1 if val > q * delta else -1
                else:
                    if bit == 0:
                        q += 1 if val > q * delta else -1
                        
                dct_block[u, v] = q * delta
                bit_idx += 1
                
            # Inverse DCT
            y_channel_float[row:row+8, col:col+8] = cv2.idct(dct_block)
            
    # Clip and convert back
    y_channel_mod = np.clip(y_channel_float, 0, 255).astype(np.uint8)
    
    # Remove padding
    y_channel_mod = y_channel_mod[:height, :width]
    
    img_ycc_mod = cv2.merge((y_channel_mod, cr_channel, cb_channel))
    img_bgr_mod = cv2.cvtColor(img_ycc_mod, cv2.COLOR_YCrCb2BGR)
    
    if output_path.lower().endswith(('.jpg', '.jpeg')):
        # Save as PNG anyway to avoid standard JPEG destroying our delicate DCT modifications
        output_path = output_path.rsplit(".", 1)[0] + ".png"
        
    cv2.imwrite(output_path, img_bgr_mod)
    return output_path


def decode_image_freq(image_path: str) -> str:
    """Дістає повідомлення, приховане частотним методом (DCT)."""
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Не вдалося прочитати зображення")
        
    img_ycc = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    y_channel, _, _ = cv2.split(img_ycc)
    
    height, width = y_channel.shape
    h_pad = (8 - height % 8) % 8
    w_pad = (8 - width % 8) % 8
    if h_pad != 0 or w_pad != 0:
        y_channel = np.pad(y_channel, ((0, h_pad), (0, w_pad)), mode='edge')
        
    padded_height, padded_width = y_channel.shape
    y_channel_float = np.float32(y_channel)
    
    coords = [
        (3, 3), (3, 4), (4, 3), (4, 4), (4, 5), (5, 4),
        (2, 4), (2, 5), (3, 2), (3, 5), (4, 2), (5, 2), (5, 3),
        (5, 5), (6, 3), (3, 6), (4, 6), (6, 4), (6, 5), (5, 6)
    ]
    delta = 25
    
    bits = ""
    data = bytearray()
    marker_bytes = END_MARKER.encode("utf-8")
    marker_len = len(marker_bytes)
    
    for row in range(0, padded_height, 8):
        for col in range(0, padded_width, 8):
            block = y_channel_float[row:row+8, col:col+8]
            dct_block = cv2.dct(block)
            
            for u, v in coords:
                val = dct_block[u, v]
                q = round(val / delta)
                bit = str(int(abs(q) % 2))
                
                bits += bit
                if len(bits) == 8:
                    data.append(int(bits, 2))
                    bits = ""
                    
                    if len(data) >= marker_len and data[-marker_len:] == marker_bytes:
                        try:
                            return data[:-marker_len].decode("utf-8")
                        except UnicodeDecodeError:
                            pass
                        
    return "Приховане повідомлення не знайдено."


def main():
    print("LSB Стеганографія")
    print("1 — Приховати повідомлення")
    print("2 — Дістати повідомлення")
    print("2 — Дістати повідомлення")

    choice = input("Оберіть режим (1/2): ").strip()

    if choice == "1":
        image_path = input("Шлях до зображення: ").strip()
        message = input("Введіть текстове повідомлення: ")
        output_path = input("Імʼя вихідного файлу: ").strip()

        final_path = encode_image(image_path, message, output_path)
        print(f"Повідомлення успішно приховано у файлі: {final_path}")
        if final_path != output_path:
            print("⚠️ Формат було змінено на PNG для збереження даних.")

    elif choice == "2":
        image_path = input("Шлях до зображення: ").strip()
        message = decode_image(image_path)
        print("\nПриховане повідомлення:")
        print(message)

    else:
        print("Невірний вибір.")


if __name__ == "__main__":
    main()
