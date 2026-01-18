from PIL import Image
import os

def validate_sizes(paths):
    images = []

    # load all real image paths
    for path in paths:
        if path is None:
            continue
        img = Image.open(path).convert("RGBA")
        images.append({
            "path": path,
            "name": os.path.basename(path),
            "size": img.size  # (w, h)
        })

    if not images:
        return None  # no real images

    # find largest by pixel count
    reference = max(images, key=lambda i: i["size"][0] * i["size"][1])
    expected_size = reference["size"]

    # compare
    for img in images:
        if img["size"] != expected_size:
            raise ValueError(
                f"Size mismatch:\n"
                f"  File: {img['name']} ({img['size'][0]}x{img['size'][1]})\n"
                f"  Expected: {expected_size[0]}x{expected_size[1]}\n"
                f"  Reference: {reference['name']}"
            )

    return expected_size

def load_or_white(path, size, preserve_transparent_colors=False):
    if path is None:
        # create white channel
        return Image.new("L", size, 255)

    img = Image.open(path).convert("RGBA")

    if img.size != size:
        img = img.resize(size, Image.BICUBIC)

    # If not preserving transparent colors, flatten transparent areas to white
    if not preserve_transparent_colors:
        pixels = img.load()
        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = pixels[x, y]
                if a == 0:
                    # zero alpha → force white in this channel
                    pixels[x, y] = (255, 255, 255, 0)

    # Return only the single grayscale channel
    return img.split()[0]

def channel_pack(
    r_path=None,
    g_path=None,
    b_path=None,
    a_path=None,
    output_path="channel_packed.png",
    preserve_transparent_colors=True
):
    paths = [r_path, g_path, b_path, a_path]

    # Find expected size (largest image)
    size = validate_sizes(paths)
    if size is None:
        raise ValueError("No input images provided for channel packing.")

    # Load each channel
    r = load_or_white(r_path, size, preserve_transparent_colors)
    g = load_or_white(g_path, size, preserve_transparent_colors)
    b = load_or_white(b_path, size, preserve_transparent_colors)
    a = load_or_white(a_path, size, preserve_transparent_colors)

    # Merge and save
    packed = Image.merge("RGBA", (r, g, b, a))
    packed.save(output_path)

    print(f"Saved channel-packed texture as {output_path}")

channel_pack(
    r_path="G36_Metallic.png",
    g_path="G36_Roughness.png",
    b_path=None,
    a_path=None,
    preserve_transparent_colors=True
)