"""Рисует образцы фото для шагов анкеты. Это схемы, не настоящие документы."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "assets" / "examples"
W, H = 1200, 760


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def canvas(top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    image = Image.new("RGB", (W, H), bottom)
    draw = ImageDraw.Draw(image)
    for y in range(H):
        mix = y / H
        color = tuple(int(top[i] * (1 - mix) + bottom[i] * mix) for i in range(3))
        draw.line([(0, y), (W, y)], fill=color)
    return image


def rounded(draw: ImageDraw.ImageDraw, box, radius, fill, outline=None, width=1) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def watermark(image: Image.Image) -> None:
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    overlay = ImageDraw.Draw(layer)
    overlay.text((W / 2, H / 2), "NAMUNA", font=font(110, True), fill=(15, 23, 42, 48), anchor="mm")
    image.paste(Image.alpha_composite(image.convert("RGBA"), layer).convert("RGB"))


def label(draw: ImageDraw.ImageDraw, text: str) -> None:
    badge = font(28, True)
    draw.rounded_rectangle((36, 28, 36 + 220, 78), radius=18, fill=(15, 23, 42))
    draw.text((146, 53), text, font=badge, fill="white", anchor="mm")


def lines(draw: ImageDraw.ImageDraw, x: int, y: int, rows: list[str], color) -> None:
    small = font(22)
    for index, row in enumerate(rows):
        top = y + index * 46
        draw.text((x, top), row, font=small, fill=color)
        draw.rounded_rectangle((x + 250, top + 4, x + 620, top + 28), radius=6, fill=(226, 232, 240))


def save(image: Image.Image, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    image.save(OUT / name, "JPEG", quality=92)


def passport() -> None:
    image = canvas((226, 240, 252), (191, 219, 254))
    draw = ImageDraw.Draw(image)
    rounded(draw, (70, 110, 1130, 680), 28, (248, 250, 252), (37, 99, 235), 6)
    draw.rectangle((70, 110, 1130, 190), fill=(22, 101, 52))
    draw.text((600, 150), "O'ZBEKISTON  ·  PASPORT / ID", font=font(34, True), fill="white", anchor="mm")
    rounded(draw, (120, 240, 390, 580), 16, (203, 213, 225))
    draw.text((255, 400), "FOTO", font=font(36, True), fill=(71, 85, 105), anchor="mm")
    lines(
        draw,
        440,
        250,
        ["Familiya", "Ism", "Otasining ismi", "Tug'ilgan sana", "JSHSHIR"],
        (15, 23, 42),
    )
    watermark(image)
    label(draw, "1  ·  OLD")
    save(image, "passport.jpg")


def license_front() -> None:
    image = canvas((254, 226, 226), (254, 202, 202))
    draw = ImageDraw.Draw(image)
    rounded(draw, (70, 110, 1130, 680), 28, (255, 247, 247), (185, 28, 28), 6)
    draw.rectangle((70, 110, 1130, 200), fill=(153, 27, 27))
    draw.text((600, 155), "HAYDOVCHILIK GUVOHNOMASI", font=font(32, True), fill="white", anchor="mm")
    rounded(draw, (120, 250, 390, 560), 16, (148, 163, 184))
    draw.text((255, 390), "FOTO", font=font(32, True), fill="white", anchor="mm")
    lines(draw, 440, 260, ["Familiya", "Ism", "Tug'ilgan sana", "Berilgan sana", "Raqami"], (127, 29, 29))
    watermark(image)
    label(draw, "2  ·  OLD")
    save(image, "license_front.jpg")


def license_back() -> None:
    image = canvas((255, 237, 213), (254, 215, 170))
    draw = ImageDraw.Draw(image)
    rounded(draw, (70, 110, 1130, 680), 28, (255, 251, 235), (194, 65, 12), 6)
    draw.text((600, 160), "ORQA TARAF  ·  TOIFALAR", font=font(32, True), fill=(124, 45, 18), anchor="mm")
    categories = ["A", "B", "C", "D", "BE", "CE"]
    for index, name in enumerate(categories):
        column = index % 3
        row = index // 3
        x = 140 + column * 320
        y = 250 + row * 180
        rounded(draw, (x, y, x + 280, y + 140), 16, "white", (251, 146, 60), 3)
        draw.text((x + 40, y + 70), name, font=font(40, True), fill=(154, 52, 18), anchor="lm")
        draw.rounded_rectangle((x + 110, y + 48, x + 240, y + 92), radius=8, fill=(255, 237, 213))
    watermark(image)
    label(draw, "3  ·  ORQA")
    save(image, "license_back.jpg")


def tech(side: str, filename: str, badge: str, rows: list[str]) -> None:
    image = canvas((224, 242, 254), (186, 230, 253))
    draw = ImageDraw.Draw(image)
    rounded(draw, (70, 110, 1130, 680), 28, (240, 249, 255), (3, 105, 161), 6)
    draw.rectangle((70, 110, 1130, 200), fill=(3, 105, 161))
    draw.text((600, 155), side, font=font(30, True), fill="white", anchor="mm")
    lines(draw, 160, 250, rows, (12, 74, 110))
    watermark(image)
    label(draw, badge)
    save(image, filename)


def selfie() -> None:
    image = canvas((241, 245, 249), (226, 232, 240))
    draw = ImageDraw.Draw(image)
    rounded(draw, (330, 80, 870, 700), 36, "white", (100, 116, 139), 4)
    draw.ellipse((470, 180, 730, 440), fill=(203, 213, 225))
    draw.pieslice((400, 430, 800, 760), 200, 340, fill=(148, 163, 184))
    draw.text((600, 620), "Yuz aniq ko'rinsin", font=font(32, True), fill=(51, 65, 85), anchor="mm")
    watermark(image)
    label(draw, "6  ·  SELFIE")
    save(image, "selfie.jpg")


def taxi_license() -> None:
    image = canvas((243, 244, 246), (229, 231, 235))
    draw = ImageDraw.Draw(image)
    rounded(draw, (260, 70, 940, 700), 8, "white", (17, 24, 39), 3)
    draw.rounded_rectangle((340, 130, 860, 220), radius=8, outline=(220, 38, 38), width=6)
    draw.text((600, 175), "LITSENZIYA", font=font(40, True), fill=(185, 28, 28), anchor="mm")
    for index in range(6):
        y = 270 + index * 58
        draw.text((320, y), f"{index + 1}.", font=font(22), fill=(55, 65, 81))
        draw.line((370, y + 18, 860, y + 18), fill=(209, 213, 219), width=3)
    watermark(image)
    label(draw, "7  ·  A4")
    save(image, "taxi_license.jpg")


def car_panel(draw: ImageDraw.ImageDraw, box, title: str, kind: str) -> None:
    rounded(draw, box, 24, "white")
    x1, y1, x2, y2 = box
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2 + 10
    body = (15, 23, 42)
    if kind == "front":
        draw.rounded_rectangle((cx - 150, cy - 70, cx + 150, cy + 90), radius=30, fill=body)
        draw.rectangle((cx - 120, cy - 20, cx - 40, cy + 20), fill=(56, 189, 248))
        draw.rectangle((cx + 40, cy - 20, cx + 120, cy + 20), fill=(56, 189, 248))
        draw.rounded_rectangle((cx - 70, cy + 40, cx + 70, cy + 70), radius=6, fill=(203, 213, 225))
    elif kind == "back":
        draw.rounded_rectangle((cx - 150, cy - 70, cx + 150, cy + 90), radius=30, fill=body)
        draw.rectangle((cx - 110, cy - 10, cx - 40, cy + 16), fill=(248, 113, 113))
        draw.rectangle((cx + 40, cy - 10, cx + 110, cy + 16), fill=(248, 113, 113))
        draw.rounded_rectangle((cx - 80, cy + 40, cx + 80, cy + 78), radius=6, fill=(226, 232, 240))
    else:
        draw.rounded_rectangle((cx - 170, cy - 20, cx + 170, cy + 70), radius=24, fill=body)
        draw.rounded_rectangle((cx - 70, cy - 80, cx + 90, cy), radius=20, fill=(30, 41, 59))
        draw.ellipse((cx - 120, cy + 40, cx - 60, cy + 100), fill=(51, 65, 85))
        draw.ellipse((cx + 70, cy + 40, cx + 130, cy + 100), fill=(51, 65, 85))
        if kind == "right":
            draw.polygon([(cx + 150, cy - 10), (cx + 190, cy + 10), (cx + 150, cy + 30)], fill=(148, 163, 184))
    draw.text(((x1 + x2) / 2, y1 + 36), title, font=font(28, True), fill=(15, 23, 42), anchor="mm")


def cars() -> None:
    image = canvas((248, 250, 252), (226, 232, 240))
    draw = ImageDraw.Draw(image)
    car_panel(draw, (40, 40, 640, 720), "1. Old", "front")
    car_panel(draw, (680, 40, 1160, 250), "2. Orqa", "back")
    car_panel(draw, (680, 275, 1160, 485), "3. Chap", "left")
    car_panel(draw, (680, 510, 1160, 720), "4. O'ng", "right")
    save(image, "car.jpg")


if __name__ == "__main__":
    passport()
    license_front()
    license_back()
    tech(
        "TEXNIK PASPORT  ·  OLD TARAF",
        "tech_front.jpg",
        "4  ·  OLD",
        ["Davlat raqami", "Ishlab chiqarilgan yili", "Berilgan sana", "Egasi", "Manzil"],
    )
    tech(
        "TEXNIK PASPORT  ·  ORQA TARAF",
        "tech_back.jpg",
        "5  ·  ORQA",
        ["Rusumi", "Modeli", "Rangi", "Kuzov raqami", "Dvigatel"],
    )
    selfie()
    taxi_license()
    cars()
    print(OUT)
