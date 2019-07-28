# Avie!

# Copyright 2019 Taiko2k captain(dot)gxj(at)gmail.com

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import math
import gi
import cairo
import subprocess
from PIL import Image, ImageFilter

gi.require_version("Gtk", "3.0")
gi.require_foreign("cairo")
gi.require_version('Notify', '0.7')
from gi.repository import Gtk, Gdk, Gio, GLib, Notify


app_title = "Avie"

settings = Gtk.Settings.get_default()
settings.set_property("gtk-application-prefer-dark-theme", True)
background_color = (0.15, 0.15, 0.15)


Notify.init(app_title)
notify = Notify.Notification.new(app_title, "Image file exported to Downloads.")

TARGET_TYPE_URI_LIST = 80

def open_encode_out(notification, action, data):
    subprocess.call(["xdg-open", picture.base_folder])


notify.add_action(
    "action_click",
    "Open output folder",
    open_encode_out,
    None
)


def point_prox(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


class Glo:
    def __init__(self):

        self.spacing = 100


glo = Glo()


class Picture:
    def __init__(self):
        self.source_image = None
        self.source_w = 0
        self.source_h = 0
        self.display_w = 0
        self.display_h = 0
        self.display_x = 0
        self.display_y = 0
        self.ready = False

        self.rec_x = 10
        self.rec_y = 10
        self.rec_w = 250
        self.rec_h = 250

        self.drag_start_position = (0, 0)

        self.dragging_center = False
        self.dragging_tr = False
        self.dragging_tl = False
        self.dragging_bl = False
        self.dragging_br = False
        self.original_position = (0, 0)
        self.original_drag_size = (0, 0)

        self.scale_factor = 1

        self.surface184 = None

        self.file_name = ""
        self.base_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        self.sharpen = False
        self.export_constrain = None
        self.crop_ratio = None
        self.png = False
        self.crop = True

        self.corner_hot_area = 40


    def test_br(self, x, y):
        rx, ry, rw, rh = self.get_display_rect()
        return point_prox(x, y, picture.display_x + rx + rw, picture.display_y + ry + rh) < self.corner_hot_area

    def test_tl(self, x, y):
        rx, ry, rw, rh = self.get_display_rect()
        return point_prox(x, y, picture.display_x + rx, picture.display_y + ry) < self.corner_hot_area

    def test_bl(self, x, y):
        rx, ry, rw, rh = self.get_display_rect()
        return point_prox(x, y, picture.display_x + rx, picture.display_y + ry + rh) < self.corner_hot_area

    def test_tr(self, x, y):
        rx, ry, rw, rh = self.get_display_rect()
        return point_prox(x, y, picture.display_x + rx + rw, picture.display_y + ry) < self.corner_hot_area

    def test_center_start_drag(self, x, y):

        rx, ry, rw, rh = self.get_display_rect()

        border = self.corner_hot_area / 2
        if x < self.display_x + rx + border:
            return False
        if y < self.display_y + ry + border:
            return False
        if x > self.display_x + rx + rw - border:
            return False
        if y > self.display_y + ry + rh - border:
            return False
        return True

    def apply_filters(self, im):

        if self.sharpen:
            im = im.filter(ImageFilter.UnsharpMask(radius=0.35, percent=150, threshold=0))

        return im

    def gen_thumb_184(self, hq=False):

        im = self.source_image
        if not im:
            return

        if self.crop:
            cr = im.crop((self.rec_x, self.rec_y, self.rec_x + self.rec_w, self.rec_y + self.rec_h))
        else:
            cr = im.copy()

        cr.load()
        if not hq:
            cr.thumbnail((184, 184), Image.NEAREST)  # BILINEAR
        else:
            cr.thumbnail((184, 184), Image.ANTIALIAS)

        w, h = cr.size

        if "A" not in cr.getbands():
            cr.putalpha(int(1 * 256.0))

        cr = self.apply_filters(cr)


        by = cr.tobytes("raw", "BGRa")
        arr = bytearray(by)
        self.surface184 = cairo.ImageSurface.create_for_data(
            arr, cairo.FORMAT_ARGB32, w, h
        )

    def load(self, path, bounds):

        self.file_name = os.path.splitext(os.path.basename(path))[0]

        im = Image.open(path)


        # im = im.rotate(20, expand=True)
        self.source_image = im

        w, h = im.size
        self.source_w, self.source_h = w, h

        im = im.copy()

        glo.spacing = 100

        self.display_w, self.display_h = w, h
        self.display_x, self.display_y = 40, 40

        b_w, b_h = bounds

        if b_h > 100 and b_w > 100 and b_h - 80 < h:
            im.thumbnail((max(b_w - 320, 320), b_h - 80))
            self.display_w, self.display_h = im.size

        self.scale_factor = self.display_h / self.source_h
        print(self.scale_factor)
        self.rec_w = round(250 / self.scale_factor)
        self.rec_h = self.rec_w

        if "A" not in im.getbands():
            im.putalpha(int(1 * 256.0))

        by = im.tobytes("raw", "BGRa")
        arr = bytearray(by)
        self.surface = cairo.ImageSurface.create_for_data(
            arr, cairo.FORMAT_ARGB32, self.display_w, self.display_h
        )
        self.ready = True

    def get_display_rect(self):

        return (round(self.rec_x * self.scale_factor),
                round(self.rec_y * self.scale_factor),
                round(self.rec_w * self.scale_factor),
                round(self.rec_h * self.scale_factor))

    def save_display_rect(self, x, y, w, h):

        self.rec_x = round(x / self.scale_factor)
        self.rec_y = round(y / self.scale_factor)
        self.rec_w = round(w / self.scale_factor)
        self.rec_h = round(h / self.scale_factor)

    def export(self):

        im = self.source_image
        if not im:
            return

        if self.crop:
            cr = im.crop((self.rec_x, self.rec_y, self.rec_x + self.rec_w, self.rec_y + self.rec_h))
            cr.load()
        else:
            cr = im

        if self.export_constrain:
            cr.thumbnail((self.export_constrain, self.export_constrain), Image.ANTIALIAS)

        # if not hq:
        #     cr.thumbnail((184, 184), Image.NEAREST)  #BILINEAR
        # else:
        #     cr.thumbnail((184, 184), Image.ANTIALIAS)
        cr = self.apply_filters(cr)

        w, h = cr.size


        path = os.path.join(self.base_folder, self.file_name + "-cropped")

        if self.png:
            path += ".png"
            cr.save(path, "PNG")
        else:
            path += '.jpg'
            cr = cr.convert("RGB")
            cr.save(path, "JPEG", quality=95)

        notify.show()


picture = Picture()


class Window(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title=app_title)

        GLib.set_application_name(app_title)
        GLib.set_prgname('com.github.taiko2k.avie')

        # self.set_border_width(10)
        self.set_default_size(1200, 700)

        self.arrow_cursor = Gdk.Cursor(Gdk.CursorType.LEFT_PTR)
        self.drag_cursor = Gdk.Cursor(Gdk.CursorType.FLEUR)
        self.br_cursor = Gdk.Cursor(Gdk.CursorType.BOTTOM_RIGHT_CORNER)
        self.tr_cursor = Gdk.Cursor(Gdk.CursorType.TOP_RIGHT_CORNER)
        self.bl_cursor = Gdk.Cursor(Gdk.CursorType.BOTTOM_LEFT_CORNER)
        self.tl_cursor = Gdk.Cursor(Gdk.CursorType.TOP_LEFT_CORNER)

        self.about = Gtk.AboutDialog()

        self.setup_window()

    def setup_window(self):

        draw = Gtk.DrawingArea()
        self.add(draw)

        draw.set_events(
            draw.get_events()
            | Gdk.EventMask.LEAVE_NOTIFY_MASK
            | Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.POINTER_MOTION_HINT_MASK
        )

        draw.connect("button-press-event", self.click)
        draw.connect("button-release-event", self.click_up)
        draw.connect("motion-notify-event", self.mouse_motion)
        draw.connect("leave-notify-event", self.mouse_leave)

        draw.connect("draw", self.draw)
        self.connect("drag_data_received", self.drag_drop_file)
        self.drag_dest_set(
            Gtk.DestDefaults.MOTION
            | Gtk.DestDefaults.HIGHLIGHT
            | Gtk.DestDefaults.DROP,
            [Gtk.TargetEntry.new("text/uri-list", 0, 80)],
            Gdk.DragAction.COPY,
        )

        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.props.title = app_title
        self.set_titlebar(hb)

        button = Gtk.Button()
        icon = Gio.ThemedIcon(name="document-open-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        hb.pack_start(button)
        button.connect("clicked", self.open_file)

        button = Gtk.Button()
        icon = Gio.ThemedIcon(name="document-save-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        button.connect("clicked", self.save)

        hb.pack_end(button)

        popover = Gtk.Popover()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.set_border_width(15)

        vbox.pack_start(child=Gtk.Separator(), expand=True, fill=False, padding=4)

        # label = Gtk.Label(label="Maximum size for downscale")
        # vbox.pack_start(child=label, expand=True, fill=False, padding=4)


        opt1 = Gtk.RadioButton.new_with_label_from_widget(None, "No downscale")
        opt1.connect("toggled", self.toggle_menu_setting, "1:1")
        vbox.pack_start(child=opt1, expand=True, fill=False, padding=4)
        opt2 = Gtk.RadioButton.new_with_label_from_widget(opt1, "184x184 max")
        opt2.connect("toggled", self.toggle_menu_setting, "184")
        vbox.pack_start(child=opt2, expand=True, fill=False, padding=4)
        opt3 = Gtk.RadioButton.new_with_label_from_widget(opt2, "500x500 max")
        opt3.connect("toggled", self.toggle_menu_setting, "500")
        vbox.pack_start(child=opt3, expand=True, fill=False, padding=4)
        opt4 = Gtk.RadioButton.new_with_label_from_widget(opt3, "1000x1000 max")
        opt4.connect("toggled", self.toggle_menu_setting, "1000")
        vbox.pack_start(child=opt4, expand=True, fill=False, padding=4)

        vbox.pack_start(child=Gtk.Separator(), expand=True, fill=False, padding=4)

        pn = Gtk.CheckButton()
        pn.set_label("Save as PNG")
        pn.connect("toggled", self.toggle_menu_setting, "png")
        vbox.pack_start(child=pn, expand=True, fill=False, padding=4)

        sh = Gtk.CheckButton()
        sh.set_label("Sharpen")
        sh.connect("toggled", self.toggle_menu_setting, "sharpen")
        vbox.pack_start(child=sh, expand=True, fill=False, padding=4)

        vbox.pack_start(child=Gtk.Separator(), expand=True, fill=False, padding=4)

        about_button = Gtk.Button(label="About")
        about_button.connect("clicked", self.show_about)
        vbox.pack_start(child=about_button, expand=True, fill=False, padding=4)

        popover.add(vbox)
        vbox.show_all()

        menu = Gtk.MenuButton()
        icon = Gio.ThemedIcon(name="open-menu-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        menu.add(image)
        menu.set_popover(popover)

        hb.pack_end(menu)


        # CROP MENU ----------------------------------------------------------
        menu = Gtk.MenuButton()
        icon = Gio.ThemedIcon(name="insert-image-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        menu.add(image)

        popover = Gtk.Popover()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.set_border_width(13)

        opt = Gtk.RadioButton.new_with_label_from_widget(None, "No Crop")
        opt.connect("toggled", self.toggle_menu_setting2, "none")
        vbox.pack_start(child=opt, expand=True, fill=False, padding=4)
        opt = Gtk.RadioButton.new_with_label_from_widget(opt, "Square")
        opt.connect("toggled", self.toggle_menu_setting2, "square")
        opt.set_active(True)
        vbox.pack_start(child=opt, expand=True, fill=False, padding=4)
        opt = Gtk.RadioButton.new_with_label_from_widget(opt, "16:10")
        opt.connect("toggled", self.toggle_menu_setting2, "16:10")
        vbox.pack_start(child=opt, expand=True, fill=False, padding=4)
        opt = Gtk.RadioButton.new_with_label_from_widget(opt, "16:9")
        opt.connect("toggled", self.toggle_menu_setting2, "16:9")
        vbox.pack_start(child=opt, expand=True, fill=False, padding=4)
        opt = Gtk.RadioButton.new_with_label_from_widget(opt, "21:9")
        opt.connect("toggled", self.toggle_menu_setting2, "21:9")
        vbox.pack_start(child=opt, expand=True, fill=False, padding=4)



        popover.add(vbox)
        menu.set_popover(popover)
        vbox.show_all()

        hb.pack_start(Gtk.Separator())
        hb.pack_start(menu)


        self.about.set_authors(["Taiko2k"])
        self.about.set_copyright("Copyright 2019 Taiko2k captain.gxj@gmail.com")
        self.about.set_license_type(Gtk.License(3))
        self.about.set_website("https://github.com/taiko2k")
        self.about.set_destroy_with_parent(True)
        self.about.set_logo_icon_name('com.github.taiko2k.tauonmb')

    def show_about(self, button):
        self.about.run()
        self.about.hide()

    def toggle_menu_setting2(self, button, name):

        print(name)

        if name == "square":
            picture.crop = True
            picture.crop_ratio = (1, 1)
            picture.rec_w = picture.rec_h

        if name == '21:9':
            picture.crop_ratio = (21, 9)
            if picture.source_w >= 2560:
                picture.rec_w = 2560
                picture.rec_h = 1080

        if name == '16:9':
            picture.crop = True
            picture.crop_ratio = (16, 9)

        if name == '16:10':
            picture.crop = True
            picture.crop_ratio = (16, 10)

        if name == 'none':
            picture.crop_ratio = (1, 1)
            picture.crop = False

        self.confine()
        picture.gen_thumb_184(hq=True)
        self.queue_draw()

    def toggle_menu_setting(self, button, name):

        if name == 'sharpen':
            picture.sharpen = button.get_active()

        if name == "png":
            picture.png = button.get_active()

        if name == "1:1" and button.get_active():
            picture.export_constrain = None

        if name == "184" and button.get_active():
            picture.export_constrain = 184

        if name == "500" and button.get_active():
            picture.export_constrain = 500

        if name == "1000" and button.get_active():
            picture.export_constrain = 1000

        picture.gen_thumb_184(hq=True)
        self.queue_draw()


    def save(self, widget):

        picture.export()

    def open_file(self, widget):

        dialog = Gtk.FileChooserDialog(
            title="Please choose a file", parent=self, action=Gtk.FileChooserAction.OPEN
        )

        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )

        f = Gtk.FileFilter()
        f.set_name("Image files")
        f.add_mime_type("image/jpeg")
        f.add_mime_type("image/png")
        dialog.add_filter(f)

        response = dialog.run()
        filename = dialog.get_filename()
        dialog.destroy()

        if response == Gtk.ResponseType.OK:
            print("Open clicked")
            print("File selected: " + filename)
            picture.load(filename, self.get_size())
        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel clicked")

    def drag_drop_file(self, widget, context, x, y, selection, target_type, timestamp):

        if target_type == TARGET_TYPE_URI_LIST:
            uris = selection.get_data().strip()
            uri = uris.decode().splitlines()[0]

            if not uri.startswith("file://"):
                return
            path = uri[7:]
            if os.path.isfile(path):
                picture.load(path, self.get_size())
            self.queue_draw()

    def click(self, draw, event):

        if event.button == 1:

            if not picture.source_image or not picture.crop:
                return

            rx, ry, rw, rh = picture.get_display_rect()

            if picture.test_tl(event.x, event.y):
                picture.dragging_tl = True
            if picture.test_br(event.x, event.y):
                picture.dragging_br = True
            if picture.test_tr(event.x, event.y):
                picture.dragging_tr = True
            if picture.test_bl(event.x, event.y):
                picture.dragging_bl = True

            if picture.test_center_start_drag(event.x, event.y):
                picture.dragging_center = True

            picture.drag_start_position = (event.x, event.y)
            picture.original_position = (rx, ry)
            picture.original_drag_size = (rw, rh)

    def click_up(self, draw, event):

        if event.button == 1:
            picture.dragging_center = False
            picture.dragging_tl = False
            picture.dragging_br = False
            picture.dragging_bl = False
            picture.dragging_tr = False
            picture.gen_thumb_184(hq=True)



        self.queue_draw()

    def mouse_leave(self, draw, event):

        self.get_window().set_cursor(self.arrow_cursor)

    def confine(self):

        # Confine mask rectangle to picture
        if picture.rec_x + picture.rec_w > picture.source_w:
            picture.rec_x = picture.source_w - picture.rec_w
        if picture.rec_y + picture.rec_h > picture.source_h:
            picture.rec_y = picture.source_h - picture.rec_h

        if picture.rec_x < 0:
            picture.rec_x = 0
        if picture.rec_y < 0:
            picture.rec_y = 0

        if picture.rec_w > picture.source_w:
            picture.rec_w = picture.source_w
            if picture.crop_ratio == (1, 1):
                picture.rec_h = picture.rec_w

        if picture.rec_h > picture.source_h:
            picture.rec_h = picture.source_h
            picture.rec_w = picture.rec_h

        if picture.crop_ratio and picture.crop_ratio != (1, 1):

            if picture.crop_ratio == (21, 9) and abs(picture.rec_h - 1080) < 50:
                picture.rec_h = 1080
                picture.rec_w = 2560

            elif picture.crop_ratio == (16, 9) and abs(picture.rec_h - 1080) < 50:
                picture.rec_h = 1080
                picture.rec_w = 1920

            else:
                a = picture.rec_h // picture.crop_ratio[1]
                picture.rec_w = a * picture.crop_ratio[0]
                picture.rec_h = a * picture.crop_ratio[1]



    def mouse_motion(self, draw, event):

        if not picture.source_image:
            return

        if event.state & Gdk.ModifierType.BUTTON1_MASK and picture.crop:
            pass

            offset_x = event.x - picture.drag_start_position[0]
            offset_y = event.y - picture.drag_start_position[1]

            rx, ry, rw, rh = picture.get_display_rect()

            if picture.dragging_tr:

                offset = ((offset_x + (offset_y * -1)) / 2)
                ry = round(picture.original_position[1] - offset)
                rh = round(picture.original_drag_size[1] + offset)
                rw = round(picture.original_drag_size[0] + offset)

            if picture.dragging_bl:

                offset = (((offset_x * -1) + offset_y) / 2)
                rx = round(picture.original_position[0] - offset)
                rh = round(picture.original_drag_size[1] + offset)
                rw = round(picture.original_drag_size[0] + offset)

            elif picture.dragging_tl:

                offset = ((offset_x + offset_y) / 2) * -1

                rx = round(picture.original_position[0] - offset)
                rw = round(picture.original_drag_size[0] + offset)

                ry = round(picture.original_position[1] - offset)
                rh = round(picture.original_drag_size[1] + offset)

            elif picture.dragging_br:

                offset = (offset_x + offset_y) / 2

                # picture.rec_x = round(picture.original_position[0] - offset)
                rw = round(picture.original_drag_size[0] + offset)

                # picture.rec_y = round(picture.original_position[1] - offset)
                rh = round(picture.original_drag_size[1] + offset)


            elif picture.dragging_center:

                # Drag mask rectangle relative to original click position
                x_offset = event.x - picture.drag_start_position[0]
                y_offset = event.y - picture.drag_start_position[1]

                # x_offset = x_offset // 6
                # y_offset = y_offset // 6

                rx = round(picture.original_position[0] + x_offset)
                ry = round(picture.original_position[1] + y_offset)

            picture.save_display_rect(rx, ry, rw, rh)

            picture.corner_hot_area = min(rh * 0.2, 40)

            self.confine()
            picture.gen_thumb_184()
            self.queue_draw()

        else:
            picture.dragging_center = False

        gdk_window = self.get_window()

        if picture.test_br(event.x, event.y):
            gdk_window.set_cursor(self.br_cursor)
        elif picture.test_tr(event.x, event.y):
            gdk_window.set_cursor(self.tr_cursor)
        elif picture.test_bl(event.x, event.y):
            gdk_window.set_cursor(self.bl_cursor)
        elif picture.test_tl(event.x, event.y):
            gdk_window.set_cursor(self.tl_cursor)
        elif picture.test_center_start_drag(event.x, event.y) or picture.dragging_center:
            gdk_window.set_cursor(self.drag_cursor)
        else:
            gdk_window.set_cursor(self.arrow_cursor)

    def draw(self, wid, c):

        w, h = self.get_size()

        # Draw background colour
        c.set_source_rgb(background_color[0], background_color[1], background_color[2])
        c.paint()

        # Draw background grid
        c.set_source_rgb(0.3, 0.3, 0.3)
        c.set_line_width(1)

        size = 8
        for y in range(0, h + 20, 100):
            y += 40
            for x in range(0, w + 20, 100):
                x += 40

                c.move_to(x - size, y)
                c.line_to(x + size, y)
                c.stroke()

                c.move_to(x, y - size)
                c.line_to(x, y + size)
                c.stroke()

        # Draw image
        if picture.ready:

            x = picture.display_x
            y = picture.display_y
            w = picture.display_w
            h = picture.display_h

            c.set_source_surface(picture.surface, x, y)
            c.paint()

            c.set_source_rgba(0, 0, 0, 0.8)

            if picture.crop:
                rx, ry, rw, rh = picture.get_display_rect()

                # Mask out rectangle
                c.rectangle(x, y, rx, h)
                c.fill()
                c.rectangle(x + rx, y, w - rx, ry)
                c.fill()
                c.rectangle(x + rx + rw, y + ry, w - rx - rw, h - ry)
                c.fill()
                c.rectangle(x + rx, y + ry + rh, rw, h - ry - rh)
                c.fill()

                # Draw mask rectangle outline
                c.set_source_rgba(0.6, 0.6, 0.6, 1)
                c.rectangle(x + rx, y + ry, rw, rh)
                c.stroke()

                # Draw mask center lines
                c.set_source_rgba(0.6, 0.6, 0.6, 0.6)
                c.move_to(x + rx + rw // 2, y + ry)
                c.line_to(x + rx + rw // 2, y + ry + rh)
                c.stroke()
                c.move_to(x + rx, y + ry + rh // 2)
                c.line_to(x + rx + rw, y + ry + rh // 2)
                c.stroke()

                c.select_font_face("Sans")
                c.set_font_size(13)
                c.move_to(x + rx, y + ry - 5)

                if picture.rec_h == 1080 and (picture.rec_w == 2560 or picture.rec_w == 1920):
                    c.set_source_rgba(0.2, 0.9, 0.2, 1)

                c.show_text(f"{picture.rec_w} x {picture.rec_h}")

            w, h = self.get_size()
            if not picture.surface184:
                picture.gen_thumb_184(hq=True)
            if picture.surface184:
                c.move_to(0, 0)
                c.set_source_surface(picture.surface184, w - 200, h - 200)
                c.paint()


win = Window()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
