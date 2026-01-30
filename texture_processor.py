from PIL import Image, ImageTk
import os
from typing import Optional, Dict, List, Tuple, Union
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
from dataclasses import dataclass
from enum import Enum
import threading
from pathlib import Path
import customtkinter as ctk

class ChannelType(Enum):
    """Enum for channel types"""
    RED = "R"
    GREEN = "G"
    BLUE = "B"
    ALPHA = "A"


TEMP_DIR = "temp_channels"



@dataclass
class ImageConfig:
    """Configuration class for image processing"""
    SUPPORTED_FORMATS = [".png", ".dds"]
    DROP_SIZE = (170, 170)
    PREVIEW_SIZE = (300, 300)
    CHANNEL_PREVIEW_SIZE = (180, 180)
    ZOOM_FACTOR = 1.2
    MAX_ZOOM = 10.0
    MIN_ZOOM = 0.1


class ImageProcessor:
    """Handles all image processing operations"""
    
    @staticmethod
    def validate_image_format(file_path: str) -> bool:
        """Validate if file format is supported"""
        return any(file_path.lower().endswith(fmt) for fmt in ImageConfig.SUPPORTED_FORMATS)
    
    @staticmethod
    def validate_image_sizes(image_paths: List[Optional[str]]) -> Optional[Tuple[int, int]]:
        """
        Validate that all images have the same size
        Returns the size if valid, None if no images, raises ValueError if sizes mismatch
        """
        valid_paths = [path for path in image_paths if path is not None]
        
        if not valid_paths:
            return None
        
        images_info = []
        for path in valid_paths:
            try:
                with Image.open(path) as img:
                    images_info.append({
                        "path": path,
                        "name": os.path.basename(path),
                        "size": img.size
                    })
            except Exception as e:
                raise ValueError(f"Cannot open image {path}: {e}")
        
        # Find largest image by pixel count
        reference = max(images_info, key=lambda i: i["size"][0] * i["size"][1])
        expected_size = reference["size"]
        
        # Check all images have same size
        for img_info in images_info:
            if img_info["size"] != expected_size:
                raise ValueError(
                    f"Size mismatch: {img_info['name']} ({img_info['size'][0]}x{img_info['size'][1]}) "
                    f"vs expected {expected_size[0]}x{expected_size[1]} from {reference['name']}"
                )
        
        return expected_size
    
    @staticmethod
    def load_or_create_white_channel(path: Optional[str], size: Tuple[int, int], 
                                   preserve_transparent: bool = False) -> Image.Image:
        """Load image channel or create white channel if path is None"""
        if path is None:
            return Image.new("L", size, 255)
        
        try:
            img = Image.open(path).convert("RGBA")
            
            if img.size != size:
                img = img.resize(size, Image.Resampling.BICUBIC)
            
            if not preserve_transparent:
                # Convert transparent pixels to white
                pixels = img.load()
                for y in range(img.height):
                    for x in range(img.width):
                        r, g, b, a = pixels[x, y]
                        if a == 0:
                            pixels[x, y] = (255, 255, 255, 0)
            
            return img.split()[0]  # Return only first channel as grayscale
            
        except Exception as e:
            raise ValueError(f"Error loading image {path}: {e}")
    
    @staticmethod
    def pack_channels(r_path: Optional[str] = None, g_path: Optional[str] = None, 
                     b_path: Optional[str] = None, a_path: Optional[str] = None,
                     preserve_transparent: bool = True) -> Image.Image:
        """Pack individual channel images into RGBA image"""
        paths = [r_path, g_path, b_path, a_path]
        
        # Validate sizes
        size = ImageProcessor.validate_image_sizes(paths)
        if size is None:
            raise ValueError("No input images provided for channel packing")
        
        # Load channels
        r = ImageProcessor.load_or_create_white_channel(r_path, size, preserve_transparent)
        g = ImageProcessor.load_or_create_white_channel(g_path, size, preserve_transparent)
        b = ImageProcessor.load_or_create_white_channel(b_path, size, preserve_transparent)
        a = ImageProcessor.load_or_create_white_channel(a_path, size, preserve_transparent)
        
        return Image.merge("RGBA", (r, g, b, a))
    
    @staticmethod
    def unpack_channels(image_path: str, apply_gamma_correction: bool = False) -> List[Image.Image]:
        """Unpack RGBA image into individual channel images"""
        try:
            img = Image.open(image_path).convert("RGBA")
            r, g, b, a = img.split()
            
            if apply_gamma_correction:
                channels = [ImageProcessor._apply_gamma_correction(channel) for channel in [r, g, b, a]]
            else:
                channels = [r, g, b, a]
            
            return channels
            
        except Exception as e:
            raise ValueError(f"Error unpacking channels from {image_path}: {e}")
    
    @staticmethod
    def _apply_gamma_correction(img: Image.Image) -> Image.Image:
        """Apply linear to sRGB gamma correction"""
        arr = np.array(img) / 255.0
        arr = np.where(arr <= 0.0031308,
                      arr * 12.92,
                      1.055 * (arr ** (1 / 2.4)) - 0.055)
        return Image.fromarray((arr * 255).astype("uint8"))
    
    @staticmethod
    def create_thumbnail(img: Image.Image, size: Tuple[int, int]) -> Image.Image:
        """Create thumbnail of specified size"""
        thumb = img.copy()
        thumb.thumbnail(size, Image.Resampling.LANCZOS)
        return thumb
    
    @staticmethod
    def save_channels(channels: List[Image.Image], output_dir: str, base_name: str) -> List[str]:
        """Save individual channels to files"""
        os.makedirs(output_dir, exist_ok=True)
        
        saved_files = []
        channel_names = ["R", "G", "B", "A"]
        
        for i, channel in enumerate(channels):
            filename = f"{base_name}_CHANNEL_{channel_names[i]}.png"
            filepath = os.path.join(output_dir, filename)
            channel.save(filepath)
            saved_files.append(filepath)
        
        return saved_files


