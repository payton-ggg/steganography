from PIL import Image, ImageOps

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
    
    return {
        'max_bytes': max_bytes,
        'max_chars_approx': max_chars_conservative,
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
