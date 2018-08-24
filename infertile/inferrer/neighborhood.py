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

__all__ = ['Neighborhood']


class Neighborhood:

    @classmethod
    def from_iterable(cls, iterable):
        """
        Parse an iterable into a Neighborhood object.

        :type iterable: Iterable
        :param iterable: Iterable of booleans, indicating whether there's a neighboring tile, in left-to-right,
                         top-to-bottom order.
        :return: Normalized Neighborhood object
        :rtype: Neighborhood
        """
        neighborhood = cls()
        neighbors_list = list(iterable)
        for y in "umd":
            for x in "lmr":
                if x + y != 'mm':  # The center tile is not a neighbor, it's the tile we're generating!
                    # Fill the list
                    neighborhood[y + x] = neighbors_list.pop(0)
        neighborhood.normalize()
        return neighborhood

    @classmethod
    def from_int(cls, neighborhood_int):
        """
        Parse an 8-bit integer into a neighborhood object.

        :type neighborhood_int: int
        :param neighborhood_int: Integer, where each binary digit indicates whether there's a neighboring tile there, in
                                 left-to-right, top-to-bottom order.
        :return: Normalized Neighborhood object
        :rtype: Neighborhood
        """
        return cls.from_string("{0:b}".format(neighborhood_int))

    @classmethod
    def from_string(cls, neighborhood_str):
        """
        Parse a string of 8 binary digits into a neighborhood object.

        :type neighborhood_str: str
        :param neighborhood_str: String of 8 binary digits, where each character indicates whether there's a neighboring
                                 tile there, in left-to-right, top-to-bottom order.
        :return: Normalized Neighborhood object
        :rtype: Neighborhood
        """
        return cls.from_iterable([bool(int(ch)) for ch in neighborhood_str])

    def __init__(self):
        # Enable in PyCharm > Preferences > Editor > Code Style > Formatter Control
        # @formatter:off
        self.ul, self.um, self.ur = False, False, False
        self.ml,          self.mr = False,        False
        self.dl, self.dm, self.dr = False, False, False
        # @formatter:on

    def normalize(self):
        """
        Normalize neighborhood, discarding unimportant neighbors.
        Notice that the following tile, marked with an X (a ``#`` denotes a neighbor)::
            #..
            .X#
            .##

        Should be the same as this tile:

            ...
            .X#
            .##

        So, we discard the corner neighbors if neither of the non-diagonally adjacent tiles is a neighbor.
        """
        for y in "ud":
            for x in "lr":
                if self[y + x] and not (self[y + 'm'] and self['m' + x]):
                    self[y + x] = False

    def __getitem__(self, item):
        """
        Allow dict-like access to attributes.
        """
        return getattr(self, item)

    def __setitem__(self, key, value):
        """
        Allow dict-like key setting.

        Guard against typos, and ensure no sneaky stuff like::

            setattr(neighborhood, "__getitem__", lambda *args, **kwargs: os.remove("/"))

        happens - that is, check if the key being set is a proper neighboring direction; if it is, set the value.
        """
        assert len(key) == 2 and key[0] in 'umd' and key[1] in "lmr"
        return setattr(self, key, value)

    def to_list(self):
        """
        Convert to a list of booleans

        :return: List of booleans, indicating whether there's a neighboring tile, in left-to-right,
                 top-to-bottom order.
        :rtype: list[bool]
        """
        neighbors_list = []
        for y in "umd":
            for x in "lmr":
                if x + y != 'mm':  # The center tile is not a neighbor, it's the tile we're generating!
                    # Fill the list
                    neighbors_list.append(self[y + x])
        return neighbors_list

    def to_string(self):
        """
        Convert to an 8-character string of binary digits.

        :return: 8-character string of binary digits, indicating whether there's a neighboring tile, in left-to-right,
                 top-to-bottom order.
        :rtype: str
        """
        return "".join('1' if n else '0' for n in self.to_list())

    def to_int(self):
        """
        Convert to an integer, with its binary digits indicating whether there's a neighboring tile, in left-to-right,
        top-to-bottom order.

        :return: :py:meth:`.to_string` converted to an int.
        :rtype: int
        """
        return int(self.to_string(), 2)

    def __hash__(self):
        """
        Allow use as key in dictionary.

        (convert to 8-character string of binary digits)
        :return: hash of the binary string representing this Neighborhood.
        :rtype: int
        """
        return hash(self.to_int())

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __repr__(self):
        return "Neighborhood: " + self.to_string()