class ZoomableImageViewer:
    """Reusable zoomable image viewer widget"""
    
    def __init__(self, parent: tk.Widget, title: str = "Image Viewer"):
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("600x600")
        
        self.zoom_factor = 1.0
        self.original_image = None
        self.current_image = None
        self.photo = None
        self.image_item = None
        
        self._setup_ui()
        self._bind_events()
    
    def _setup_ui(self):
        """Setup the UI components"""
        # Canvas frame with scrollbars
        canvas_frame = tk.Frame(self.window)
        canvas_frame.pack(fill="both", expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg="gray")
        h_scrollbar = tk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        v_scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        h_scrollbar.pack(side="bottom", fill="x")
        v_scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
    
    def _bind_events(self):
        """Bind zoom and navigation events"""
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.window.bind("<Key>", self._on_key_press)
        self.window.focus_set()
    
    def display_image(self, image: Image.Image):
        """Display an image in the viewer"""
        self.original_image = image
        self.zoom_factor = 1.0
        self._update_display()
    
    def _update_display(self):
        """Update the display with current zoom"""
        if self.original_image is None:
            return
        
        # Calculate new size
        original_size = self.original_image.size
        new_width = int(original_size[0] * self.zoom_factor)
        new_height = int(original_size[1] * self.zoom_factor)
        
        # Resize image
        self.current_image = self.original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(self.current_image)
        
        # Update canvas
        if self.image_item:
            self.canvas.delete(self.image_item)
        self.image_item = self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
        
        # Update scroll region and title
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.window.title(f"Image Viewer - Zoom: {self.zoom_factor:.2f}x")
    
    def _zoom(self, factor: float):
        """Apply zoom factor"""
        new_zoom = self.zoom_factor * factor
        if ImageConfig.MIN_ZOOM <= new_zoom <= ImageConfig.MAX_ZOOM:
            self.zoom_factor = new_zoom
            self._update_display()
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel zoom"""
        if event.delta > 0:
            self._zoom(ImageConfig.ZOOM_FACTOR)
        else:
            self._zoom(1 / ImageConfig.ZOOM_FACTOR)
    
    def _on_key_press(self, event):
        """Handle keyboard zoom"""
        if event.keysym in ["plus", "equal"]:
            self._zoom(ImageConfig.ZOOM_FACTOR)
        elif event.keysym == "minus":
            self._zoom(1 / ImageConfig.ZOOM_FACTOR)
        elif event.keysym == "0":
            self.zoom_factor = 1.0
            self._update_display()


class FileDropHandler:
    """Handles file drop operations with validation"""
    
    def __init__(self, on_file_dropped_callback):
        self.on_file_dropped = on_file_dropped_callback
    
    def handle_drop(self, event, **kwargs):
        """Handle file drop event with validation"""
        try:
            filepaths_raw = event.data
            if not filepaths_raw:
                return
            
            raw = filepaths_raw.strip("{}")
            path = raw.split()[-1]
            
            if not os.path.isfile(path):
                print(
                    f"Dropped item is not a valid file: {path}\n",
                    f"path: {path}\n",
                    f"filepaths_raw: {filepaths_raw}"
                    
                )
                raise ValueError(f"Not a valid file: {path}")
            
            if not ImageProcessor.validate_image_format(path):
                raise ValueError(f"Unsupported file format. Please use: {', '.join(ImageConfig.SUPPORTED_FORMATS)}")
            
            self.on_file_dropped(path, **kwargs)
            
        except Exception as e:
            messagebox.showerror("File Drop Error", str(e))


class ChannelPackerModel:
    """Model class for channel packing functionality"""
    
    def __init__(self):
        self.channel_paths: Dict[str, Optional[str]] = {ch.value: None for ch in ChannelType}
        self.channel_images: Dict[str, Image.Image] = {}
        # Store original images for restoration
        self.original_channel_paths: Dict[str, Optional[str]] = {ch.value: None for ch in ChannelType}
        self.original_channel_images: Dict[str, Image.Image] = {}
        self.merged_image: Optional[Image.Image] = None
        self.observers = []
    
    def add_observer(self, observer):
        """Add observer for model changes"""
        self.observers.append(observer)
    
    def notify_observers(self, event: str, **kwargs):
        """Notify all observers of changes"""
        for observer in self.observers:
            if hasattr(observer, f'on_{event}'):
                getattr(observer, f'on_{event}')(**kwargs)
    
    def set_channel_image_with_another_channel(self, curr_channel: str, source_channel: str):
        """Set image for a specific channel using another channel's image"""
        # If clicking same channel button, restore original
        if curr_channel == source_channel:
            self.restore_original_channel(curr_channel)
            return
            
        if source_channel not in self.channel_images:
            raise ValueError(f"Source channel {source_channel} has no image set")
        
        # Store original before overwriting (if not already stored)
        if curr_channel not in self.original_channel_images and curr_channel in self.channel_images:
            self.original_channel_paths[curr_channel] = self.channel_paths[curr_channel]
            self.original_channel_images[curr_channel] = self.channel_images[curr_channel]
        
        # Copy from source channel
        image = self.channel_images[source_channel]
        self.channel_paths[curr_channel] = self.channel_paths[source_channel]
        self.channel_images[curr_channel] = image
        self.notify_observers('channel_updated', channel=curr_channel, image=image, path=self.channel_paths[source_channel])
    
    def set_channel_image_to_color(self, channel: str, hex_color: str):
        """Set image for a specific channel to a solid color"""
        # Convert hex color to RGB
        
        default_size = (256, 256)
        
        # Find the largest existing image size
        if self.channel_images:
           
            for img in self.channel_images.values():
                img_size = img.size                
                if img_size[0] * img_size[1] > default_size[0] * default_size[1]:
                    default_size = img_size
            
        
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Create solid color image
        size = default_size
        color_image = Image.new("RGB", size, 255)  # White channel
        
        if channel == ChannelType.RED.value:
            color_image = Image.new("RGB", size, color=(r, g, b))
        elif channel == ChannelType.GREEN.value:
            color_image = Image.new("RGB", size, color=(r, g, b))
        elif channel == ChannelType.BLUE.value:
            color_image = Image.new("RGB", size, color=(r, g, b))
        elif channel == ChannelType.ALPHA.value:
            color_image = Image.new("RGB", size, color=(r, g, b)).convert("L")
            
      
        if (os.path.isdir(TEMP_DIR) == False):
            os.mkdir(TEMP_DIR)
        temp_path = os.path.join(TEMP_DIR, f"solid_color_{hex_color}.png")
        
        color_image.save(temp_path)
        
        # Store original before overwriting (if not already stored)
        if channel not in self.original_channel_images and channel in self.channel_images:
            self.original_channel_paths[channel] = self.channel_paths[channel]
            self.original_channel_images[channel] = self.channel_images[channel]
        
        # Set the new color image
        self.channel_paths[channel] = temp_path
        self.channel_images[channel] = color_image
        self.notify_observers('channel_updated', channel=channel, image=color_image, path=self.channel_paths[channel])
    
    def restore_original_channel(self, channel: str):
        """Restore original image for a channel"""
        if channel in self.original_channel_images:
            # Restore from backup
            original_image = self.original_channel_images[channel]
            original_path = self.original_channel_paths[channel]
            
            self.channel_paths[channel] = original_path
            self.channel_images[channel] = original_image
            
            # Clear the backup since we've restored
            del self.original_channel_images[channel]
            del self.original_channel_paths[channel]
            
            self.notify_observers('channel_updated', channel=channel, image=original_image, path=original_path)
        # If no original stored, do nothing (already at original state)
    
    def load_image(self, image_path: str):
        """Load image and automatically populate all channels from it"""
        try:
            image = Image.open(image_path)
            # Unpack the image into individual channels
            channels = ImageProcessor.unpack_channels(image_path)
            
            # Set each channel with the corresponding unpacked channel
            channel_names = ['R', 'G', 'B', 'A']
            for i, channel_name in enumerate(channel_names):
                if i < len(channels):
                    # Create a temporary path for the channel
                    temp_path = f"{image_path}_{channel_name}"
                    
                    # Store as original if this is the first time setting this channel
                    if channel_name not in self.channel_images:
                        self.original_channel_paths[channel_name] = temp_path
                        self.original_channel_images[channel_name] = channels[i]
                    
                    self.channel_paths[channel_name] = temp_path
                    self.channel_images[channel_name] = channels[i]
                    self.notify_observers('channel_updated', channel=channel_name, image=channels[i], path=temp_path)
                    
            self.notify_observers('image_loaded', image=image, path=image_path)
        except Exception as e:
            raise ValueError(f"Error loading image: {e}")

    def set_channel_image(self, channel: str, image_path: str):
        """Set image for a specific channel"""
        try:
            image = Image.open(image_path)
            
            # Store as original if this is the first time setting this channel
            if channel not in self.channel_images:
                self.original_channel_paths[channel] = image_path
                self.original_channel_images[channel] = image
            
            self.channel_paths[channel] = image_path
            self.channel_images[channel] = image
            self.notify_observers('channel_updated', channel=channel, image=image, path=image_path)
        except Exception as e:
            raise ValueError(f"Error loading image for channel {channel}: {e}")
    
    def clear_channel(self, channel: str):
        """Clear a specific channel"""
        self.channel_paths[channel] = None
        self.channel_images.pop(channel, None)
        
        # Also clear original backups for this channel
        self.original_channel_paths[channel] = None
        self.original_channel_images.pop(channel, None)
        
        self.notify_observers('channel_cleared', channel=channel)
    
    def create_merged_image(self, target_bit_depth: int = 8) -> Image.Image:
        """Create merged image from all channels with specified bit depth"""
        try:
            # First create the merged RGBA image
            print("Creating merged image with channels:", self.channel_paths)
            merged_rgba = ImageProcessor.pack_channels(
                r_path=self.channel_paths[ChannelType.RED.value],
                g_path=self.channel_paths[ChannelType.GREEN.value],
                b_path=self.channel_paths[ChannelType.BLUE.value],
                a_path=self.channel_paths[ChannelType.ALPHA.value]
            )
            
            # Apply bit depth conversion
            self.merged_image = self._convert_to_target_format(merged_rgba, target_bit_depth)
            self.notify_observers('image_merged', image=self.merged_image)
            return self.merged_image
        except Exception as e:
            raise ValueError(f"Error creating merged image: {e}")
    
    def _convert_to_target_format(self, image: Image.Image, target_bit_depth: int) -> Image.Image:
        """Convert image to target format based on bit depth"""
        if target_bit_depth == 8:
            # Keep as RGB (no alpha) for 8-bit
            return image.convert('RGB')
        elif target_bit_depth == 16:
            # Convert to 16-bit grayscale 
            return image.convert('L').convert('I;16')
        elif target_bit_depth == 24:
            # 24-bit RGB (8 bits per channel, 3 channels)
            return image.convert('RGB')
        elif target_bit_depth == 32:
            # Keep RGBA for 32-bit (8 bits per channel, 4 channels)
            return image.convert('RGBA')
        else:
            raise ValueError(f"Unsupported bit depth: {target_bit_depth}")
    
    def save_merged_image(self, output_path: str):
        """Save the merged image"""
        if self.merged_image is None:
            raise ValueError("No merged image to save")
        
        try:
            self.merged_image.save(output_path)
            
            self.notify_observers('image_saved', path=output_path)
        except Exception as e:
            raise ValueError(f"Error saving image: {e}")


