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
import sys
import io

from infertile.ui.gui import UI
from infertile.inferrer.generator import TilesetGenerator, Box

DESC_STR = """
usage: infertile [-h] [--nogui x1 y1 x2 y2] [--input path] [--output path]

Arguments:
    -h --help                 show this message
    -n --nogui x1 y1 x2 y2    run on an input file with the given center box, with no gui
    -i --input path           specify input file
    -o --output path          specify output file
"""


def main(args=None):
    nogui = False
    box_coords = []
    infile = None
    outfile = None
    if args is None:
        args = sys.argv[1:]
    argn = 0
    if '-h' in args or '--help' in args:
        print(DESC_STR)
        return
    while argn < len(args):
        if args[argn] == '--nogui' or args[argn] == '-n':
            nogui = True
            argn += 1
            continue
        if nogui and len(box_coords) < 4:
            try:
                box_coords.append(int(args[argn]))
                argn += 1
                continue
            except ValueError:
                print("If --nogui is specified, the following four arguments must be integer pixel offsets.")
                return
        if args[argn] == '-i' or args[argn] == '--input':
            if argn < len(args):
                infile = args[argn+1]
                argn += 2
                continue
            else:
                print("--input must be followed by the path to the input file!")
                return
        if args[argn] == '-o' or args[argn] == '--output':
            if argn < len(args):
                outfile = args[argn+1]
                argn += 2
                continue
            else:
                print("--output must be followed by the path to the input file!")
                return
        print(DESC_STR)
        return
    if nogui:
        cli(infile, outfile, box_coords)
    else:
        gui()


def cli(infile, outfile, box):
    generator = TilesetGenerator()
    generator.load_image(infile)
    generator.box = Box(*box)
    tilelist = generator.get_tiling_sprite_list()
    inferred_img = generator.get_tilelist_merged_into_single_image(tilelist)
    if outfile:
        inferred_img.save(outfile)
    else:
        bytearr = io.BytesIO()
        inferred_img.save(bytearr, format="PNG")
        sys.stdout.buffer.write(bytearr.getvalue())


def gui():
    UI().run()


if __name__ == '__main__':
    main()
