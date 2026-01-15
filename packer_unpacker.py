from PIL import Image, ImageTk
import os
import FreeSimpleGUI as sg
import numpy as np
import tkinter as tk
from tkinter import filedialog
from tkinterdnd2 import TkinterDnD, DND_FILES



root = TkinterDnD.Tk()  
root.title("Texture Channel Unpacker/Packer")
root.geometry("800x850")
btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)
gamma_correction = tk.BooleanVar(value=False)
content_frame = tk.Frame(root)
content_frame.pack(fill="both", expand=True)
merge_channel_paths = {"R": None, "G": None, "B": None, "A": None}
merge_channel_images = {}    # store full‑size PIL images
merge_channel_thumbs = {}    # store thumbnails displayed
merge_channels_active = {"R": False, "G": False, "B": False, "A": False}
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

# This is the text message after doing a certain action
action_label = tk.Label(content_frame, text="", font=("Arial", 12), fg="purple")





def validate_sizes(paths):
    global action_label
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
            action_label.config(
                text=
                 f"Size mismatch:\n"
                f"  File: {img['name']} ({img['size'][0]}x{img['size'][1]})\n"
                f"  Expected: {expected_size[0]}x{expected_size[1]}\n"
                f"  Reference: {reference['name']}"
                
            )
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
    global action_label
    # Find expected size (largest image)
    size = validate_sizes(paths)
    if size is None:
        action_label.config(text=f"No input images provided for channel packing.")
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


def preview_channel_packed_image(): 
    global merged_image
    if (merged_image is None):
        return
    
    new_window = tk.Toplevel(root)
    new_window.title("Merged Image Preview - Use mouse wheel or +/- to zoom")
    new_window.geometry("600x600")
    
    # Create a frame with scrollbars
    canvas_frame = tk.Frame(new_window)
    canvas_frame.pack(fill="both", expand=True)
    
    canvas = tk.Canvas(canvas_frame, bg="gray")
    h_scrollbar = tk.Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
    v_scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
    canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
    
    h_scrollbar.pack(side="bottom", fill="x")
    v_scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    
    # Zoom variables
    zoom_factor = 1.0
    original_size = merged_image.size
    
    # Create initial image
    current_image = merged_image
    photo = ImageTk.PhotoImage(current_image)
    image_item = canvas.create_image(0, 0, anchor="nw", image=photo)
    canvas.image = photo  # Keep reference
    
    def update_canvas_scroll_region():
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    def zoom_image(factor):
        nonlocal zoom_factor, current_image, photo, image_item
        zoom_factor *= factor
        
        # Calculate new size
        new_width = int(original_size[0] * zoom_factor)
        new_height = int(original_size[1] * zoom_factor)
        
        # Resize image
        current_image = merged_image.resize((new_width, new_height), Image.LANCZOS)
        photo = ImageTk.PhotoImage(current_image)
        
        # Update canvas image
        canvas.delete(image_item)
        image_item = canvas.create_image(0, 0, anchor="nw", image=photo)
        canvas.image = photo  # Keep reference
        
        update_canvas_scroll_region()
        new_window.title(f"Merged Image Preview - Zoom: {zoom_factor:.2f}x - Use mouse wheel or +/- to zoom")
    
    def on_mousewheel(event):
        if event.delta > 0:
            zoom_image(1.2)
        else:
            zoom_image(0.8)
    
    def on_key_press(event):
        if event.keysym == "plus" or event.keysym == "equal":
            zoom_image(1.2)
        elif event.keysym == "minus":
            zoom_image(0.8)
        elif event.keysym == "0":
            # Reset to original size
            nonlocal zoom_factor
            zoom_factor = 1.0
            zoom_image(1.0)
    
    # Bind events
    canvas.bind("<MouseWheel>", on_mousewheel)
    new_window.bind("<Key>", on_key_press)
    new_window.focus_set()  # Make window focusable for keyboard events
    
    update_canvas_scroll_region()
    

