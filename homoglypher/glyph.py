#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PIL import Image, ImageFont
import base64
import numpy as np

class Glyph:

    def __init__(self, char):
        """
        initialize with the string, decimal, and hex representations
        of the character
        """
        if len(char) != 1:
            raise ValueError("Input single glyphs only!")
        self.char = char
        self.dec = ord(char)
        self.hex = hex(self.dec)

    def _make_bitmap(self, typeface=None, size=10):
        """
        create a bitmap for the glyph
        """
        font = ImageFont.truetype(typeface, size)
        return font.getmask(self.char, mode='L')

    def dimensions(self, typeface=None, size=10):
        """
        return the dimensions of the bitmap
        """
        bitmap = self._make_bitmap(typeface, size)
        return bitmap.size

    def draw(self, typeface=None, size=10):
        """
        create an image of the bitmap
        """
        bitmap = self._make_bitmap(typeface, size)
        return Image.frombytes(bitmap.mode, bitmap.size, bytes(bitmap))

    def bitmap(self, typeface=None, size=10, encode_as='b64'):
        """
        return the glyph's bitmap
        """
        bitmap = self._make_bitmap(typeface, size)
        if encode_as == 'b64':
            bitmap = bytes(bitmap)
            return base64.b64encode(bitmap)
        elif encode_as == 'bytes':
            return bytes(bitmap)
        elif encode_as == 'numpy':
            img = self.draw(typeface, size)
            return np.asarray(img)
        elif encode_as == 'raw':
            return bitmap
        elif encode_as == 'stringified':
            img = self.draw(typeface, size)
            arr = np.asarray(img)
            grayscaled = (arr > 0).astype('uint8')
            stringified = map(str, (bit for row in grayscaled for bit in row))
            return ''.join(stringified)
        else:
            valid_opts = "b64, bytes, numpy, raw, or stringified"
            raise ValueError(f"{encode_as} is not valid. Use {valid_opts}")

