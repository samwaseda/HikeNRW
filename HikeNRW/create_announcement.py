import numpy as np
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import urllib.request
import re
import os

# Assign the path to the fonts from the env variable PATH_TO_FONTS
PATH_TO_FONTS = os.environ.get("PATH_TO_FONT", "/usr/share/fonts/opentype/urw-base35/")


def div(size):
    return size[0] / size[1]


def get_size(current_size, target_size, by_height=True):
    if by_height:
        height = target_size[1]
        width = int(current_size[0] / current_size[1] * height)
    else:
        width = target_size[0]
        height = int(current_size[1] / current_size[0] * width)
    return width, height


def resize_and_crop(img, target_size):
    if div(img.size) > div(target_size):
        width, height = get_size(img.size, target_size, by_height=True)
    else:
        width, height = get_size(img.size, target_size, by_height=False)
    img = img.resize((width, height))
    img = img.crop(
        (
            (width - target_size[0]) // 2,
            (height - target_size[1]) // 2,
            (width + target_size[0]) // 2,
            (height + target_size[1]) // 2,
        )
    )
    return img


def get_image_from_url(url):
    response = requests.get(url)
    return Image.open(BytesIO(response.content))


def get_komoot_images(komoot_dict):
    html_source = urllib.request.urlopen(
        komoot_dict["links_dict"]["cover_images"]["href"]
    ).read()
    urls = re.findall("src\":\"(https://[^?\s]+/0)", html_source.decode())
    images = [
        get_image_from_url(url)
        for url in urls
        if "/000/" in url and "defaultuserimage" not in url
    ]
    return komoot_dict["name"], komoot_dict["vector_image"], images


def get_most_common_color(map_img):
    colors, counts = np.unique(
        list(map_img.convert("RGB").getdata()),
        axis=0,
        return_counts=True
    )
    return tuple(colors[counts.argmax()])


def get_banner_images(map_img, images, buffer=None):
    if buffer is None:
        buffer = get_buffer(map_img)
    new_images = []
    width, height = map_img.size
    if len(images) == 0:
        raise ValueError("No images found")
    if len(images) == 1:
        target_size = (width, height)
        new_images.append(
            (resize_and_crop(images[0], target_size), (0, buffer))
        )
        return new_images
    target_size = (width // 2, height)
    new_images.append(
        (resize_and_crop(images[0], target_size), (0, buffer))
    )
    if len(images) == 2:
        new_images.append(
            (resize_and_crop(images[1], target_size), (width // 2, buffer))
        )
        return new_images
    target_size = (width // 2, height // 2)
    new_images.append(
        (resize_and_crop(images[1], target_size), (width // 2, buffer))
    )
    new_images.append(
        (resize_and_crop(images[2], target_size), (width // 2, height // 2 + buffer))
    )
    return new_images


def get_text_size(
    text,
    font_size=70,
    font='/usr/share/fonts/opentype/urw-base35/URWGothic-Demi.otf'
):
    my_font = ImageFont.truetype(font, size=font_size)
    size = []
    for t in text.split("\n"):
        dummy_image = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(dummy_image)
        size.append(draw.textlength(t, font=my_font))
    return (int(max(size)), len(text.split("\n")) * font_size)


def get_opposite_color(color):
    return tuple(255 - c for c in color)


def draw_text(
    text,
    img,
    position,
    most_common_color,
    font_size=70,
    font=PATH_TO_FONTS + 'URWGothic-Demi.otf'
):
    img_text = ImageDraw.Draw(img)
    myFont = ImageFont.truetype(font, font_size)
    img_text.text(
        (position[0], position[1]),
        text,
        font=myFont,
        fill=get_opposite_color(most_common_color)
    )


def write_multiple_lines(
    text,
    img,
    position,
    height,
    most_common_color,
    font_size=70,
    font=PATH_TO_FONTS + 'URWGothic-Demi.otf'
):
    buffer = (
        height - font_size * len(text.split("\n"))
    ) // (len(text.split("\n")) - 1)
    position = list(position)
    for ii, tt in enumerate(text.split("\n")):
        draw_text(
            tt,
            img,
            position,
            font_size=font_size,
            font=font,
            most_common_color=most_common_color
        )
        position[1] += font_size + buffer


def get_buffer(map_img):
    return map_img.width // 2 - map_img.height


def get_topographic_info(distance, elev_up, elev_down):
    d = round(distance / 100) / 10
    up = round(elev_up)
    down = round(elev_down)
    return f"↔️{d}km\n↗️{up}m\n↘️{down}m"


def export_banner_image(komoot_dict):
    _, map_img, images = get_komoot_images(komoot_dict)
    img = Image.new("RGB", (map_img.width, map_img.height))
    for image, position in get_banner_images(map_img, images, buffer=0):
        img.paste(image, position)
    return img


def get_image(komoot_dict, date, meeting_point):
    title, map_img, images = get_komoot_images(komoot_dict)
    width, height = map_img.size
    most_common_color = get_most_common_color(map_img)
    buffer = get_buffer(map_img)
    img = Image.new("RGB", (map_img.width, map_img.width), color=most_common_color)
    for image, position in get_banner_images(map_img, images):
        img.paste(image, position)
    img.paste(map_img, (0, height + 2 * buffer))
    font_size = 100
    text_size = get_text_size(title, font_size=font_size)
    if text_size[0] > img.width:
        font_size = int(font_size * img.width / text_size[0])
        text_size = get_text_size(title, font_size=font_size)
    displacement = (10, buffer // 2 - text_size[1] // 2)
    draw_text(
        title,
        img,
        position=displacement,
        font_size=font_size,
        most_common_color=most_common_color
    )
    imgl = ImageDraw.Draw(img)
    imgl.line(
        (
            (img.width // 2, int(1.1 * buffer) + map_img.height),
            (img.width // 2, int(1.9 * buffer) + map_img.height)
        ),
        fill="white",
        width=5
    )
    write_multiple_lines(
        date + "\n" + meeting_point,
        img,
        position=(img.width // 2 + 20, int(1.15 * buffer) + map_img.height),
        font_size=50,
        height=0.7 * buffer,
        most_common_color=most_common_color
    )
    topo = get_topographic_info(
        komoot_dict["distance"],
        komoot_dict["elevation_up"],
        komoot_dict["elevation_down"]
    )
    size = get_text_size(topo, font_size=40)
    write_multiple_lines(
        topo,
        img,
        position=(img.width // 2 - 50 - size[0], int(1.1 * buffer) + map_img.height),
        font_size=40,
        height=0.8 * buffer,
        most_common_color=most_common_color
    )
    return img
