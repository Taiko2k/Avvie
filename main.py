# Avvie!

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
import sys
import math
import gi
import cairo
import urllib.parse
import subprocess
from PIL import Image, ImageFilter

gi.require_version("Gtk", "3.0")
gi.require_foreign("cairo")
gi.require_version('Notify', '0.7')
from gi.repository import Gtk, Gdk, Gio, GLib, Notify


app_title = "Avvie"
app_id = "com.github.taiko2k.avvie"
version = "1.0"

try:
    settings = Gtk.Settings.get_default()
    settings.set_property("gtk-application-prefer-dark-theme", True)
except AttributeError:
    print("Failed to get GTK settings")

background_color = (0.15, 0.15, 0.15)

Notify.init(app_title)
notify = Notify.Notification.new(app_title, "Image file exported to Downloads.")
notify_invalid_output = Notify.Notification.new(app_title, "Could not locate output Downloads folder!")

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


class Picture:
    def __init__(self):
        self.source_image = None
        self.surface = None
        self.source_w = 0
        self.source_h = 0
        self.display_w = 0
        self.display_h = 0
        self.display_x = 0
        self.display_y = 0
        self.ready = False
        self.lock_ratio = True

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
        self.bounds = (500, 500)

        self.surface184 = None

        self.file_name = ""
        self.base_folder = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD)
        self.sharpen = False
        self.export_constrain = None
        self.crop_ratio = None
        self.png = False
        self.crop = True
        self.slow_drag = False
        self.circle = False
        self.rotation = 0
        self.flip_hoz = False
        self.flip_vert = False
        self.gray = False

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

        if self.rotation and not hq:
            return

        im = self.source_image
        if not im:
            return

        if self.gray:
            im = im.convert("L")
            im = im.convert("RGB")

        if self.flip_hoz:
            im = im.transpose(method=Image.FLIP_LEFT_RIGHT)
        if self.flip_vert:
            im = im.transpose(method=Image.FLIP_TOP_BOTTOM)

        if self.rotation:
            im = im.rotate(self.rotation, expand=True, resample=Image.BICUBIC)

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

    def reload(self, keep_rect=False):

        im = self.source_image.copy()
        im.load()

        if self.flip_hoz:
            im = im.transpose(method=Image.FLIP_LEFT_RIGHT)
        if self.flip_vert:
            im = im.transpose(method=Image.FLIP_TOP_BOTTOM)

        if self.rotation:
            im = im.rotate(self.rotation, expand=True, resample=0)

        w, h = im.size
        self.source_w, self.source_h = w, h
        self.display_w, self.display_h = w, h
        self.display_x, self.display_y = 40, 40

        b_w, b_h = self.bounds

        if b_h > 100 and b_w > 100 and b_h - 80 < h:
            im.thumbnail((max(b_w - 320, 320), b_h - 80))
            self.display_w, self.display_h = im.size

        self.scale_factor = self.display_h / self.source_h
        if not keep_rect:
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
        self.confine()

    def set_ratio(self):

        if self.crop_ratio and self.crop_ratio != (1, 1):

            if self.crop_ratio == (21, 9) and abs(self.rec_h - 1080) < 50:
                self.rec_h = 1080
                self.rec_w = 2560

            elif self.crop_ratio == (16, 9) and abs(self.rec_h - 1080) < 50:
                self.rec_h = 1080
                self.rec_w = 1920

            else:
                a = self.rec_h // self.crop_ratio[1]
                self.rec_w = a * self.crop_ratio[0]
                self.rec_h = a * self.crop_ratio[1]

    def confine(self):

        if self.lock_ratio:
            self.set_ratio()

        # Confine mask rectangle to self
        if self.rec_x + self.rec_w > self.source_w:
            self.rec_x = self.source_w - self.rec_w
        if self.rec_y + self.rec_h > self.source_h:
            self.rec_y = self.source_h - self.rec_h

        if self.rec_x < 0:
            self.rec_x = 0
        if self.rec_y < 0:
            self.rec_y = 0

        if self.rec_w > self.source_w:
            self.rec_w = self.source_w
            if self.lock_ratio:
                if self.crop_ratio == (1, 1):
                    self.rec_h = self.rec_w

        if self.rec_h > self.source_h:
            self.rec_h = self.source_h
            if self.lock_ratio:
                self.rec_w = self.rec_h

    def load(self, path, bounds):

        self.file_name = os.path.splitext(os.path.basename(path))[0]
        self.bounds = bounds
        self.source_image = Image.open(path)
        self.reload()

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

    def export(self, path=None):

        if not os.path.isdir(self.base_folder):
            notify_invalid_output.show()

        im = self.source_image
        if not im:
            return

        if self.gray:
            im = im.convert("L")
            im = im.convert("RGB")


        if self.flip_hoz:
            im = im.transpose(method=Image.FLIP_LEFT_RIGHT)
        if self.flip_vert:
            im = im.transpose(method=Image.FLIP_TOP_BOTTOM)

        if self.rotation:
            im = im.rotate(self.rotation, expand=True, resample=Image.BICUBIC)

        cropped = False

        if self.crop:
            cr = im.crop((self.rec_x, self.rec_y, self.rec_x + self.rec_w, self.rec_y + self.rec_h))
            cr.load()
            cropped = True
        else:
            cr = im

        old_size = cr.size
        scaled = False

        if self.export_constrain:
            cr.thumbnail((self.export_constrain, self.export_constrain), Image.ANTIALIAS)

        if old_size != cr.size:
            scaled = True

        cr = self.apply_filters(cr)

        png = self.png

        overwrite = False

        if path is None:
            path = os.path.join(self.base_folder, self.file_name)

            if cropped:
                path += "-cropped"

            if scaled:
                path += "-scaled"

            ext = '.jpg'
            if png:
                ext = '.png'

        else:
            if path.lower().endswith(".png"):
                png = True
            else:
                png = False
            overwrite = True

        extra = ""

        if not overwrite:
            if os.path.isfile(path + ext):
                i = 0
                while True:
                    i += 1
                    extra = f"({str(i)})"
                    if not os.path.isfile(path + extra + ext):
                        break

            path = path + extra + ext

        if png:
            cr.save(path, "PNG")
        else:

            cr = cr.convert("RGB")
            cr.save(path, "JPEG", quality=95)

        if not overwrite:
            notify.show()


