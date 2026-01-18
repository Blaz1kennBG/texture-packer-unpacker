#!/usr/bin/env python3
"""
Test script for the refactored texture processor
"""

import unittest
import tempfile
import os
from PIL import Image
from texture_processor import ImageProcessor, ChannelType, ChannelPackerModel, ChannelUnpackerModel


class TestImageProcessor(unittest.TestCase):
    """Test cases for ImageProcessor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test images
        self.test_image_path = os.path.join(self.temp_dir, "test.png")
        test_img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
        test_img.save(self.test_image_path)
        
        self.test_image_path2 = os.path.join(self.temp_dir, "test2.png")
        test_img2 = Image.new("RGBA", (100, 100), (0, 255, 0, 255))
        test_img2.save(self.test_image_path2)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_validate_image_format(self):
        """Test image format validation"""
        self.assertTrue(ImageProcessor.validate_image_format("test.png"))
        self.assertTrue(ImageProcessor.validate_image_format("test.dds"))
        self.assertFalse(ImageProcessor.validate_image_format("test.jpg"))
    
    def test_validate_image_sizes(self):
        """Test image size validation"""
        # Test with valid same-size images
        size = ImageProcessor.validate_image_sizes([self.test_image_path, self.test_image_path2])
        self.assertEqual(size, (100, 100))
        
        # Test with no images
        self.assertIsNone(ImageProcessor.validate_image_sizes([None, None]))
        
        # Test with mismatched sizes
        small_path = os.path.join(self.temp_dir, "small.png")
        Image.new("RGBA", (50, 50), (0, 0, 255, 255)).save(small_path)
        
        with self.assertRaises(ValueError):
            ImageProcessor.validate_image_sizes([self.test_image_path, small_path])
    
    def test_pack_channels(self):
        """Test channel packing"""
        packed = ImageProcessor.pack_channels(
            r_path=self.test_image_path,
            g_path=self.test_image_path2
        )
        
        self.assertEqual(packed.mode, "RGBA")
        self.assertEqual(packed.size, (100, 100))
    
    def test_unpack_channels(self):
        """Test channel unpacking"""
        # Create a packed image first
        packed = ImageProcessor.pack_channels(
            r_path=self.test_image_path,
            g_path=self.test_image_path2
        )
        packed_path = os.path.join(self.temp_dir, "packed.png")
        packed.save(packed_path)
        
        # Unpack it
        channels = ImageProcessor.unpack_channels(packed_path)
        
        self.assertEqual(len(channels), 4)
        for channel in channels:
            self.assertEqual(channel.mode, "L")  # Grayscale
            self.assertEqual(channel.size, (100, 100))


class TestChannelPackerModel(unittest.TestCase):
    """Test cases for ChannelPackerModel"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.model = ChannelPackerModel()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test image
        self.test_image_path = os.path.join(self.temp_dir, "test.png")
        test_img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
        test_img.save(self.test_image_path)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_set_channel_image(self):
        """Test setting channel image"""
        self.model.set_channel_image(ChannelType.RED.value, self.test_image_path)
        
        self.assertEqual(self.model.channel_paths[ChannelType.RED.value], self.test_image_path)
        self.assertIn(ChannelType.RED.value, self.model.channel_images)
    
    def test_clear_channel(self):
        """Test clearing channel"""
        self.model.set_channel_image(ChannelType.RED.value, self.test_image_path)
        self.model.clear_channel(ChannelType.RED.value)
        
        self.assertIsNone(self.model.channel_paths[ChannelType.RED.value])
        self.assertNotIn(ChannelType.RED.value, self.model.channel_images)


def run_tests():
    """Run all tests"""
    unittest.main()


if __name__ == "__main__":
    run_tests()