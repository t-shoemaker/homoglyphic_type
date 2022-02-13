#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PIL import Image, ImageFont
import base64
import numpy as np

class Glyph:

    def __init__(self, char):
        """initialize the character class.

        associate the character string, unicode decimal, and unicode hex

        :param char: a unicode character
        :type char: str
        """
        if len(char) != 1:
            raise ValueError("Input single glyphs only!")
        self.char = char
        self.dec = ord(char)
        self.hex = hex(self.dec)

    def _make_bitmap(self, typeface=None, size=10):
        """create a bitmap for the glyph.

        :param typeface: filepath, a typeface to use
        :type typeface: str
        :param size: the size to draw
        :type size: int
        :returns: a bitmap glyph for the character
        :rtype: pil memory instance
        """
        font = ImageFont.truetype(typeface, size)
        return font.getmask(self.char, mode='L')

    def dimensions(self, typeface=None, size=10):
        """return the dimensions of the glyph bitmap.

        :param typeface: filepath, a typeface to use
        :type typeface: str
        :param size: the size to draw
        :type size: int
        :returns: dimensions of the glyph
        :rtype: tup
        """
        bitmap = self._make_bitmap(typeface, size)
        return bitmap.size

    def draw(self, typeface=None, size=10):
        """create an image of the bitmap.

        :param typeface: filepath, a typeface to use
        :type typeface: str
        :param size: the size to draw
        :type size: int
        :returns: a rendered bitmap
        :rtype: pil image
        """
        bitmap = self._make_bitmap(typeface, size)
        return Image.frombytes(bitmap.mode, bitmap.size, bytes(bitmap))

    def bitmap(self, typeface=None, size=10, encode_as='b64'):
        """return the glyph's bitmap.

        :param typeface: filepath, a typeface to use
        :type typeface: str
        :param size: the size to draw
        :type size: int
        :param encode_as: an encoding method for the bitmap
        :type encode_as: str
        :returns: an encoded bitmap
        :rtype: byte str, numpy array, raw encoding, or str
        """
        VALID_OPTS = ['b64', 'bytes', 'numpy', 'raw', 'stringified']
        if encode_as not in VALID_OPTS:
            raise ValueError(f"{encode_as} is not valid. Use {', '.join(VALID_OPTS)}")

        bitmap = self._make_bitmap(typeface, size)
        if encode_as == 'b64':
            bitmap = bytes(bitmap)
            return base64.b64encode(bitmap)
        if encode_as == 'bytes':
            return bytes(bitmap)
        if encode_as == 'numpy':
            img = self.draw(typeface, size)
            return np.asarray(img)
        if encode_as == 'raw':
            return bitmap
        if encode_as == 'stringified':
            img = self.draw(typeface, size)
            arr = np.asarray(img)
            grayscaled = (arr > 0).astype('uint8')
            stringified = map(str, (bit for row in grayscaled for bit in row))
            return ''.join(stringified)

