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
            (height + target_size[1]) // 2
        )
    )
    return img