def preview_unpacked_channel_image():
    global unpack_channels_list, merge_channels_active
    if not unpack_channels_list:
        return
    
    # Find which channel is active
    active_channel = None
    channel_names = ["R", "G", "B", "A"]
    for i, channel in enumerate(channel_names):
        if merge_channels_active[channel]:
            active_channel = i
            break
    
    if active_channel is None:
        return
    
    new_window = tk.Toplevel(root)
    new_window.title(f"{channel_names[active_channel]} Channel Preview - Use mouse wheel or +/- to zoom")
    new_window.geometry("600x600")
    
    # Create a frame with scrollbars
    canvas_frame = tk.Frame(new_window)
    canvas_frame.pack(fill="both", expand=True)
    
    canvas = tk.Canvas(canvas_frame, bg="gray")
    h_scrollbar = tk.Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
    v_scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
    canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
    
    h_scrollbar.pack(side="bottom", fill="x")
    v_scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    
    # Zoom variables
    zoom_factor = 1.0
    
    # Get the active channel image
    channel_img = unpack_channels_list[active_channel]
    original_size = channel_img.size
    
    # Convert grayscale to RGB for display
    current_image = Image.merge("RGB", (channel_img, channel_img, channel_img))
    photo = ImageTk.PhotoImage(current_image)
    image_item = canvas.create_image(0, 0, anchor="nw", image=photo)
    canvas.image = photo  # Keep reference
    
    def update_canvas_scroll_region():
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    def zoom_image(factor):
        nonlocal zoom_factor, current_image, photo, image_item
        zoom_factor *= factor
        
        # Calculate new size
        new_width = int(original_size[0] * zoom_factor)
        new_height = int(original_size[1] * zoom_factor)
        
        # Resize image
        resized_channel = channel_img.resize((new_width, new_height), Image.LANCZOS)
        current_image = Image.merge("RGB", (resized_channel, resized_channel, resized_channel))
        photo = ImageTk.PhotoImage(current_image)
        
        # Update canvas image
        canvas.delete(image_item)
        image_item = canvas.create_image(0, 0, anchor="nw", image=photo)
        canvas.image = photo  # Keep reference
        
        update_canvas_scroll_region()
        new_window.title(f"Unpacked Channels Preview - Zoom: {zoom_factor:.2f}x - Use mouse wheel or +/- to zoom")
    
    def on_mousewheel(event):
        if event.delta > 0:
            zoom_image(1.2)
        else:
            zoom_image(0.8)
    
    def on_key_press(event):
        if event.keysym == "plus" or event.keysym == "equal":
            zoom_image(1.2)
        elif event.keysym == "minus":
            zoom_image(0.8)
        elif event.keysym == "0":
            # Reset to original size
            nonlocal zoom_factor
            zoom_factor = 1.0
            zoom_image(1.0)
    
    # Bind events
    canvas.bind("<MouseWheel>", on_mousewheel)
    new_window.bind("<Key>", on_key_press)
    new_window.focus_set()  # Make window focusable for keyboard events
    
    # Add labels to identify channels
    label_frame = tk.Frame(new_window)
    label_frame.pack(side="bottom", fill="x")
    
    
    
    update_canvas_scroll_region()


