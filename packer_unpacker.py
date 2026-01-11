from PIL import Image, ImageTk
import os
import FreeSimpleGUI as sg
import numpy as np
import tkinter as tk
from tkinter import filedialog
from tkinterdnd2 import TkinterDnD, DND_FILES



root = TkinterDnD.Tk()  
root.title("Texture Channel Unpacker/Packer")
root.geometry("800x800")
btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)
gamma_correction = tk.BooleanVar(value=False)
content_frame = tk.Frame(root)
content_frame.pack(fill="both", expand=True)
merge_channel_paths = {"R": None, "G": None, "B": None, "A": None}
merge_channel_images = {}    # store full‑size PIL images
merge_channel_thumbs = {}    # store thumbnails displayed
merged_image = None
merged_image_thumb = None
DROP_SIZE = (170, 170)  # thumbnail display size
current_panel = None
unpack_path_var = tk.StringVar()
output_filename = tk.StringVar()
output_filename.set("packed_texture.png")
unpack_image = None
unpack_images = {}
unpack_thumbs = {}
unpack_channels_list = {}
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
    return packed
    packed.save(output_path)



def unpack_channels_no_gamma_correction(packed_path):
    img = Image.open(packed_path).convert("RGBA")
    r, g, b, a = img.split()
   

    base = os.path.splitext(os.path.basename(packed_path))[0]

  

    print("Channels unpacked successfully")
    return [
        r,
        g,
        b,
        a
    ]



def linear_to_srgb(img):
    arr = np.array(img) / 255.0
    arr = np.where(arr <= 0.0031308,
                   arr * 12.92,
                   1.055 * (arr ** (1 / 2.4)) - 0.055)
    return Image.fromarray((arr * 255).astype("uint8"))

def unpack_channels_gamma_correction(packed_path):
    img = Image.open(packed_path).convert("RGBA")
    r, g, b, a = img.split()

    # output_dir = packed_path + "_unpacked_gamma_corrected"
    # os.makedirs(output_dir, exist_ok=True)
    # base = os.path.splitext(os.path.basename(packed_path))[0]

    # linear_to_srgb(r).save(f"{output_dir}/{base}_R_GAMMA_CORRECTED.png")
    # linear_to_srgb(g).save(f"{output_dir}/{base}_G_GAMMA_CORRECTED.png")
    # linear_to_srgb(b).save(f"{output_dir}/{base}_B_GAMMA_CORRECTED.png")
    # linear_to_srgb(a).save(f"{output_dir}/{base}_A_GAMMA_CORRECTED.png")

    print("Channels unpacked (gamma corrected)")
    return [
        linear_to_srgb(r),
        linear_to_srgb(g),
        linear_to_srgb(b),
        linear_to_srgb(a)
    ]



# unpack_channels_gamma_correction("T_AT_TE_aa_NMA.png")
# unpack_channels_no_gamma_correction("T_AT_TE_aa_NMA.png")



def clear_panel(frame):
    for widget in frame.winfo_children():
        widget.destroy()



def show_merge():
    show_panel("merge")

def show_unpack():
    show_panel("unpack")

tk.Button(btn_frame, text="Merge Textures", command=show_merge).pack(side="left", padx=10)
tk.Button(btn_frame, text="Unpack Texture", command=show_unpack).pack(side="left", padx=10)




def create_merged_image():
    global merged_image, merged_image_thumb
    merged_image = channel_pack(
        r_path=merge_channel_paths["R"],
        g_path=merge_channel_paths["G"],
        b_path=merge_channel_paths["B"],
        a_path=merge_channel_paths["A"],
    )
    print("merged image created:", merged_image)
    merged_image_thumb = ImageTk.PhotoImage(merged_image.resize((300, 300), Image.LANCZOS))
    preview_frame.config(image=merged_image_thumb, bg=None, text="")
    preview_frame.image = merged_image_thumb
    
def save_merged_image():
    print("merged image to save:", merged_image)
    if (merged_image is None):
        print("No merged image to save.")
        return
    merged_image.save(output_filename.get() or "merged_texture.png")

def clear_channel(channel):
    # remove stored images
    merge_channel_paths[channel] = None
    merge_channel_images.pop(channel, None)
    merge_channel_thumbs.pop(channel, None)

    # reset thumbnail square
    thumb_frames[channel].config(image="", bg="lightgray")
    thumb_frames[channel].image = None

    # reset resolution text
    res_labels[channel].config(text="")

