from texture_processor import *
import tkinter as tk
from tkinter import ttk
import numpy as np
from PIL import Image
import customtkinter as ctk
from CTkColorPicker import *
from tkinter import colorchooser
from os.path import isfile, join

def get_color_bit_depth(im: Image.Image) -> Tuple[int, int]:
    mode = im.mode
    # map Pillow modes to bits-per-channel
    bits_map = {
        "1": 1,    # 1-bit
        "L": 8,
        "P": 8,
        "RGB": 8,
        "RGBA": 8,
        "CMYK": 8,
        "I;16": 16,
        "I;16L": 16,
        "I;16B": 16,
        "I": 32,
        "F": 32,
    }

    bpc = bits_map.get(mode, None)
    if bpc is None:
        raise ValueError(f"Unknown mode: {mode}")

    # bits per pixel = bits per channel × number of channels
    channels = len(im.getbands())
    bpp = bpc * channels

    return bpc, bpp

def convert_image_to_bit_depth(image: Image.Image, target_bpc: int) -> Image.Image:
    """
    Convert image to target color bit depth.
    
    Args:
        image: Input PIL Image
        target_bpc: Target bits per channel (1, 8, 16, 32)
    
    Returns:
        PIL Image converted to target bit depth
    """
    if target_bpc == 1:
        return image.convert("1")
    elif target_bpc == 8:
        return image.convert("RGB")
    elif target_bpc == 16:
        return image.convert("I;16")
    elif target_bpc == 32:
        return image.convert("F")
    else:
        raise ValueError(f"Unsupported target bits per channel: {target_bpc}")