picture = Picture()


class Window(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title=app_title)

        GLib.set_application_name(app_title)
        GLib.set_prgname(app_id)

        # self.set_border_width(10)
        self.set_default_size(1200, 760)

        self.arrow_cursor = Gdk.Cursor(Gdk.CursorType.LEFT_PTR)
        self.drag_cursor = Gdk.Cursor(Gdk.CursorType.FLEUR)
        self.br_cursor = Gdk.Cursor(Gdk.CursorType.BOTTOM_RIGHT_CORNER)
        self.tr_cursor = Gdk.Cursor(Gdk.CursorType.TOP_RIGHT_CORNER)
        self.bl_cursor = Gdk.Cursor(Gdk.CursorType.BOTTOM_LEFT_CORNER)
        self.tl_cursor = Gdk.Cursor(Gdk.CursorType.TOP_LEFT_CORNER)

        self.about = Gtk.AboutDialog()

        self.rotate_reset_button = Gtk.Button(label="Reset rotation")
        self.preview_circle_check = Gtk.CheckButton()
        self.rot = Gtk.Scale.new_with_range(orientation=0, min=-180, max=180, step=4)

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

        self.set_events(self.get_events() | Gdk.EventMask.KEY_PRESS_MASK | Gdk.EventMask.KEY_RELEASE_MASK)

        draw.connect("button-press-event", self.click)
        draw.connect("button-release-event", self.click_up)
        draw.connect("motion-notify-event", self.mouse_motion)
        draw.connect("leave-notify-event", self.mouse_leave)
        self.connect("key-press-event", self.on_key_press_event)
        self.connect("key-release-event", self.on_key_release_event)

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
        button.set_tooltip_text("Open image file")
        icon = Gio.ThemedIcon(name="document-open-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        hb.pack_start(button)
        button.connect("clicked", self.open_file)

        button = Gtk.Button()
        button.set_tooltip_text("Export to Downloads folder")
        icon = Gio.ThemedIcon(name="document-save-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)
        button.connect("clicked", self.save)
        button.set_sensitive(False)
        self.open_button = button

        hb.pack_end(button)
        hb.pack_end(Gtk.Separator())

        popover = Gtk.Popover()

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.set_border_width(15)


        opt1 = Gtk.RadioButton.new_with_label_from_widget(None, "No Downscale")
        opt1.connect("toggled", self.toggle_menu_setting, "1:1")
        vbox.pack_start(child=opt1, expand=True, fill=False, padding=4)

        opt2 = Gtk.RadioButton.new_with_label_from_widget(opt1, "184")
        opt2.connect("toggled", self.toggle_menu_setting, "184")
        vbox.pack_start(child=opt2, expand=True, fill=False, padding=4)
        opt3 = Gtk.RadioButton.new_with_label_from_widget(opt2, "500")
        opt3.connect("toggled", self.toggle_menu_setting, "500")
        vbox.pack_start(child=opt3, expand=True, fill=False, padding=4)

        # opt3 = Gtk.RadioButton.new_with_label_from_widget(opt2, "750")
        # opt3.connect("toggled", self.toggle_menu_setting, "750")
        # vbox.pack_start(child=opt3, expand=True, fill=False, padding=4)

        opt4 = Gtk.RadioButton.new_with_label_from_widget(opt3, "1000")
        opt4.connect("toggled", self.toggle_menu_setting, "1000")
        vbox.pack_start(child=opt4, expand=True, fill=False, padding=4)

        opt4 = Gtk.RadioButton.new_with_label_from_widget(opt4, "1500")
        opt4.connect("toggled", self.toggle_menu_setting, "1000")
        vbox.pack_start(child=opt4, expand=True, fill=False, padding=4)

        vbox.pack_start(child=Gtk.Separator(), expand=True, fill=False, padding=4)

        pn = Gtk.CheckButton()
        pn.set_label("Export as PNG")
        pn.connect("toggled", self.toggle_menu_setting, "png")
        vbox.pack_start(child=pn, expand=True, fill=False, padding=4)

        sh = Gtk.CheckButton()
        sh.set_label("Sharpen")
        sh.connect("toggled", self.toggle_menu_setting, "sharpen")
        vbox.pack_start(child=sh, expand=True, fill=False, padding=4)

        sh = Gtk.CheckButton()
        sh.set_label("Grayscale")
        sh.connect("toggled", self.toggle_menu_setting, "grayscale")
        vbox.pack_start(child=sh, expand=True, fill=False, padding=4)

        self.preview_circle_check.set_label("Circle (Preview Only)")
        self.preview_circle_check.connect("toggled", self.toggle_menu_setting, "circle")
        vbox.pack_start(child=self.preview_circle_check, expand=True, fill=False, padding=4)

        vbox.pack_start(child=Gtk.Separator(), expand=True, fill=False, padding=4)

        vbox2 = vbox


        m1 = Gtk.ModelButton(label="Export As")
        m1.connect("clicked", self.export_as)
        vbox.pack_start(child=m1, expand=True, fill=False, padding=4)

        m1 = Gtk.ModelButton(label="About")
        m1.connect("clicked", self.show_about)
        vbox.pack_start(child=m1, expand=True, fill=False, padding=4)

        menu = Gtk.MenuButton()
        icon = Gio.ThemedIcon(name="open-menu-symbolic")
        menu.set_tooltip_text("Options Menu")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        menu.add(image)
        menu.set_popover(popover)

        hb.pack_end(menu)

        # CROP MENU ----------------------------------------------------------
        popover = Gtk.PopoverMenu()


        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.set_border_width(13)

        opt = Gtk.RadioButton.new_with_label_from_widget(None, "No Crop")
        opt.connect("toggled", self.toggle_menu_setting2, "none")
        vbox.pack_start(child=opt, expand=True, fill=False, padding=4)
        opt = Gtk.RadioButton.new_with_label_from_widget(opt, "Square")
        opt.connect("toggled", self.toggle_menu_setting2, "square")
        opt.set_active(True)
        vbox.pack_start(child=opt, expand=True, fill=False, padding=4)

        opt = Gtk.RadioButton.new_with_label_from_widget(opt, "Rectangle")
        opt.connect("toggled", self.toggle_menu_setting2, "rect")
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

        self.rotate_reset_button.connect("clicked", self.rotate_reset)
        self.rotate_reset_button.set_sensitive(False)

        self.rot.set_value(0)
        self.rot.set_size_request(180, -1)
        self.rot.set_draw_value(False)
        self.rot.set_has_origin(False)
        self.rot.connect("value-changed", self.rotate)
        vbox.pack_start(child=self.rot, expand=True, fill=False, padding=7)
        vbox.pack_start(child=self.rotate_reset_button, expand=True, fill=False, padding=7)

        flip_vert_button = Gtk.Button(label="Flip Vertical")
        flip_vert_button.connect("clicked", self.toggle_flip_vert)
        vbox.pack_start(child=flip_vert_button, expand=True, fill=False, padding=2)
        flip_hoz_button = Gtk.Button(label="Flip Horizontal")
        flip_hoz_button.connect("clicked", self.toggle_flip_hoz)
        vbox.pack_start(child=flip_hoz_button, expand=True, fill=False, padding=2)

        hbox.pack_start(child=vbox, expand=True, fill=False, padding=4)
        hbox.pack_start(child=Gtk.Separator(), expand=True, fill=False, padding=4)
        hbox.pack_start(child=vbox2, expand=True, fill=False, padding=4)

        popover.add(hbox)
        vbox.show_all()
        vbox2.show_all()
        hbox.show_all()

        menu.set_popover(popover)
        vbox.show_all()

        self.about.set_authors(["Taiko2k"])
        self.about.set_copyright("Copyright 2019 Taiko2k captain.gxj@gmail.com")
        self.about.set_license_type(Gtk.License(3))
        self.about.set_website("https://github.com/taiko2k/" + app_title.lower())
        self.about.set_website_label("Github")
        self.about.set_destroy_with_parent(True)
        self.about.set_version(version)
        self.about.set_logo_icon_name(app_id)

        for item in sys.argv:
            if not item.endswith(".py") and os.path.isfile(item):
                self.open_button.set_sensitive(True)
                picture.load(item, self.get_size())
                break

    def toggle_flip_vert(self, button):
        picture.flip_vert ^= True
        if picture.source_image:
            picture.reload(keep_rect=True)
            self.queue_draw()
            picture.gen_thumb_184(hq=True)

    def toggle_flip_hoz(self, button):
        picture.flip_hoz ^= True
        if picture.source_image:
            picture.reload(keep_rect=True)
            self.queue_draw()
            picture.gen_thumb_184(hq=True)

    def rotate_reset(self, button):

        picture.rotation = 0
        self.rot.set_value(0)
        if picture.source_image:
            picture.reload(keep_rect=True)
            self.queue_draw()
            picture.gen_thumb_184(hq=True)
        self.rotate_reset_button.set_sensitive(False)

    def rotate(self, scale):

        picture.rotation = scale.get_value()
        self.rotate_reset_button.set_sensitive(True)
        if picture.source_image:
            picture.reload(keep_rect=True)
            self.queue_draw()
            #picture.gen_thumb_184(hq=True)

    def on_key_press_event(self, widget, event):

        if event.keyval == Gdk.KEY_Control_L or event.keyval == Gdk.KEY_Control_R:
            picture.slow_drag = True
            picture.drag_start_position = None

    def on_key_release_event(self, widget, event):

        if event.keyval == Gdk.KEY_Control_L or event.keyval == Gdk.KEY_Control_R:
            picture.slow_drag = False
            picture.drag_start_position = None

    def show_about(self, button):
        self.about.run()
        self.about.hide()

    def export_as(self, button):

        if not picture.ready:
            return

        dialog = Gtk.FileChooserNative(title="Please choose where to save to", action=Gtk.FileChooserAction.SAVE)
        f = Gtk.FileFilter()
        f.set_name("Image files")
        f.add_mime_type("image/jpeg")
        f.add_mime_type("image/png")
        dialog.add_filter(f)

        choice = dialog.run()
        filename = dialog.get_filename()
        dialog.destroy()

        if choice == Gtk.ResponseType.ACCEPT:
            picture.export(filename)


    def toggle_menu_setting2(self, button, name):

        picture.lock_ratio = True

        if name == "rect":
            picture.crop = True
            picture.lock_ratio = False
            self.preview_circle_check.set_active(False)

        if name == "square":
            picture.crop = True
            picture.crop_ratio = (1, 1)
            picture.rec_w = picture.rec_h

        if name == '21:9':
            picture.crop = True
            picture.crop_ratio = (21, 9)
            if picture.source_w >= 2560:
                picture.rec_w = 2560
                picture.rec_h = 1080

            self.preview_circle_check.set_active(False)

        if name == '16:9':
            picture.crop = True
            picture.crop_ratio = (16, 9)
            self.preview_circle_check.set_active(False)

        if name == '16:10':
            picture.crop = True
            picture.crop_ratio = (16, 10)
            picture.circle = False
            self.preview_circle_check.set_active(False)

        if name == 'none':
            picture.crop_ratio = (1, 1)
            picture.crop = False

        self.confine()
        picture.gen_thumb_184(hq=True)
        self.queue_draw()

    def toggle_menu_setting(self, button, name):

        if name == 'circle':
            picture.circle ^= True
            self.queue_draw()

        if name == 'grayscale':
            picture.gray ^= True
            self.queue_draw()

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

        if name == "750" and button.get_active():
            picture.export_constrain = 750

        if name == "1000" and button.get_active():
            picture.export_constrain = 1000

        if name == "1500" and button.get_active():
            picture.export_constrain = 1500

        picture.gen_thumb_184(hq=True)
        self.queue_draw()

    def save(self, widget):

        picture.export()

    def open_file(self, widget):

        dialog = Gtk.FileChooserNative(title="Please choose a file", action=Gtk.FileChooserAction.OPEN)

        f = Gtk.FileFilter()
        f.set_name("Image files")
        f.add_mime_type("image/jpeg")
        f.add_mime_type("image/png")
        dialog.add_filter(f)

        dialog.run()
        filename = dialog.get_filename()
        dialog.destroy()

        if filename:
            print("File selected: " + filename)
            self.open_button.set_sensitive(True)
            picture.load(filename, self.get_size())



    def drag_drop_file(self, widget, context, x, y, selection, target_type, timestamp):

        if target_type == TARGET_TYPE_URI_LIST:
            uris = selection.get_data().strip()
            uri = uris.decode().splitlines()[0]

            if not uri.startswith("file://"):
                return
            path = urllib.parse.unquote(uri[7:])
            self.open_button.set_sensitive(True)
            if os.path.isfile(path):
                picture.load(path, self.get_size())

            self.queue_draw()

    def click(self, draw, event):

        if event.button == 1:

            w, h = self.get_size()
            if w - 200 < event.x < w - 200 + 184:
                if h - 200 < event.y < h - 200 + 184:
                    picture.circle ^= True

                    self.preview_circle_check.set_active(picture.circle)

                    self.queue_draw()

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
        
        picture.confine()

    def mouse_motion(self, draw, event):

        if not picture.source_image:
            return

        if event.state & Gdk.ModifierType.BUTTON1_MASK and picture.crop:

            rx, ry, rw, rh = picture.get_display_rect()

            if picture.drag_start_position is None:
                picture.drag_start_position = (event.x, event.y)
                picture.original_position = (rx, ry)
                picture.original_drag_size = (rw, rh)

            offset_x = event.x - picture.drag_start_position[0]
            offset_y = event.y - picture.drag_start_position[1]

            if picture.dragging_center and not (picture.dragging_tl or
                                                picture.dragging_bl or
                                                picture.dragging_br or
                                                picture.dragging_tr):

                # Drag mask rectangle relative to original click position
                x_offset = event.x - picture.drag_start_position[0]
                y_offset = event.y - picture.drag_start_position[1]

                if picture.slow_drag:
                    x_offset = x_offset // 10
                    y_offset = y_offset // 10

                rx = round(picture.original_position[0] + x_offset)
                ry = round(picture.original_position[1] + y_offset)

            elif not picture.lock_ratio:

                if picture.dragging_tr:

                    ry = round(picture.original_position[1] + offset_y)
                    rh = round(picture.original_drag_size[1] - offset_y)
                    rw = round(picture.original_drag_size[0] + offset_x)

                if picture.dragging_bl:

                    rx = round(picture.original_position[0] + offset_x)
                    rh = round(picture.original_drag_size[1] + offset_y)
                    rw = round(picture.original_drag_size[0] - offset_x)

                elif picture.dragging_tl:

                    rx = round(picture.original_position[0] + offset_x)
                    rw = round(picture.original_drag_size[0] - offset_x)

                    ry = round(picture.original_position[1] + offset_y)
                    rh = round(picture.original_drag_size[1] - offset_y)

                elif picture.dragging_br:

                    rw = round(picture.original_drag_size[0] + offset_x)
                    rh = round(picture.original_drag_size[1] + offset_y)

            else:

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

                    rw = round(picture.original_drag_size[0] + offset)
                    rh = round(picture.original_drag_size[1] + offset)

            if rw < 30:
                rw = 30
            if rh < 30:
                rh = 30

            picture.save_display_rect(rx, ry, rw, rh)

            picture.corner_hot_area = min(rh * 0.2, 40)

            self.confine()
            picture.gen_thumb_184()
            self.queue_draw()

        else:
            picture.dragging_center = False

        gdk_window = self.get_window()

        if picture.crop:
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
                elif picture.lock_ratio and picture.crop_ratio != (1, 1):
                    if picture.rec_w / picture.crop_ratio[0] * picture.crop_ratio[1] == picture.rec_h:
                        c.set_source_rgba(0.9, 0.9, 0.4, 1)

                c.show_text(f"{picture.rec_w} x {picture.rec_h}")

            w, h = self.get_size()


            ex_w = picture.rec_w
            ex_h = picture.rec_h
            ratio = ex_h / ex_w

            if picture.export_constrain:
                if ex_w > picture.export_constrain:
                    ex_w = picture.export_constrain
                    ex_h = int(ex_w * ratio)
                if ex_h > picture.export_constrain:
                    ex_h = picture.export_constrain
                    ex_w = int(ex_w * ratio)

            if not picture.surface184:
                picture.gen_thumb_184(hq=True)
            if picture.surface184:
                c.move_to(0, 0)

                if picture.circle:
                    c.save()
                    c.arc(w - 200 + (184 // 2), h - 200 + (184 // 2), 184 // 2, 0, 2 * math.pi)
                    c.clip()
                    c.set_source_surface(picture.surface184, w - 200, h - 200)
                    c.paint()
                    c.restore()
                else:
                    c.set_source_surface(picture.surface184, w - 200, h - 200)
                    c.paint()

                c.select_font_face("Sans")
                c.set_font_size(13)
                c.move_to(w - 200, h - 205)

                c.set_source_rgba(0.4, 0.4, 0.4, 1)
                c.show_text(f"{ex_w} x {ex_h}")


win = Window()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
notify.close()
notify_invalid_output.close()