def merge_drop(event, channel):
    filepaths_raw = event.data
    if not filepaths_raw:
        return

    raw = filepaths_raw.strip("{}")
    path = raw.split()[-1]
    if not os.path.isfile(path):
        return

    # store original
    try:
        original = Image.open(path)
    except Exception as e:
        print("Error loading image:", e)
        return

    merge_channel_paths[channel] = path
    merge_channel_images[channel] = original.copy()

    # thumbnail for display
    thumb = original.copy()
    thumb.thumbnail(DROP_SIZE, Image.LANCZOS)
    photo_thumb = ImageTk.PhotoImage(thumb)

    merge_channel_thumbs[channel] = photo_thumb

    # update the thumbnail square
    thumb_frames[channel].config(image=photo_thumb, bg=None)
    thumb_frames[channel].image = photo_thumb

    # show resolution below
    w, h = original.size
    res_labels[channel].config(text=f"{w} × {h}")

    print(f"{channel} channel loaded: {path}")

def build_merge():
    clear_panel(content_frame)

    tk.Label(content_frame, text="CHANNEL PACKING",
             font=("Arial", 14), fg="green").pack(pady=5)
    tk.Label(content_frame, text="Drag textures onto the squares below:").pack()

    square_frame = tk.Frame(content_frame)
    square_frame.pack(pady=10)

    global thumb_frames, res_labels
    thumb_frames = {}
    res_labels = {}

    for idx, chan in enumerate(["R", "G", "B", "A"]):
        # channel container
        container = tk.Frame(square_frame)
        container.grid(row=0, column=idx, padx=10)

        # header row (name + clear button)
        header = tk.Frame(container)
        header.pack()

        label_name = tk.Label(header,
                              width=2,
                              height=1,
                              text=chan,
                              font=("Arial", 12, "bold"),
                              bg=("red" if chan == "R" else
                                  "green" if chan == "G" else
                                  "blue" if chan == "B" else "gray"),
                              fg="white")
        label_name.pack(side="left")

        btn_clear = tk.Button(header, text="✕", fg="black",
                              font=("Arial", 10, "bold"),
                              command=lambda c=chan: clear_channel(c))
        btn_clear.pack(side="right", padx=(115,0))

        # thumbnail frame of fixed pixel size
        frame_thumb = tk.Frame(container, width=DROP_SIZE[0], height=DROP_SIZE[1], bd=2, relief="ridge")
        frame_thumb.pack()
        frame_thumb.grid_propagate(False)

        # inside: a label to hold the thumbnail
        lbl_thumb = tk.Label(frame_thumb, bg="lightgray")
        lbl_thumb.place(x=0, y=0, width=DROP_SIZE[0], height=DROP_SIZE[1])

        # register DnD on the thumb label
        lbl_thumb.drop_target_register(DND_FILES)
        lbl_thumb.dnd_bind("<<Drop>>", lambda e, c=chan: merge_drop(e, c))

        thumb_frames[chan] = lbl_thumb

        # resolution label under thumbnail
        res_lbl = tk.Label(container, text="", font=("Arial", 10))
        res_lbl.pack(pady=(4,0))
        res_labels[chan] = res_lbl

    tk.Label(content_frame, text="Drag textures onto the squares above.").pack()
    
    button_container = tk.Frame(content_frame)
    button_container.pack(pady=10)
    
    tk.Button(button_container, text="Preview", font=("Arial", 15), command=create_merged_image).pack(side="left", padx=10)
    tk.Button(button_container, text="Save", font=("Arial", 15), command=save_merged_image).pack(side="left", padx=10)
    
    # Preview container
    preview_container = tk.Frame(content_frame)
    preview_container.pack(pady=20)
    
    tk.Label(preview_container, text="Preview", font=("Arial", 12, "bold")).pack()
    
    # Text input field
    global output_filename
    text_entry = tk.Entry(preview_container, textvariable=output_filename, width=40)
    text_entry.pack(pady=5)
    
    # Preview thumbnail frame of fixed pixel size (larger than channel thumbs)
    global preview_frame
    preview_size = (300, 300)
    frame_preview = tk.Frame(preview_container, width=preview_size[0], height=preview_size[1], bd=2, relief="ridge")
    frame_preview.pack()
    frame_preview.grid_propagate(False)
    
    # Inside: a label to hold the preview thumbnail
    preview_frame = tk.Label(frame_preview, bg="lightgray", text="No preview")
    preview_frame.place(x=0, y=0, width=preview_size[0], height=preview_size[1])
    