class BasePanel:
    """Base class for UI panels"""
    
    def __init__(self, parent: tk.Widget):
        self.parent = parent
        self.frame = tk.Frame(parent)
        self.status_label = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Override in subclasses"""
        pass
    
    def show(self):
        """Show this panel"""
        self.frame.pack(fill="both", expand=True)
    
    def hide(self):
        """Hide this panel"""
        self.frame.pack_forget()
    
    def update_status(self, message: str, color: str = "purple"):
        """Update status message"""
        if self.status_label:
            self.status_label.config(text=message, fg=color)
    
    def show_error(self, message: str):
        """Show error message"""
        messagebox.showerror("Error", message)
        self.update_status(f"Error: {message}", "red")
    
    def show_success(self, message: str):
        """Show success message"""
        self.update_status(message, "green")


class ChannelThumbnail:
    """Widget for displaying channel thumbnails with drag-and-drop"""
    
    def __init__(self, parent: tk.Widget, channel: str, on_drop_callback, on_clear_callback, on_set_channel_image_with_another_channel, on_browse_file, on_color_select):
        self.channel = channel
        self.on_drop = on_drop_callback
        self.on_clear = on_clear_callback
        self.on_set_channel_image_with_another_channel = on_set_channel_image_with_another_channel
        self.on_browse_file = on_browse_file
        self.on_color_select = on_color_select
        self._create_widget(parent)
    
    def _create_widget(self, parent):
        """Create the thumbnail widget"""
        # Container
        self.container = tk.Frame(parent)

        additional_container = tk.Frame(self.container)
        additional_container.pack(pady=(0, 4))
        
        # Header with channel name and clear button
        header = tk.Frame(self.container)
        header.pack()
        
        # Additional container below header
       
       
       
       
        # Channel color mapping
        color_map = {
            ChannelType.RED.value: "red",
            ChannelType.GREEN.value: "green", 
            ChannelType.BLUE.value: "blue",
            ChannelType.ALPHA.value: "gray"
        }
        
        tk.Label(additional_container, text="Set source as", font=("Arial", 10)).pack(padx=(0, 4))
        
        # Add buttons for each color in additional_container
        for channel_type, color in color_map.items():
            btn = tk.Button(additional_container, text=channel_type, bg=color, fg="white", width=4, height=1, 
                            command=lambda ch=channel_type: self.on_set_channel_image_with_another_channel(self.channel, ch))
            btn.pack(side="left", padx=2)
        
        label = tk.Label(header, text=self.channel, font=("Arial", 12, "bold"),
                        bg=color_map[self.channel], fg="white", width=2, height=1)
        label.pack(side="left")
        
        clear_btn = tk.Button(header, text="✕", fg="black", font=("Arial", 10, "bold"),
                             command=lambda: self.on_clear(self.channel))
        clear_btn.pack(side="right", padx=(5, 0))
        
        browse_btn = tk.Button(header, text="📁", fg="black", font=("Arial", 10, "bold"),
                              command=lambda: self.on_browse_file(self.channel))
        browse_btn.pack(side="right", padx=(60, 0))
        
        blank_image_color_btn = tk.Button(header, text="🎨", fg="black", font=("Arial", 10, "bold"),
                            command=lambda: self.open_color_picker())
        blank_image_color_btn.pack(side="right", padx=(5, 0))
        
        # Thumbnail frame
        thumb_frame = tk.Frame(self.container, width=ImageConfig.DROP_SIZE[0], 
                              height=ImageConfig.DROP_SIZE[1], bd=2, relief="ridge")
        thumb_frame.pack()
        thumb_frame.grid_propagate(False)
        
        # Thumbnail label
        self.thumb_label = tk.Label(thumb_frame, bg="lightgray")
        self.thumb_label.place(x=0, y=0, width=ImageConfig.DROP_SIZE[0], height=ImageConfig.DROP_SIZE[1])
        
        # Setup drag and drop
        self.thumb_label.drop_target_register(DND_FILES)
        self.thumb_label.dnd_bind("<<Drop>>", lambda e: self.on_drop(e, self.channel))
        
        # Resolution label
        self.res_label = tk.Label(self.container, text="", font=("Arial", 10))
        self.res_label.pack(pady=(4, 0))
    
    def update_thumbnail(self, image: Image.Image, image_path: str):
        """Update the thumbnail display"""
        # Create and set thumbnail
        thumb = ImageProcessor.create_thumbnail(image, ImageConfig.DROP_SIZE)
        photo = ImageTk.PhotoImage(thumb)
        self.thumb_label.config(image=photo, bg=None)
        self.thumb_label.image = photo
        
        # Update resolution display
        w, h = image.size
        self.res_label.config(text=f"{w} × {h}")
    
    def clear_thumbnail(self):
        """Clear the thumbnail display"""
        self.thumb_label.config(image="", bg="lightgray")
        self.thumb_label.image = None
        self.res_label.config(text="")
    def open_color_picker(self):
        # This uses CustoMTkinter Color Picker
        # pick_color = AskColor() # open the color picker
        # color = pick_color.get() # get the color string
        # print(color)
        # button.configure(fg_color=color)
        color_code = colorchooser.askcolor(title ="Choose color for empty image channel")
        hex_color = color_code[1]
        if hex_color:
            self.on_color_select(self.channel, hex_color)
            return
        return
        
        

class ChannelPackerPanel(BasePanel):
    """Panel for channel packing functionality"""
    
    def __init__(self, parent: tk.Widget):
        self.model = ChannelPackerModel()
        self.model.add_observer(self)
        self.thumbnails = {}
        self.drop_handler = FileDropHandler(self._on_file_dropped)
        self.preview_widget = None
        self.output_filename_var = tk.StringVar(value="packed_texture.png")
        self.output_directory_var = tk.StringVar(value=os.getcwd())
        self.bit_depth_var = tk.StringVar(value="8")
        
        
        super().__init__(parent)
    
    def _setup_ui(self):
        """Setup the channel packing UI"""
        # Title
        tk.Label(self.frame, text="CHANNEL PACKING", font=("Arial", 14), fg="green").pack(pady=5)
        tk.Label(self.frame, text="Drag textures onto the squares below:").pack()
        
        # Channel thumbnails
        self._setup_channel_thumbnails()
        
        # Control buttons
        self._setup_controls()
        
        # Status label
        self.status_label = tk.Label(self.frame, text="", font=("Arial", 12), fg="purple")
        self.status_label.pack(pady=1)
        
        # Preview section
        self._setup_preview()
    
    def _setup_channel_thumbnails(self):
        """Setup channel thumbnail widgets"""
        square_frame = tk.Frame(self.frame)
        square_frame.pack(pady=5)
        
        for idx, channel_type in enumerate(ChannelType):
            channel = channel_type.value
            thumbnail = ChannelThumbnail(
                square_frame, channel,
                self._handle_channel_drop,
                self.model.clear_channel,
                self.model.set_channel_image_with_another_channel,
                self._browse_file_for_channel,
                self.model.set_channel_image_to_color
            )
            thumbnail.container.grid(row=0, column=idx, padx=10)
            self.thumbnails[channel] = thumbnail
    
    def _setup_controls(self):
        """Setup control buttons"""
        button_container = tk.Frame(self.frame)
        button_container.pack(pady=5)
        
        tk.Button(button_container, text="Preview", font=("Arial", 15),
                 command=self._create_preview).pack(side="left", padx=10)
        tk.Button(button_container, text="Save", font=("Arial", 15),
                 command=self._save_image).pack(side="left", padx=10)
        
        # Bit depth selection
        depth_frame = tk.Frame(self.frame)
        depth_frame.pack(pady=0)
        
        tk.Label(depth_frame, text="Color Depth:", font=("Arial", 12)).pack(side="left", padx=5)
        
        tk.Radiobutton(depth_frame, text="8-bit (L)", variable=self.bit_depth_var, 
                      value="8", font=("Arial", 10)).pack(side="left", padx=2)
        tk.Radiobutton(depth_frame, text="16-bit (I;16)", variable=self.bit_depth_var, 
                      value="16", font=("Arial", 10)).pack(side="left", padx=2)
        tk.Radiobutton(depth_frame, text="24-bit (RGB)", variable=self.bit_depth_var, 
                      value="24", font=("Arial", 10)).pack(side="left", padx=2)
        tk.Radiobutton(depth_frame, text="32-bit (RGBA)", variable=self.bit_depth_var, 
                      value="32", font=("Arial", 10)).pack(side="left", padx=2)
        tk.Label(self.frame, text="Downgrading color depth not supported", fg="red").pack(pady=0)
    
    def _setup_preview(self):
        """Setup preview section"""
        preview_container = tk.Frame(self.frame)
        preview_container.pack(pady=5)
        
        tk.Label(preview_container, text="Preview", font=("Arial", 12, "bold")).pack()
        
        # Filename entry
        filename_entry = tk.Entry(preview_container, textvariable=self.output_filename_var, width=40)
        filename_entry.pack(pady=5)
        
        # Directory save entry
        dir_frame = tk.Frame(preview_container)
        dir_frame.pack(pady=5)
        
        tk.Label(dir_frame, text="Save to:").pack(side="left", padx=(0, 5))
        dir_entry = tk.Entry(dir_frame, textvariable=self.output_directory_var, width=100)
        dir_entry.pack(side="left", padx=5)
        tk.Button(dir_frame, text="Browse", command=self._browse_directory).pack(side="left", padx=5)
        
        # Preview frame
        preview_frame = tk.Frame(preview_container, width=ImageConfig.PREVIEW_SIZE[0],
                               height=ImageConfig.PREVIEW_SIZE[1], bd=2, relief="ridge")
        preview_frame.pack()
        preview_frame.grid_propagate(False)
        
        self.preview_widget = tk.Button(preview_frame, bg="lightgray", text="No preview",
                                       command=self._show_full_preview)
        self.preview_widget.place(x=0, y=0, width=ImageConfig.PREVIEW_SIZE[0], 
                                 height=ImageConfig.PREVIEW_SIZE[1])
    
    def _handle_channel_drop(self, event, channel: str):
        """Handle drag-and-drop for channel thumbnails"""
        print("_handle_channel_drop")
        self.drop_handler.handle_drop(event, channel=channel)
    
    def _on_file_dropped(self, file_path: str, channel: str):
        """Handle file drop on channel"""
        print("_on_file_dropped")
        try:
            self.model.set_channel_image(channel, file_path)
            self.output_directory_var.set(os.path.dirname(file_path))
        except Exception as e:
            self.show_error(str(e))
    
    def _create_preview(self):
        """Create preview of merged image"""
        try:
            # Get selected bit depth and convert to integer
            selected_bit_depth = int(self.bit_depth_var.get())
            self.model.create_merged_image(target_bit_depth=selected_bit_depth)
        except Exception as e:
            self.show_error(str(e))
    
    def _save_image(self):
        """Save the merged image"""
        try:
            filename = self.output_filename_var.get() or 'merged_texture.png'
            directory = self.output_directory_var.get() or os.getcwd()
            full_path = os.path.join(directory, filename)
            
            # Ensure we have a merged image with the current bit depth settings
            if self.model.merged_image is None:
                selected_bit_depth = int(self.bit_depth_var.get())
                self.model.create_merged_image(target_bit_depth=selected_bit_depth)
            
            self.model.save_merged_image(full_path)
        except Exception as e:
            self.show_error(str(e))
    
    def _browse_directory(self):        
        """Browse for output directory"""
        directory = filedialog.askdirectory(title="Select output directory")
        if directory:
            self.output_directory_var.set(directory)
    
    def _show_full_preview(self):
        """Show full-size preview in new window"""
        if self.model.merged_image:
            viewer = ZoomableImageViewer(self.frame, "Merged Image Preview")
            viewer.display_image(self.model.merged_image)
    
    
    
    # Model observer methods
    def on_channel_updated(self, channel: str, image: Image.Image, path: str):
        """Called when a channel is updated"""
        self.thumbnails[channel].update_thumbnail(image, path)
        
        color_bit_depth_number = get_color_bit_depth(image)[1]
        # print("Color bit depth number:", color_bit_depth_number[1])
        self.bit_depth_var.set(str(color_bit_depth_number))
        
        self.show_success(f"{channel} channel loaded: {os.path.basename(path)}")
    
    def on_channel_cleared(self, channel: str):
        """Called when a channel is cleared"""
        self.thumbnails[channel].clear_thumbnail()
        self.show_success(f"{channel} channel cleared")
    
    def on_image_merged(self, image: Image.Image):
        """Called when image is merged"""
        # Update preview thumbnail
        thumb = ImageProcessor.create_thumbnail(image, ImageConfig.PREVIEW_SIZE)
        photo = ImageTk.PhotoImage(thumb)
        self.preview_widget.config(image=photo, bg=None, text="")
        self.preview_widget.image = photo
        self.show_success("Image merged successfully")
    
    def on_image_saved(self, path: str):
        """Called when image is saved"""
        self.show_success(f"File saved: {path}")
        
    def _browse_file_for_channel(self, channel: str):
        """Browse for file for a specific channel"""
        filetypes = [("PNG files", "*.png"), ("DDS files", "*.dds"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(title=f"Select image file for {channel} channel", filetypes=filetypes)
        
        if filename:
            try:
                self.model.set_channel_image(channel, filename)
                self.output_directory_var.set(os.path.dirname(filename))
            except Exception as e:
                self.show_error(str(e))


class ChannelPreviewWidget:
    """Widget for previewing individual channels"""
    
    def __init__(self, parent: tk.Widget, channel: str, on_click_callback):
        self.channel = channel
        self.on_click = on_click_callback
        self._create_widget(parent)
    
    def _create_widget(self, parent):
        """Create the preview widget"""
        self.container = tk.Frame(parent)
        
        # Channel name with color
        color_map = {
            ChannelType.RED.value: "red",
            ChannelType.GREEN.value: "green",
            ChannelType.BLUE.value: "blue", 
            ChannelType.ALPHA.value: "gray"
        }
        
        tk.Label(self.container, text=self.channel, font=("Arial", 12, "bold"),
                bg=color_map[self.channel], fg="white", width=2, height=1).pack()
        
        # Preview frame
        preview_frame = tk.Frame(self.container, width=ImageConfig.CHANNEL_PREVIEW_SIZE[0],
                               height=ImageConfig.CHANNEL_PREVIEW_SIZE[1], bd=2, relief="ridge")
        preview_frame.pack()
        preview_frame.grid_propagate(False)
        
        self.preview_button = tk.Button(preview_frame, bg="lightgray",
                                       command=lambda: self.on_click(self.channel))
        self.preview_button.place(x=0, y=0, width=ImageConfig.CHANNEL_PREVIEW_SIZE[0],
                                 height=ImageConfig.CHANNEL_PREVIEW_SIZE[1])
    
    def update_preview(self, image: Image.Image):
        """Update the preview with channel image"""
        # Convert grayscale to RGB for display
        rgb_image = Image.merge("RGB", (image, image, image))
        thumb = ImageProcessor.create_thumbnail(rgb_image, ImageConfig.CHANNEL_PREVIEW_SIZE)
        photo = ImageTk.PhotoImage(thumb)
        self.preview_button.config(image=photo, bg=None)
        self.preview_button.image = photo
    
    def clear_preview(self):
        """Clear the preview"""
        self.preview_button.config(image="", bg="lightgray")
        self.preview_button.image = None
        
 

class ChannelUnpackerPanel(BasePanel):
    """Panel for channel unpacking functionality"""
    
    def __init__(self, parent: tk.Widget):
        self.model = ChannelUnpackerModel()
        self.model.add_observer(self)
        self.drop_handler = FileDropHandler(self._on_file_dropped)
        self.file_path_var = tk.StringVar()
        self.gamma_correction_var = tk.BooleanVar(value=False)
        self.drop_label = None
        self.channel_previews = {}
        self.active_channel = None
        super().__init__(parent)
    
    def _setup_ui(self):
        """Setup the channel unpacking UI"""
        # Title
        tk.Label(self.frame, text="CHANNEL UNPACKING", font=("Arial", 14), fg="blue").pack(pady=5)
        
        # Drop area
        self._setup_drop_area()
        
        # File selection
        self._setup_file_selection()
        
        # Options
        self._setup_options()
        
        # Controls
        self._setup_controls()
        
        # Status label
        self.status_label = tk.Label(self.frame, text="", font=("Arial", 12), fg="purple")
        self.status_label.pack(pady=1)
        
        # Channel previews
        self._setup_channel_previews()
    
    def _setup_drop_area(self):
        """Setup drag-and-drop area"""
        tk.Label(self.frame, text="Drag a texture here:").pack(pady=(10, 5))
        
        drop_frame = tk.Frame(self.frame, width=ImageConfig.PREVIEW_SIZE[0],
                             height=ImageConfig.PREVIEW_SIZE[1], bd=2, relief="ridge")
        drop_frame.pack()
        drop_frame.grid_propagate(False)
        
        self.drop_label = tk.Label(drop_frame, text="Drop Image Here", bg="lightgray")
        self.drop_label.place(x=0, y=0, width=ImageConfig.PREVIEW_SIZE[0],
                             height=ImageConfig.PREVIEW_SIZE[1])
        
        # Setup drag and drop
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind("<<Drop>>", self.drop_handler.handle_drop)
    
    def _setup_file_selection(self):
        """Setup file selection controls"""
        input_frame = tk.Frame(self.frame)
        input_frame.pack(pady=10)
        
        tk.Label(input_frame, text="Or choose file:").pack(side="left", padx=5)
        file_entry = tk.Entry(input_frame, textvariable=self.file_path_var, width=40, state="readonly")
        file_entry.pack(side="left", padx=5)
        tk.Button(input_frame, text="Browse", command=self._browse_file).pack(side="left", padx=5)
    
    def _setup_options(self):
        """Setup option controls"""
        options_frame = tk.Frame(self.frame)
        options_frame.pack(pady=(0, 15))
        
        tk.Checkbutton(options_frame, text="Apply Gamma Correction",
                      variable=self.gamma_correction_var,
                      command=self._on_gamma_changed).pack()
    
    def _setup_controls(self):
        """Setup control buttons"""
        controls_frame = tk.Frame(self.frame)
        controls_frame.pack(pady=10)
        
        tk.Button(controls_frame, text="Preview", font=("Arial", 13),
                 command=self._create_preview).pack(side="left", padx=10)
        tk.Button(controls_frame, text="Save Channels", font=("Arial", 13),
                 command=self._save_channels).pack(side="left", padx=10)
    
    def _setup_channel_previews(self):
        """Setup channel preview widgets"""
        tk.Label(self.frame, text="Channel Previews:", font=("Arial", 12, "bold")).pack(pady=(15, 5))
        
        channels_frame = tk.Frame(self.frame)
        channels_frame.pack()
        
        for idx, channel_type in enumerate(ChannelType):
            channel = channel_type.value
            preview = ChannelPreviewWidget(channels_frame, channel, self._on_channel_clicked)
            preview.container.grid(row=0, column=idx, padx=5)
            self.channel_previews[channel] = preview
    
    def _on_file_dropped(self, file_path: str):
        """Handle file drop"""
        try:
            self.model.load_image(file_path)
            self.file_path_var.set(file_path)
        except Exception as e:
            self.show_error(str(e))
    
    def _browse_file(self):
        """Browse for file"""
        filetypes = [("PNG files", "*.png"), ("DDS files", "*.dds"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(title="Select image file", filetypes=filetypes)
        
        if filename:
            try:
                self.model.load_image(filename)
                self.file_path_var.set(filename)
            except Exception as e:
                self.show_error(str(e))
    
    def _on_gamma_changed(self):
        """Handle gamma correction option change"""
        self.model.apply_gamma_correction = self.gamma_correction_var.get()
    
    def _create_preview(self):
        """Create channel preview"""
        try:
            self.model.unpack_channels()
        except Exception as e:
            self.show_error(str(e))
    
    def _save_channels(self):
        """Save unpacked channels"""
        try:
            output_dir = f"{Path(self.model.source_path).stem}_unpacked" if self.model.source_path else "unpacked_channels"
            saved_files = self.model.save_channels(output_dir)
            self.show_success(f"Channels saved to: {output_dir}")
        except Exception as e:
            self.show_error(str(e))
    
    def _on_channel_clicked(self, channel: str):
        """Handle channel preview click"""
        self.active_channel = channel
        if self.model.unpacked_channels:
            channel_idx = list(ChannelType)[ord(channel) - ord('R') if channel != 'A' else 3].value
            channel_idx = ["R", "G", "B", "A"].index(channel)
            viewer = ZoomableImageViewer(self.frame, f"{channel} Channel Preview")
            
            # Convert grayscale channel to RGB for viewing
            channel_img = self.model.unpacked_channels[channel_idx]
            rgb_img = Image.merge("RGB", (channel_img, channel_img, channel_img))
            viewer.display_image(rgb_img)
    
    # Model observer methods
    def on_image_loaded(self, image: Image.Image, path: str):
        """Called when image is loaded"""
        # Update drop area preview
        thumb = ImageProcessor.create_thumbnail(image, ImageConfig.PREVIEW_SIZE)
        photo = ImageTk.PhotoImage(thumb)
        self.drop_label.config(image=photo, bg=None, text="")
        self.drop_label.image = photo
        self.show_success(f"Image loaded: {os.path.basename(path)}")
    
    def on_channels_unpacked(self, channels: List[Image.Image]):
        """Called when channels are unpacked"""
        # Update channel previews
        for idx, channel_type in enumerate(ChannelType):
            channel = channel_type.value
            self.channel_previews[channel].update_preview(channels[idx])
        self.show_success("Channels unpacked successfully")
    
    def on_channels_saved(self, files: List[str]):
        """Called when channels are saved"""
        self.show_success(f"Saved {len(files)} channel files")

class BulkChannelUnpackerPanel(BasePanel):
    """Panel for channel unpacking functionality"""
    
    def __init__(self, parent: tk.Widget):
        self.model = ChannelUnpackerModel()
        self.model.add_observer(self)
        # self.drop_handler = FileDropHandler(self._on_file_dropped)
        self.output_folder_var = tk.StringVar()
        self.input_folder_var = tk.StringVar()
        self.total_images = []
        self.processed_images = []

        super().__init__(parent)
    
    def _setup_ui(self):
        """Setup the channel unpacking UI"""
        # Title
        tk.Label(self.frame, text="BULK CHANNEL UNPACKING", font=("Arial", 14), fg="blue").pack(pady=5)
        
        # Input folder selection
        input_frame = tk.Frame(self.frame)
        input_frame.pack(pady=10, fill="x", padx=20)
        
        tk.Label(input_frame, text="Input Folder:", font=("Arial", 12)).pack(anchor="w")
        input_folder_frame = tk.Frame(input_frame)
        input_folder_frame.pack(fill="x", pady=(5, 15))
        
        self.input_folder_var = tk.StringVar()
        input_entry = tk.Entry(input_folder_frame, textvariable=self.input_folder_var, width=30, state="readonly", font=("Arial", 20))
        input_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        tk.Button(input_folder_frame, text="Browse", command=self._browse_input_folder).pack(side="right")
        
        # Output folder selection
        tk.Label(input_frame, text="Output Folder:", font=("Arial", 12)).pack(anchor="w")
        output_folder_frame = tk.Frame(input_frame)
        output_folder_frame.pack(fill="x", pady=5)
        
        self.output_folder_var = tk.StringVar()
        output_entry = tk.Entry(output_folder_frame, textvariable=self.output_folder_var, width=30, state="readonly", font=("Arial", 20))
        output_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        tk.Button(output_folder_frame, text="Browse", command=self._browse_output_folder).pack(side="right")

        tk.Button(self.frame, text="Start Unpacking", font=("Arial", 15), 
                 command=self._start_bulk_unpacking).pack(pady=20)
    
        # Progress bar
        self.progress_frame = tk.Frame(self.frame)
        self.progress_frame.pack(pady=10, fill="x", padx=20)
        
        tk.Label(self.progress_frame, text="Progress:", font=("Arial", 12)).pack(anchor="w")
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", pady=(5, 0))
        
        self.progress_label = tk.Label(self.progress_frame, text="Ready", font=("Arial", 10))
        self.progress_label.pack(anchor="w", pady=(2, 0))
        
        # Status label
        self.status_label = tk.Label(self.frame, text="", font=("Arial", 12), fg="purple")
        self.status_label.pack(pady=1)
    
        # Process log
        tk.Label(self.frame, text="Processing Log:", font=("Arial", 12, "bold")).pack(anchor="w", padx=20, pady=(10, 5))
        process_items_frame = tk.Frame(self.frame)
        process_items_frame.pack(pady=5, fill="both", expand=True, padx=20)
        
        scrollbar = ttk.Scrollbar(process_items_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.log_listbox = tk.Listbox(process_items_frame, height=15, yscrollcommand=scrollbar.set)
        self.log_listbox.pack(side="left", fill="both", expand=True)
        
        scrollbar.config(command=self.log_listbox.yview)
    
    
    
    def _start_bulk_unpacking(self):
        """Start the bulk unpacking process"""
        input_folder = self.input_folder_var.get()
        output_folder = self.output_folder_var.get()
        
        # Validation
        if not input_folder:
            self.show_error("Please select an input folder")
            return
        
        if not output_folder:
            self.show_error("Please select an output folder")
            return
        
        if not self.total_images:
            self.show_error("No supported image files found in input folder")
            return
        
        # Clear previous results
        self.log_listbox.delete(0, tk.END)
        self.processed_images = []
        self.progress_var.set(0)
        self.progress_label.config(text=f"Processing {len(self.total_images)} images...")
        
        # Build full paths
        image_paths = [os.path.join(input_folder, img) for img in self.total_images]
        
        try:
            # Start bulk unpacking with progress callback
            self.model.bulk_unpack_channels(
                image_paths, 
                output_folder, 
                progress_callback=self._update_progress
            )
        except Exception as e:
            self.show_error(str(e))
    
    def _browse_input_folder(self):
        """Browse for input folder"""
        folder = filedialog.askdirectory(title="Select input folder containing images")
        if folder:
            self.input_folder_var.set(folder)
            self.total_images = [f for f in os.listdir(folder) if isfile(join(folder, f)) and f.lower().endswith(('.png', '.dds'))]
            
    
    def _browse_output_folder(self):
        """Browse for output folder"""
        folder = filedialog.askdirectory(title="Select output folder for unpacked channels")
        if folder:
            self.output_folder_var.set(folder)
    
    def _update_progress(self, current_index: int, total_count: int, current_file: str):
        """Update progress display during bulk processing"""
        progress_percent = (current_index / total_count) * 100
        self.progress_var.set(progress_percent)
        self.progress_label.config(text=f"Processing {current_index + 1}/{total_count}: {os.path.basename(current_file)}")
        
        # Force UI update
        self.frame.update_idletasks()

    def _on_file_dropped(self, file_path: str):
        """Handle file drop"""
        return

    # Model observer methods
    def on_bulk_channels_unpacked(self, current_file: str, saved_files: List[str], progress: int, total: int):
        """Called when a file is successfully processed during bulk unpacking"""
        self.processed_images.append(current_file)
        filename = os.path.basename(current_file)
        
        # Add success entry to log
        log_entry = f"✓ {filename} → {len(saved_files)} channels saved"
        self.log_listbox.insert(tk.END, log_entry)
        self.log_listbox.see(tk.END)  # Auto-scroll to bottom
        
        # Update progress
        progress_percent = (progress / total) * 100
        self.progress_var.set(progress_percent)
        self.progress_label.config(text=f"Processed {progress}/{total}: {filename}")
        
        # Force UI update
        self.frame.update_idletasks()
    
    def on_bulk_unpack_error(self, file: str, error: str, progress: int, total: int):
        """Called when an error occurs during bulk unpacking"""
        filename = os.path.basename(file)
        
        # Add error entry to log
        log_entry = f"✗ {filename} → ERROR: {error}"
        self.log_listbox.insert(tk.END, log_entry)
        self.log_listbox.see(tk.END)  # Auto-scroll to bottom
        
        # Update progress
        progress_percent = (progress / total) * 100
        self.progress_var.set(progress_percent)
        self.progress_label.config(text=f"Error processing {progress}/{total}: {filename}")
        
        # Force UI update
        self.frame.update_idletasks()
    
    def on_bulk_unpack_completed(self, results: Dict[str, Union[List[str], str]]):
        """Called when bulk unpacking is completed"""
        success_count = sum(1 for result in results.values() if isinstance(result, list))
        error_count = len(results) - success_count
        
        # Final progress update
        self.progress_var.set(100)
        self.progress_label.config(text=f"Completed: {success_count} successful, {error_count} errors")
        
        # Add completion summary to log
        self.log_listbox.insert(tk.END, "")
        self.log_listbox.insert(tk.END, f"=== COMPLETED ===")
        self.log_listbox.insert(tk.END, f"Total files: {len(results)}")
        self.log_listbox.insert(tk.END, f"Successful: {success_count}")
        self.log_listbox.insert(tk.END, f"Errors: {error_count}")
        self.log_listbox.see(tk.END)
        
        # Show completion message
        if error_count == 0:
            self.show_success(f"Bulk unpacking completed! Processed {success_count} files successfully.")
        else:
            self.update_status(f"Bulk unpacking completed with {error_count} errors. Check log for details.", "orange")

class TextureProcessorApp:
    """Main application class"""
    
    def __init__(self):
        self.root = TkinterDnD.Tk()
        self.root.title("Texture Channel Processor")
        self.root.geometry("800x900")
        
        self.current_panel = None
        self.panels = {}
        
        self._setup_ui()
        self._show_panel("packer")  # Show packer panel by default
    
    def _setup_ui(self):
        """Setup the main UI"""
        # Navigation buttons
        nav_frame = tk.Frame(self.root)
        nav_frame.pack(pady=10)
        
        tk.Button(nav_frame, text="Channel Packer", font=("Arial", 12),
                 command=lambda: self._show_panel("packer")).pack(side="left", padx=10)
        tk.Button(nav_frame, text="Channel Unpacker", font=("Arial", 12),
                 command=lambda: self._show_panel("unpacker")).pack(side="left", padx=10)
        tk.Button(nav_frame, text="Bulk Channel Unpacker", font=("Arial", 12),
                 command=lambda: self._show_panel("bulk_unpacker")).pack(side="left", padx=10)
        # Content area
        self.content_frame = tk.Frame(self.root)
        self.content_frame.pack(fill="both", expand=True)
        
        # Create panels
        self.panels["packer"] = ChannelPackerPanel(self.content_frame)
        self.panels["unpacker"] = ChannelUnpackerPanel(self.content_frame)
        self.panels["bulk_unpacker"] = BulkChannelUnpackerPanel(self.content_frame)
    
    def _show_panel(self, panel_name: str):
        """Show specific panel"""
        # Hide current panel
        if self.current_panel:
            self.panels[self.current_panel].hide()
        
        # Show new panel
        self.current_panel = panel_name
        self.panels[panel_name].show()
    
    def run(self):
        """Run the application"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.root.destroy()


def main():
    """Main entry point"""
    try:
        app = TextureProcessorApp()
        app.run()
    except Exception as e:
        print(f"Application error: {e}")
        messagebox.showerror("Application Error", f"An error occurred: {e}")


if __name__ == "__main__":
    main()