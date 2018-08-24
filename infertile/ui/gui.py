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

import wx

from infertile.inferrer.generator import TilesetGenerator, Box

ABOUT_DIALOG = """InferTile {version}

InferTile is a simple utility for generating (inferring ;)) an entire, 47-part, perfectly tiling tileset from just two \
sprites.
""".format(
    version="0.0"
)


class InfertileFrame(wx.Frame):
    def __init__(self, parent, id_=wx.ID_ANY):
        super(InfertileFrame, self).__init__(parent, id=id_, title="InferTile", style=wx.DEFAULT_FRAME_STYLE)

        self.generator = TilesetGenerator()
        self.inferred_img = None

        self.menu_bar = None
        self.make_menu_bar()
        self.CreateStatusBar()

        self.filename = ''
        self.dirname = ''

        self.toplevel_sizer = None

        self.preview_sizer = None
        self.preview_image = None
        self.preview_label = None

        self.editor_sizer = None
        self.editor_image = None
        self.img = None
        self.imgscaled = None
        self.imgwidth = 0
        self.editor_image_path_label = None
        self.editor_tooltip = None
        self.dragging = False
        self.drag_start = (0, 0)

        self.buttons_sizer = None
        self.open_file_button = None
        self.save_button = None
        self.make_tileset_button = None
        self.zoomin_button = None
        self.zoomout_button = None
        self.scale = 1
        self.populate_window()

        self.Show(True)

    def make_editor(self):
        self.img = wx.Image(128, 64)
        self.imgscaled = self.img
        self.imgwidth = int(self.img.GetWidth()/2)
        wx.InitAllImageHandlers()
        self.editor_image = wx.StaticBitmap(self, wx.ID_ANY, wx.Bitmap(self.img))
        self.editor_image_path_label = wx.StaticText(self, label="Open an image!", style=wx.ALIGN_CENTER)
        self.editor_tooltip = wx.StaticText(self, label="Click once to start marking the center area, "
                                                        "click one more time to finish.", style=wx.ALIGN_CENTER)

    def make_preview(self):
        img = wx.Image(384, 512)
        self.preview_label = wx.StaticText(self, label="Preview", style=wx.ALIGN_CENTER)
        self.preview_image = wx.StaticBitmap(self, wx.ID_ANY, wx.Bitmap(img))
        self.save_button = wx.Button(self, wx.ID_ANY, 'Export')
        self.save_button.Disable()
        self.save_button.Bind(wx.EVT_BUTTON, self.on_save)

    def make_buttons(self):
        self.open_file_button = wx.Button(self, wx.ID_ANY, 'Browse')
        self.open_file_button.Bind(wx.EVT_BUTTON, self.on_open)
        self.make_tileset_button = wx.Button(self, wx.ID_ANY, 'Infer tiles')
        self.make_tileset_button.Bind(wx.EVT_BUTTON, self.on_infer)
        self.make_tileset_button.Disable()
        self.zoomin_button = wx.Button(self, wx.ID_ANY, 'Zoom x2')
        self.zoomin_button.Bind(wx.EVT_BUTTON, self.on_zoomin)
        self.zoomin_button.Disable()
        self.zoomout_button = wx.Button(self, wx.ID_ANY, 'Zoom x0.5')
        self.zoomout_button.Disable()
        self.zoomout_button.Bind(wx.EVT_BUTTON, self.on_zoomout)

    def on_zoomin(self, _):
        w, h = self.editor_image.Size
        self.imgscaled = self.img.Scale(w*2, h*2)
        self.scale *= 2
        self.editor_image.SetBitmap(wx.Bitmap(self.imgscaled))
        self.redraw()

    def on_zoomout(self, _):
        w, h = self.editor_image.Size
        self.imgscaled = self.img.Scale(w/2, h/2)
        self.scale /= 2
        self.editor_image.SetBitmap(wx.Bitmap(self.imgscaled))
        self.redraw()

    def populate_window(self):
        self.toplevel_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.preview_sizer = wx.BoxSizer(wx.VERTICAL)
        self.make_preview()
        self.preview_sizer.Add(self.preview_label, 1, wx.EXPAND | wx.ALL, 5)
        self.preview_sizer.Add(self.preview_image, 10, wx.EXPAND | wx.ALL, 5)
        self.preview_sizer.Add(self.save_button, 1, wx.EXPAND | wx.ALL, 5)

        self.buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.make_buttons()
        self.buttons_sizer.Add(self.open_file_button, 0, wx.EXPAND | wx.ALL, 5)
        self.buttons_sizer.Add(self.make_tileset_button, 0, wx.EXPAND | wx.ALL, 5)

        self.editor_sizer = wx.BoxSizer(wx.VERTICAL)
        self.make_editor()
        self.editor_sizer.Add(self.editor_image_path_label, 0, wx.EXPAND | wx.TOP, 64)
        self.editor_sizer.Add(self.editor_tooltip, 0, wx.EXPAND | wx.TOP, 5)
        self.editor_sizer.Add(self.editor_image, 1, wx.ALL | wx.ALIGN_CENTER, 5)
        self.editor_sizer.Add(self.zoomin_button, 0, wx.EXPAND | wx.ALL, 5)
        self.editor_sizer.Add(self.zoomout_button, 0, wx.EXPAND | wx.ALL, 5)

        self.Bind(wx.EVT_PAINT, self.OnPaint)

        # self.preview_dc = wx.MemoryDC()

        self.editor_sizer.Add(self.buttons_sizer, 0, wx.EXPAND | wx.ALL, 5)
        self.toplevel_sizer.Add(self.editor_sizer, 1, wx.EXPAND | wx.ALL, 5)
        self.toplevel_sizer.Add(self.preview_sizer, 0, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(self.toplevel_sizer)
        self.toplevel_sizer.Fit(self)

    def make_menu_bar(self):
        file_menu = self.make_file_menu()
        self.menu_bar = wx.MenuBar()
        self.menu_bar.Append(file_menu, "&File")
        self.SetMenuBar(self.menu_bar)

    def make_file_menu(self):
        file_menu = wx.Menu()
        open_ = file_menu.Append(wx.ID_OPEN, "&Open", "Open an image")
        file_menu.AppendSeparator()
        about = file_menu.Append(wx.ID_ABOUT, "&About", " Information about this program")
        exit_ = file_menu.Append(wx.ID_EXIT, "E&xit", " Terminate the program")
        self.Bind(wx.EVT_MENU, self.on_open, open_)
        self.Bind(wx.EVT_MENU, self.on_about, about)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_)
        return file_menu

    def on_about(self, _):
        dlg = wx.MessageDialog(self, ABOUT_DIALOG, "About InferTile", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def on_exit(self, _):
        self.Close(True)  # Close the frame

    def on_infer(self, _):
        self.generator.load_image(self.filename)
        tilelist = self.generator.get_tiling_sprite_list()
        self.inferred_img = self.generator.get_tilelist_merged_into_single_image(tilelist)
        wximg = pil_image_to_wximg(self.inferred_img).Scale(384, 512, wx.IMAGE_QUALITY_HIGH)
        self.preview_image.SetBitmap(wx.Bitmap(wximg))
        self.save_button.Enable()
        self.redraw()

    def redraw(self):
        self.preview_sizer.Fit(self)
        self.preview_sizer.Layout()
        self.editor_sizer.Fit(self)
        self.editor_sizer.Layout()
        self.toplevel_sizer.Fit(self)
        self.toplevel_sizer.Layout()

    def on_open(self, _):
        self.dirname = ''
        with wx.FileDialog(self,
                           "Choose an image",
                           wildcard="PNG files (*.png)|*.png",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fd:
            if fd.ShowModal() == wx.ID_OK:
                self.filename = fd.GetPath()
                self.load_image()
                self.editor_image_path_label.SetLabel(self.filename)
                self.redraw()
                self.zoomin_button.Enable()
                self.zoomout_button.Enable()
                self.editor_image.Enable()
                self.make_tileset_button.Enable()
                self.editor_image.Bind(wx.EVT_LEFT_DOWN, self.on_down)
                self.editor_image.Bind(wx.EVT_MOTION, self.on_mouse_drag)

    def load_image(self):
        self.img = wx.Image(self.filename)
        self.imgscaled = self.img
        self.scale = 1
        self.imgwidth = int(self.img.GetWidth()/2)
        self.editor_image.SetBitmap(wx.Bitmap(self.img))

    # noinspection PyPep8Naming
    def OnPaint(self, _):
        if self.imgscaled:
            bitmap = wx.Bitmap(self.imgscaled)
            # self.editor_image.SetBitmap(wx.NullBitmap)
            dc = wx.MemoryDC()
            dc.SelectObject(bitmap)
            dc.SetPen(wx.Pen(wx.RED, 2))

            # First half
            x1, y1, x2, y2 = self.generator.box
            draw_rectangle(dc, Box(x1 * self.scale,
                                   y1 * self.scale,
                                   x2 * self.scale,
                                   y2 * self.scale))
            # Second half
            x1, y1, x2, y2 = self.generator.box
            draw_rectangle(dc, Box(x1*self.scale + self.imgwidth*self.scale,
                                   y1*self.scale,
                                   x2*self.scale + self.imgwidth*self.scale,
                                   y2*self.scale))

            dc.SelectObject(wx.NullBitmap)
            self.editor_image.SetBackgroundStyle(wx.BG_STYLE_PAINT)
            self.editor_image.SetBitmap(bitmap)

    def on_save(self, _):
        if self.inferred_img:
            with wx.FileDialog(self,
                               "Choose a destination",
                               style=wx.FD_SAVE,
                               defaultFile="inferred.png") as fd:
                if fd.ShowModal() == wx.ID_OK:
                    self.inferred_img.save(fd.GetPath())

    def on_down(self, event):
        if self.dragging:
            self.dragging = False
        else:
            self.dragging = True
            self.drag_start = event.GetPosition()

    def on_mouse_drag(self, event):
        if self.dragging:
            x1, y1 = self.drag_start
            x2, y2 = event.GetPosition()
            x1 = int(x1/self.scale)
            x2 = int(x2/self.scale)
            y1 = int(y1/self.scale)
            y2 = int(y2/self.scale)
            if x1 > self.imgwidth:
                x1 -= self.imgwidth
            if x2 > self.imgwidth:
                x2 -= self.imgwidth
            self.generator.box = Box(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
            self.editor_tooltip.SetLabel("Selected box: {},{}, {},{}".format(
                self.generator.box.x1,
                self.generator.box.y1,
                self.generator.box.x2,
                self.generator.box.y2,
            ))
            self.OnPaint(event)


def pil_image_to_wximg(image):
    wximg = wx.Image(*image.size)
    hasalpha = image.mode[-1] == 'A'
    if hasalpha:
        rgbstr = image.convert('RGB').tobytes()
        wximg.SetData(rgbstr)
        imgstr = image.convert('RGBA').tobytes()
        alphastr = imgstr[3::4]
        wximg.SetAlpha(alphastr)
    return wximg


def draw_rectangle(dc, box):
    dc.DrawLine(box.x1, box.y1, box.x2, box.y1)
    dc.DrawLine(box.x1, box.y1, box.x1, box.y2)
    dc.DrawLine(box.x1, box.y2, box.x2, box.y2)
    dc.DrawLine(box.x2, box.y1, box.x2, box.y2)


class UI:
    def __init__(self):
        self.app = wx.App()
        self.frm = InfertileFrame(None)

    def run(self):
        """Run the main loop"""
        self.app.MainLoop()


if __name__ == '__main__':
    ui = UI()
    ui.run()
