#!/usr/bin/env python3
# coding=utf-8
# vim: ai ts=4 sts=4 et sw=4 ft=python
#
# # Released under MIT License
#
# Copyright (c) 2017 Slavfox.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import itertools
from collections import namedtuple

from PIL import Image

from infertile.inferrer.neighborhood import Neighborhood

__all__ = ['Box', 'TilesetGenerator']


Box = namedtuple('Box', ('x1', 'y1', 'x2', 'y2'))


class TilesetGenerator:
    def __init__(self):
        self.source_img = None
        self.w = 0
        self.h = 0
        self.box = Box(0, 0, self.w, self.h)
        self.generated_tiles = {}
        self.parts = {}

    def load_image(self, source_path):
        """
        Given a path, load the image there as the source and reset all stored image-specific data.
        Image should be two sprites of the exact same dimensions, one convex (no neighbors) and one concave (all
        non-diagonal neighbors), like this::

            ┌┐┘└
            └┘┐┌

        :param source_path: Path to the image.
        """
        self.source_img = Image.open(source_path)
        self.w = self.source_img.size[0]
        self.h = self.source_img.size[1]
        if self.w % 2 != 0:
            raise ValueError("Image should be split into two equal parts - width is not even.")
        self.generated_tiles = {}
        self.parts = {}

    def generate_parts(self):
        """
        Split the image into the 18 parts we're using to generate the complete tileset and save them to self.parts.
        Parts are designated as ``curve + umd + rml``, where ``curve`` is either convex::

            ┌┐
            └┘

        or concave::

            ┘└
            ┐┌

        ``umd`` is one of "u", "m", or "d"; designating which horizontal third (upper, middle, or lower) of the sprite
         the part belongs to, and ``lmr`` is, likewise, one of "r", "m" or "l", designating the horizontal third (left,
         middle, or right).
        """
        for half, curve in enumerate(("convex", "concave")):
            for umd, y_start, y_end in (("u", 0, self.box.y1),
                                        ("m", self.box.y1, self.box.y2),
                                        ("d", self.box.y2, self.h)):
                for lmr, x_start, x_end in (("l", 0, self.box.x1),
                                            ("m", self.box.x1, self.box.x2),
                                            ("r", self.box.x2, int(self.w / 2))):
                    box = Box(int(half * self.w / 2) + x_start,
                              y_start,
                              int(half * self.w / 2) + x_end,
                              y_end)
                    self.parts[curve + umd + lmr] = self.source_img.crop(box)

    def get_tiling_sprite_list(self):
        """
        Generate all possible combinations of neighboring tiles - a neighboring tile is either empty or filled.
        Populates self.generated_tiles.

        :return: List of all the tiles in the generated tileset.
        :rtype: list[Image]
        """
        self.generate_parts()
        # Equivalent to generating all 8-bit numbers represented as lists of booleans.
        combinations = itertools.product([True, False], repeat=8)
        # Set, so there's no duplicates
        neighborhoods = {Neighborhood.from_iterable(nb_list) for nb_list in combinations}
        tile_list = []
        for neighborhood in sorted(neighborhoods, key=lambda nb: nb.to_string().count('1')):
            tile_list.append(self.get_tile(neighborhood))
        return tile_list

    def get_tile(self, neighborhood):
        """
        Get a sprite for a given neighborhood, generating it if it doesn't exist. Populates self.generated_tiles.

        :param neighborhood: Neighborhood object to get a sprite for
        :type neighborhood: Neighborhood
        :return: Generated/fetched sprite for the neighborhood.
        :rtype: Image
        """
        if neighborhood not in self.generated_tiles:
            self.generated_tiles[neighborhood.to_string()] = self.infer_tile(neighborhood)
        return self.generated_tiles[neighborhood.to_string()]

    def infer_tile(self, neighborhood):
        """
        Generate a sprite for a given neighborhood.

        :param neighborhood: Neighborhood object to get a sprite for
        :type neighborhood: Neighborhood
        :return: Generated/fetched sprite for the neighborhood.
        :rtype: Image
        """
        # Fill the center with, well, the center.
        tile_parts = self.get_tile_parts(neighborhood)
        return self.merge_tile_parts(tile_parts)

    def get_tile_parts(self, neighborhood):
        """
        Get the 9 sections (images) needed to generate the tile for a given neighborhood.

        :param neighborhood: Neighborhood object to get the parts for the tile for
        :type neighborhood: Neighborhood
        :return: Dictionary mapping position keys to the images representing them. Keys are two-character, with the
                 first, as usual, being one of 'u', 'm', 'd' and indicating the vertical position, and the second being
                 one of 'r', 'm', 'l' and indicating the horizontal position
        :rtype: dict[str: Image]
        """
        # Fill the center with, well, the center.
        sprite_parts = {'mm': self.parts['convexmm']}
        for umd in "ud":
            # We can just reuse the top and bottom middle parts
            sprite_parts[umd + 'm'] = self.parts['{curve}{y}m'.format(
                curve='concave' if neighborhood[umd + 'm'] else 'convex',
                y=umd
            )]
            for lmr in "lr":
                # center cross
                sprite_parts['m' + lmr] = self.parts['{curve}m{x}'.format(
                    curve='concave' if neighborhood['m' + lmr] else 'convex',
                    x=lmr
                )]
                sprite_parts[umd + lmr] = self.get_corner(umd, lmr, neighborhood)
        return sprite_parts

    def get_corner(self, umd, lmr, neighborhood):
        """
        Get the proper image for a corner of a sprite.

        :type umd: str
        :param umd: one of "u", "m", or "d"; designating which horizontal third of the sprite (upper, middle, or lower)
                    the corner belongs to.
        :param lmr: one of "r", "m" or "l", designating the horizontal third of the sprite (left, middle, or right) the
                    corner belongs to.
        :type neighborhood: Neighborhood
        :param neighborhood: the neighborhood of the tile being generated
        :return: Corner of the generated tile
        :rtype: Image
        """
        corner_size = self.parts['concave' + umd + lmr].size
        # No diagonal neighbor at the corner
        if not neighborhood[umd + lmr]:
            # Sanity check; the Neighborhood should be normalized, but it doesn't hurt to make sure
            # No diagonal neighbor, both non-diagonal neighbors: concave corner.
            if neighborhood[umd + 'm'] and neighborhood['m' + lmr]:
                return self.parts['concave' + umd + lmr]
        # All neighbors - fill it out with the middle.
        if neighborhood[umd + 'm'] and neighborhood['m' + lmr]:
            # ToDo: tile the middle instead of resizing it
            return self.parts['concavemm'].resize(corner_size)
        # Only the vertical neighbor present - vertical edge.
        elif neighborhood[umd + 'm']:
            return self.parts['convexm' + lmr].resize(corner_size)
        # Only the horizontal neighbor present - horizontal edge.
        elif neighborhood['m' + lmr]:
            return self.parts['convex' + umd + 'm'].resize(corner_size)
        # No neighbors - just grab the convex corner.
        else:
            return self.parts['convex' + umd + lmr]

    def merge_tile_parts(self, tile_parts):
        """
        Merge tile parts into a single image.

        :type tile_parts: dict[str: Image]
        :param tile_parts: Dictionary mapping position keys to the images representing them.
        :return: Complete tile image
        :rtype: Image
        """
        tile = Image.new(self.source_img.mode, (int(self.w / 2), self.h))
        yoffset = 0
        for umd in "umd":
            xoffset = 0
            for lmr in "lmr":
                w, h = tile_parts[umd+lmr].size
                tile.paste(tile_parts[umd+lmr], (xoffset, yoffset, xoffset+w, yoffset+h))
                xoffset += tile_parts[umd+lmr].size[0]
            yoffset += tile_parts[umd+'m'].size[1]
        return tile

    def get_tilelist_merged_into_single_image(self, tilelist):
        result = Image.new(self.source_img.mode, (self.w * 3, self.h * 8))
        tilewidth = int(self.w / 2)
        i = 0
        for y in range(8):
            for x in range(6):
                try:
                    startx, starty = tilewidth * x, self.h * y
                    endx, endy = startx + tilewidth, starty + self.h
                    result.paste(tilelist[i], (startx, starty, endx, endy))
                    i += 1
                except IndexError:
                    return result
        return result