def set_active_channel(channel):
    global merge_channels_active
    # Reset all channels to False
    for key in merge_channels_active:
        merge_channels_active[key] = False
    # Set only the clicked channel to True
    merge_channels_active[channel] = True
    print(f"Active channel set to: {channel}")


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
    global action_label
    global merged_image
    print("merged image to save:", merged_image)
    if (merged_image is None):
        action_label.config(text="No merged image to save.")
        print("No merged image to save.")
        return
    merged_image.save(output_filename.get() or "merged_texture.png")
    action_label.config(text=f"File saved: {output_filename.get() or 'merged_texture.png'}")
    

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
    
    global action_label
    action_label = tk.Label(content_frame, text="", font=("Arial", 12), fg="purple")
    action_label.pack(pady=1)
    
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
    
    # Inside: a button to hold the preview thumbnail
    preview_frame = tk.Button(frame_preview, bg="lightgray", text="No preview", command=preview_channel_packed_image)
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


    # Input field for choosing PNG file
    input_frame = tk.Frame(content_frame)
    input_frame.pack(pady=10)
    
    tk.Label(input_frame, text="Or choose PNG file:").pack(side="left", padx=5)
    png_entry = tk.Entry(input_frame, textvariable=unpack_path_var, width=40, state="readonly")
    png_entry.pack(side="left", padx=5)
   
    
    tk.Button(input_frame, text="Browse", command=browse_png).pack(side="left", padx=5)

    gamma_frame = tk.Frame(content_frame)
    gamma_frame.pack(pady=(0,15))
    global gamma_correction
    tk.Checkbutton(gamma_frame, text="GIMP Gamma Correction", command=toggle_gamma_correction, variable=gamma_correction).pack()

    
    action_frame = tk.Frame(content_frame)
    action_frame.pack(pady=10)
   

    tk.Button(action_frame, text="Preview", font=("Arial", 13), command=unpack_preview).pack(side="left", padx=10)
    tk.Button(action_frame, text="Save", font=("Arial", 13), command=save_unpacked_channels).pack(side="left", padx=10)

    global action_label
    action_label = tk.Label(content_frame, text="", font=("Arial", 12), fg="purple")
    action_label.pack(pady=1)
   
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

        preview_button = tk.Button(frame_preview, bg="lightgray", command=lambda c=chan: (set_active_channel(c), preview_unpacked_channel_image()))
        preview_button.place(x=0, y=0, width=preview_size[0], height=preview_size[1])

        unpack_preview_frames[chan] = preview_button

def browse_png():
        global unpack_image
        global action_label
        global content_frame
        global unpack_path_var
        filename = filedialog.askopenfilename(
            title="Select PNG file",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if filename:
            if not filename.lower().endswith(".png"):
                print("Unsupported file type. Please select a PNG file.")
                return
            unpack_path_var.set(filename)
            # Load and preview the selected image
            unpack_image = Image.open(filename)
            
            thumb = unpack_image.copy()
            thumb.thumbnail((300,300), Image.LANCZOS)
            photo = ImageTk.PhotoImage(thumb)
            action_label.config(text=f"File loaded")
            
            unpack_drop_label.config(image=photo, bg=None)
            unpack_drop_label.image = photo


def on_unpack_drop(event):
    global unpack_image
    global content_frame
    global action_label
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
    
        action_label.config(text=f"File loaded")
        print("Loaded file: " + path)

def toggle_gamma_correction():
    return
    global gamma_correction
    
    # gamma_correction.set(not gamma_correction.get())
    
    print("Gamma correction set to:", gamma_correction.get())


def unpack_preview():
    global gamma_correction
    global unpack_channels_list
    global unpack_path_var
    global action_label
    global unpack_image
    if not unpack_image:
        action_label.config(text="No image loaded to preview")
        return
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
    global action_label
    global unpack_path_var
    print(f"Unpack path var: {unpack_path_var.get()}")
    # Check if there's an image to save
    if not unpack_path_var.get() or not unpack_channels_list:
        action_label.config(text="No image to save")
        return
    
    output_dir = "unpacked_channels"
    
    # Create directory with the unpack_image name
    if unpack_path_var.get():
        base_name = os.path.splitext(os.path.basename(unpack_path_var.get()))[0]
        output_dir = f"{base_name}_unpacked"
        os.makedirs(output_dir, exist_ok=True)
    
    for idx, c in enumerate(unpack_channels_list):
        channel_names = ["R", "G", "B", "A"]
        c.save(f"{output_dir}/{base_name}_{channel_names[idx]}.png")
    action_label.config(text=f"Files saved to: \n/{output_dir}/{base_name}")

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