class ChannelUnpackerModel:
    """Model class for channel unpacking functionality"""
    
    def __init__(self):
        self.source_image: Optional[Image.Image] = None
        self.source_path: Optional[str] = None
        self.unpacked_channels: List[Image.Image] = []
        self.apply_gamma_correction = False
        self.observers = []
    
    def add_observer(self, observer):
        """Add observer for model changes"""
        self.observers.append(observer)
    
    def notify_observers(self, event: str, **kwargs):
        """Notify all observers of changes"""
        for observer in self.observers:
            if hasattr(observer, f'on_{event}'):
                getattr(observer, f'on_{event}')(**kwargs)
    
    def load_image(self, image_path: str):
        """Load image for unpacking"""
        try:
            self.source_image = Image.open(image_path)
            self.source_path = image_path
            self.notify_observers('image_loaded', image=self.source_image, path=image_path)
        except Exception as e:
            raise ValueError(f"Error loading image: {e}")
    
    def bulk_unpack_channels(self, image_paths: List[str], output_dir: str, progress_callback=None) -> Dict[str, List[str]]:
        """
        Bulk unpack multiple images into channels
        
        Args:
            image_paths: List of image file paths to process
            output_dir: Directory to save unpacked channels
            progress_callback: Optional callback function for progress updates (current_index, total_count, current_file)
        
        Returns:
            Dictionary mapping source file paths to their saved channel file paths
        """
        if not image_paths:
            raise ValueError("No image paths provided for bulk unpacking")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        results = {}
        total_count = len(image_paths)
        
        for i, image_path in enumerate(image_paths):
            try:
                # Update progress if callback provided
                if progress_callback:
                    progress_callback(i, total_count, image_path)
                
                # Validate image format
                if not ImageProcessor.validate_image_format(image_path):
                    raise ValueError(f"Unsupported image format: {image_path}")
                
                # Unpack channels
                channels = ImageProcessor.unpack_channels(image_path, self.apply_gamma_correction)
                
                # Generate base filename
                base_name = Path(image_path).stem
                
                # Create a new folder for each image to put the channels
                image_output_dir = os.path.join(output_dir, base_name)
                os.makedirs(image_output_dir, exist_ok=True)
                
                # Save channels
                saved_files = ImageProcessor.save_channels(channels, image_output_dir, base_name)
                results[image_path] = saved_files
                
                self.notify_observers('bulk_channels_unpacked',
                                    current_file=image_path, 
                                    saved_files=saved_files,
                                    progress=i + 1,
                                    total=total_count)
                
            except Exception as e:
                error_msg = f"Error processing {image_path}: {e}"
                results[image_path] = error_msg
                self.notify_observers('bulk_unpack_error', 
                                    file=image_path, 
                                    error=error_msg,
                                    progress=i + 1,
                                    total=total_count)
        
        # Notify completion
        self.notify_observers('bulk_unpack_completed', results=results)
        return results
    
    def unpack_channels(self):
        """Unpack the loaded image into channels"""
        if self.source_path is None:
            raise ValueError("No image loaded to unpack")
        
        try:
            self.unpacked_channels = ImageProcessor.unpack_channels(
                self.source_path, self.apply_gamma_correction
            )
            self.notify_observers('channels_unpacked', channels=self.unpacked_channels)
            return self.unpacked_channels
        except Exception as e:
            raise ValueError(f"Error unpacking channels: {e}")
    
    def save_channels(self, output_dir: str) -> List[str]:
        """Save unpacked channels to files"""
        if not self.unpacked_channels:
            raise ValueError("No channels to save")
        
        if self.source_path is None:
            base_name = "unpacked"
        else:
            base_name = Path(self.source_path).stem
        
        try:
            saved_files = ImageProcessor.save_channels(
                self.unpacked_channels, output_dir, base_name
            )
            self.notify_observers('channels_saved', files=saved_files)
            return saved_files
        except Exception as e:
            raise ValueError(f"Error saving channels: {e}")


# [Continue with UI classes in next part...]