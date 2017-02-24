# https://github.com/sidorares/node-x11/blob/master/examples/smoketest/transpwindow.js
# https://github.com/tmarble/yxcba/blob/master/yxcba

from __future__ import print_function
import sys
import time
import xcffib
import xcffib.xproto
from xcffib.xproto import CW, EventMask
import os

conn = xcffib.connect(display=os.getenv('DISPLAY', ':0'))
setup = conn.get_setup()
screen = conn.get_setup().roots[conn.pref_screen]
root = screen.root


def get_visual(screen, desired_depth=32):
    for depth in tuple(screen.allowed_depths):
        for v in depth.visuals:
            if depth.depth == desired_depth:
                return v.visual_id
    return None

class ExternalWindow(object):
    def __init__(self, conn):
        self.conn = conn
        self.x, self.y = 100, 100
        self.width, self.height = 400, 200
        self.border_width = 20
        self.depth = 32         # 32 or 24
        # if depth is 32 then we have argb
        # if 24 just rgb
        self.visual = get_visual(screen, desired_depth=self.depth)

        # CW.BackPixel - should use?
        self.value_mask =  (
            CW.BackPixel |
            CW.BorderPixel |
            # CW.OverrideRedirect |
            CW.EventMask |
            CW.Colormap
        )
        self.event_mask = EventMask.StructureNotify | EventMask.Exposure
        background = conn.core.AllocColor(screen.default_colormap, 0x2828, 0x8383, 0xCECE).reply().pixel  # Color "#2883ce"
        self.value_list = [
            background,
            0,
            # 1,
            self.event_mask,
            self.colormap,
        ]
        self.conn.flush()
        self.wid = conn.generate_id()
        self.create_window()
        self.conn.flush()
        
    @property
    def colormap(self):
        try:
            return self._colormap
        except AttributeError:
            cmap_id = self.conn.generate_id()
            self.conn.flush()
            cm = self.conn.core.CreateColormap(
                xcffib.xproto.ColormapAlloc._None,
                cmap_id,
                screen.root,
                self.visual,
                is_checked=True
            )
            cm.check()
            # self.conn.flush()
            print(cm)
            
            self.conn.flush()
            self._colormap = cmap_id
            return cmap_id

    def create_window(self):
        w = self.conn.core.CreateWindow(
            self.depth,
            self.wid,
            screen.root,
            self.x,
            self.y,
            self.width,
            self.height,
            self.border_width,
            xcffib.xproto.WindowClass.InputOutput,
            self.visual,
            # screen.root_visual,
            self.value_mask,
            self.value_list,
            is_checked=True,
        )
        w.check()



x = ExternalWindow(conn)
cmap = x.colormap

window = x.wid

# window = conn.generate_id()


# conn.core.CreateWindow(xcffib.CopyFromParent, window, screen.root,
#                        100, 100, 100, 100, 1,
#                        xcffib.xproto.WindowClass.InputOutput, screen.root_visual,
#                        xcffib.xproto.CW.BackPixel | xcffib.xproto.CW.EventMask | CW.OverrideRedirect,
#                        [background, xcffib.xproto.EventMask.StructureNotify | xcffib.xproto.EventMask.Exposure, 1])

name = 'yolo'
conn.core.ChangeProperty(xcffib.xproto.PropMode.Replace,
                         window, xcffib.xproto.Atom.WM_NAME,
                         xcffib.xproto.Atom.STRING, 8, len(name),
                         name)

wm_protocols = "WM_PROTOCOLS"
wm_protocols = conn.core.InternAtom(0, len(wm_protocols), wm_protocols).reply().atom

wm_delete_window = "WM_DELETE_WINDOW"
wm_delete_window = conn.core.InternAtom(0, len(wm_delete_window), wm_delete_window).reply().atom

# # https://github.com/ben0x539/overlay-thing/blob/master/xcb.c

conn.core.ChangeProperty(xcffib.xproto.PropMode.Replace,
                         window, wm_protocols,
                         xcffib.xproto.Atom.ATOM, 32, 1,
                         [wm_delete_window])

conn.core.ConfigureWindow(window,
                          xcffib.xproto.ConfigWindow.X | xcffib.xproto.ConfigWindow.Y |
                          xcffib.xproto.ConfigWindow.Width | xcffib.xproto.ConfigWindow.Height |
                          xcffib.xproto.ConfigWindow.BorderWidth,
                          [0, 0, 100, 100, 1])
conn.core.MapWindow(window)
conn.flush()
conn.core.ConfigureWindow(window,
                          xcffib.xproto.ConfigWindow.X | xcffib.xproto.ConfigWindow.Y |
                          xcffib.xproto.ConfigWindow.Width | xcffib.xproto.ConfigWindow.Height |
                          xcffib.xproto.ConfigWindow.BorderWidth,
                          [0, 0, 100, 100, 1])

conn.flush()

def killwindow():
    while True:
        e = conn.wait_for_event()
        print(e)
        if e.__class__ == xcffib.xproto.ClientMessageEvent:
            print('message event!')
            data = conn.core.GetAtomName(e.data.data32[0]).reply()
            print(data)
            data2 = data.name.to_string()
            print(data2)
            if data2 == 'WM_DELETE_WINDOW':
                break

    conn.core.UnmapWindow(window)
    conn.flush()


from threading import Thread

t = Thread(target=killwindow)
t.start()

t.join()