def build_unpack():
    clear_panel(content_frame)

    tk.Label(content_frame, text="UNPACKING TEXTURES", font=("Arial", 14), fg="blue").pack(pady=5)

  
    tk.Label(content_frame, text="Drag a texture here:").pack(pady=(10,5))

    drop_frame = tk.Frame(content_frame, width=300, height=300, bd=2, relief="ridge")
    drop_frame.pack()
    drop_frame.grid_propagate(False)

    big_drop_label = tk.Label(drop_frame, text="Drop Image Here", bg="lightgray")
    big_drop_label.place(x=0, y=0, width=300, height=300)

    # register DnD
    big_drop_label.drop_target_register(DND_FILES)
    big_drop_label.dnd_bind("<<Drop>>", on_unpack_drop)

    # store reference for later preview
    global unpack_drop_label
    unpack_drop_label = big_drop_label

    tk.Label(content_frame, text="").pack(pady=(5,10))  # spacer


    gamma_frame = tk.Frame(content_frame)
    gamma_frame.pack(pady=(0,15))

    global gamma_correction
   
    tk.Checkbutton(gamma_frame, text="GIMP Gamma Correction", command=toggle_gamma_correction, variable=gamma_correction).pack()

  
    action_frame = tk.Frame(content_frame)
    action_frame.pack(pady=10)

    tk.Button(action_frame, text="Preview", font=("Arial", 13), command=unpack_preview).pack(side="left", padx=10)
    tk.Button(action_frame, text="Save", font=("Arial", 13), command=save_unpacked_channels).pack(side="left", padx=10)

   
    tk.Label(content_frame, text="Channel Previews:", font=("Arial", 12, "bold")).pack(pady=(15,5))

    channels_frame = tk.Frame(content_frame)
    channels_frame.pack()

    global unpack_preview_frames
    unpack_preview_frames = {}

    preview_size = (180, 180)

    for idx, chan in enumerate([ "R", "G", "B", "A"]):
        container = tk.Frame(channels_frame)
        container.grid(row=0, column=idx, padx=5)

        # Channel name
        bg_color = "red" if chan=="R" else "green" if chan=="G" else "blue" if chan=="B" else "gray"
        tk.Label(container, text=chan, font=("Arial", 12, "bold"), bg=bg_color, fg="white", width=2, height=1).pack()

       
        frame_preview = tk.Frame(container, width=preview_size[0], height=preview_size[1], bd=2, relief="ridge")
        frame_preview.pack()
        frame_preview.grid_propagate(False)

        preview_label = tk.Label(frame_preview, bg="lightgray")
        preview_label.place(x=0, y=0, width=preview_size[0], height=preview_size[1])

        unpack_preview_frames[chan] = preview_label

def on_unpack_drop(event):
    global unpack_image
    raw = event.data.strip("{}")
    path = raw.split()[-1]
    if os.path.isfile(path):
        unpack_path_var.set(path)
        # show big preview
        
        unpack_image = Image.open(path)
        thumb = unpack_image.copy()
        thumb.thumbnail((300,300), Image.LANCZOS)
        photo = ImageTk.PhotoImage(thumb)

        unpack_drop_label.config(image=photo, bg=None)
        unpack_drop_label.image = photo

        print("Unpacked texture path:", path)

def toggle_gamma_correction():
    
    global gamma_correction
    
    # gamma_correction.set(not gamma_correction.get())
    print("Gamma correction set to:", gamma_correction.get())


def unpack_preview():
    global gamma_correction
    global unpack_channels_list
    print("Gamma correction:", gamma_correction.get())
    if (gamma_correction.get()):
        unpack_channels_list = unpack_channels_gamma_correction(unpack_path_var.get())
    else:
        unpack_channels_list = unpack_channels_no_gamma_correction(unpack_path_var.get())  
   
 
    # Show R,G,B,A
    for idx, c in enumerate(["R","G","B","A"]):
        thumb = unpack_channels_list[idx].resize((160,160), Image.LANCZOS)
        photo = ImageTk.PhotoImage(thumb)
        unpack_preview_frames[c].config(image=photo, bg=None)
        unpack_preview_frames[c].image = photo

def save_unpacked_channels():
    global unpack_image
    global unpack_images
    
    # Create directory with the unpack_image name
    if unpack_path_var.get():
        base_name = os.path.splitext(os.path.basename(unpack_path_var.get()))[0]
        output_dir = f"{base_name}_unpacked"
        os.makedirs(output_dir, exist_ok=True)
    
    for idx, c in enumerate(unpack_channels_list):
        channel_names = ["R", "G", "B", "A"]
        c.save(f"{output_dir}/{base_name}_{channel_names[idx]}.png")

def show_panel(name):
    global current_panel
    global gamma_correction
    if name == "merge":
        build_merge()
        gamma_correction.set(False)
    elif name == "unpack":
        build_unpack()
    current_panel = name

# Show merge by default
show_merge()

root.mainloop()

