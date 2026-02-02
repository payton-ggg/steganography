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


def encode_image(image_path: str, message: str, output_path: str):
    img = Image.open(image_path)
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")
    pixels = img.load()

    width, height = img.size
    message_bits = text_to_bits(message + END_MARKER)
    bit_index = 0
    max_bits = width * height * 3

    if len(message_bits) > max_bits:
        raise ValueError("Повідомлення занадто довге для цього зображення")

    for y in range(height):
        for x in range(width):
            if bit_index >= len(message_bits):
                break

            r, g, b = pixels[x, y]
            new_colors = []

            for color in (r, g, b):
                if bit_index < len(message_bits):
                    new_color = (color & ~1) | int(message_bits[bit_index])
                    bit_index += 1
                else:
                    new_color = color
                new_colors.append(new_color)

            pixels[x, y] = tuple(new_colors)
        if bit_index >= len(message_bits):
            break
    
    if output_path.lower().endswith(".jpg") or output_path.lower().endswith(".jpeg"):
        # JPEG uses lossy compression, so force PNG
        output_path = output_path.rsplit(".", 1)[0] + ".png"

    img.save(output_path)
    return output_path


def decode_image(image_path: str) -> str:
    img = Image.open(image_path)
    img = img.convert("RGB")
    pixels = img.load()

    width, height = img.size
    bits = ""
    data = bytearray()

    for y in range(height):
        for x in range(width):
            for color in pixels[x, y]:
                bits += str(color & 1)

                if len(bits) == 8:
                    data.append(int(bits, 2))
                    bits = ""

                    try:
                        text = data.decode("utf-8")
                        if END_MARKER in text:
                            return text.replace(END_MARKER, "")
                    except UnicodeDecodeError:
                        pass

    return "Приховане повідомлення не знайдено."


def main():
    print("LSB Стеганографія")
    print("1 — Приховати повідомлення")
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
