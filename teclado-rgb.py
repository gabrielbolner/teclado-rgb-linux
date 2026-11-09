#!/usr/bin/env python3
import json
import os
import sys
import time
from pathlib import Path

LED = Path("/sys/class/leds/rgb:kbd_backlight")
CONFIG = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "teclado-rgb" / "config.json"
DEFAULT = {"color": [0, 255, 0], "brightness": 4}
PRESETS = [
    ("Vermelho", (255, 0, 0)),
    ("Laranja", (255, 80, 0)),
    ("Amarelo", (255, 200, 0)),
    ("Verde", (0, 255, 0)),
    ("Ciano", (0, 255, 255)),
    ("Azul", (0, 0, 255)),
    ("Roxo", (150, 0, 255)),
    ("Rosa", (255, 0, 150)),
    ("Branco", (255, 255, 255)),
]


def clamp(value, low, high):
    return max(low, min(high, int(value)))


def max_brightness():
    try:
        return int((LED / "max_brightness").read_text())
    except (OSError, ValueError):
        return 4


def load_config():
    try:
        data = json.loads(CONFIG.read_text())
        color = [clamp(c, 0, 255) for c in data["color"]][:3]
        if len(color) != 3:
            raise ValueError
        return {"color": color, "brightness": clamp(data["brightness"], 0, max_brightness())}
    except (OSError, ValueError, KeyError, TypeError):
        return {"color": list(DEFAULT["color"]), "brightness": DEFAULT["brightness"]}


def read_led_state():
    try:
        color = [clamp(c, 0, 255) for c in (LED / "multi_intensity").read_text().split()][:3]
        brightness = int((LED / "brightness").read_text())
        if len(color) == 3:
            return {"color": color, "brightness": brightness}
    except (OSError, ValueError):
        pass
    return None


def save_config(cfg):
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(cfg))


def apply(cfg):
    r, g, b = (clamp(c, 0, 255) for c in cfg["color"])
    (LED / "multi_intensity").write_text(f"{r} {g} {b}\n")
    (LED / "brightness").write_text(f"{clamp(cfg['brightness'], 0, max_brightness())}\n")


def writable():
    return LED.exists() and all(os.access(LED / f, os.W_OK) for f in ("multi_intensity", "brightness"))


def apply_saved_and_exit():
    for _ in range(20):
        if writable():
            break
        time.sleep(1)
    try:
        apply(load_config())
    except OSError as exc:
        print(f"teclado-rgb: não foi possível aplicar a cor: {exc}", file=sys.stderr)
        return 1
    return 0


def run_gui():
    import gi

    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Adw, Gdk, Gtk

    base_css = """
    .preview { border-radius: 14px; min-height: 76px; }
    .preview-label { font-weight: 700; font-size: 1.1em; }
    button.swatch {
        min-width: 42px; min-height: 42px; padding: 0; border-radius: 999px;
        background-image: none; border: 3px solid alpha(currentColor, 0.12);
    }
    button.swatch.selected { border-color: @accent_bg_color; box-shadow: 0 0 0 2px @window_bg_color inset; }
    """
    for index, (_, (r, g, b)) in enumerate(PRESETS):
        base_css += f"button.swatch-{index} {{ background-color: rgb({r},{g},{b}); }}\n"

    class Window(Adw.ApplicationWindow):
        def __init__(self, app):
            super().__init__(application=app, title="Teclado RGB")
            self.set_default_size(440, -1)
            self.updating = False
            self.max_brightness = max_brightness()
            self.cfg = load_config()
            current = read_led_state()
            if current:
                self.cfg = current

            self.preview_css = Gtk.CssProvider()
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(), self.preview_css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1
            )

            self.toasts = Adw.ToastOverlay()
            view = Adw.ToolbarView()
            view.add_top_bar(Adw.HeaderBar())
            self.toasts.set_child(view)
            self.set_content(self.toasts)

            outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            view.set_content(outer)

            self.banner = Adw.Banner(
                title="Sem permissão para controlar o teclado. Rode o install.sh do Teclado RGB."
            )
            self.banner.set_revealed(not writable())
            outer.append(self.banner)

            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=22)
            box.set_margin_top(18)
            box.set_margin_bottom(22)
            box.set_margin_start(18)
            box.set_margin_end(18)
            outer.append(box)

            self.preview = Gtk.Box()
            self.preview.add_css_class("preview")
            self.preview_label = Gtk.Label(hexpand=True, halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER)
            self.preview_label.add_css_class("preview-label")
            self.preview.append(self.preview_label)
            box.append(self.preview)

            colors = Adw.PreferencesGroup(title="Cor")
            flow = Gtk.FlowBox(
                selection_mode=Gtk.SelectionMode.NONE,
                homogeneous=True,
                max_children_per_line=9,
                min_children_per_line=5,
                column_spacing=8,
                row_spacing=8,
            )
            flow.set_margin_bottom(10)
            self.swatches = []
            for index, (name, rgb) in enumerate(PRESETS):
                button = Gtk.Button(tooltip_text=name, halign=Gtk.Align.CENTER)
                button.add_css_class("swatch")
                button.add_css_class(f"swatch-{index}")
                button.update_property([Gtk.AccessibleProperty.LABEL], [name])
                button.connect("clicked", self.on_preset, rgb)
                flow.append(button)
                self.swatches.append((button, rgb))
            colors.add(flow)

            custom_row = Adw.ActionRow(title="Cor personalizada")
            self.color_button = Gtk.ColorDialogButton(
                dialog=Gtk.ColorDialog(with_alpha=False, title="Escolha a cor"), valign=Gtk.Align.CENTER
            )
            self.color_button.connect("notify::rgba", self.on_custom)
            custom_row.add_suffix(self.color_button)
            custom_row.set_activatable_widget(self.color_button)
            listbox = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
            listbox.add_css_class("boxed-list")
            listbox.append(custom_row)
            colors.add(listbox)
            box.append(colors)

            light = Adw.PreferencesGroup(title="Brilho")
            self.scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, self.max_brightness, 1)
            self.scale.set_digits(0)
            self.scale.set_round_digits(0)
            self.scale.set_draw_value(False)
            for step in range(self.max_brightness + 1):
                label = "Desligado" if step == 0 else ("Máximo" if step == self.max_brightness else None)
                self.scale.add_mark(step, Gtk.PositionType.BOTTOM, label)
            self.scale.connect("value-changed", self.on_brightness)
            light.add(self.scale)
            box.append(light)

            self.refresh_ui()

        def on_preset(self, _button, rgb):
            self.cfg["color"] = list(rgb)
            if self.cfg["brightness"] == 0:
                self.cfg["brightness"] = self.max_brightness
            self.commit()

        def on_custom(self, button, _pspec):
            if self.updating:
                return
            rgba = button.get_rgba()
            self.cfg["color"] = [round(rgba.red * 255), round(rgba.green * 255), round(rgba.blue * 255)]
            if self.cfg["brightness"] == 0:
                self.cfg["brightness"] = self.max_brightness
            self.commit()

        def on_brightness(self, scale):
            if self.updating:
                return
            value = int(round(scale.get_value()))
            if value == self.cfg["brightness"]:
                return
            self.cfg["brightness"] = value
            self.commit()

        def commit(self):
            try:
                apply(self.cfg)
                self.banner.set_revealed(False)
            except OSError:
                self.banner.set_revealed(True)
                self.toasts.add_toast(Adw.Toast(title="Não consegui alterar o teclado (sem permissão)"))
            try:
                save_config(self.cfg)
            except OSError:
                pass
            self.refresh_ui()

        def refresh_ui(self):
            self.updating = True
            r, g, b = self.cfg["color"]
            level = self.cfg["brightness"]
            factor = 0 if level == 0 else 0.35 + 0.65 * level / self.max_brightness
            pr, pg, pb = (round(30 + (c - 30) * factor) for c in (r, g, b))
            luminance = 0.2126 * pr + 0.7152 * pg + 0.0722 * pb
            text = "#111111" if luminance > 140 else "#ffffff"
            self.preview_css.load_from_string(
                f".preview {{ background-color: rgb({pr},{pg},{pb}); }} .preview-label {{ color: {text}; }}"
            )
            self.preview_label.set_label(
                "Desligado" if level == 0 else f"#{r:02X}{g:02X}{b:02X}  ·  brilho {level}/{self.max_brightness}"
            )
            for button, rgb in self.swatches:
                if list(rgb) == self.cfg["color"]:
                    button.add_css_class("selected")
                else:
                    button.remove_css_class("selected")
            rgba = Gdk.RGBA()
            rgba.parse(f"rgb({r},{g},{b})")
            self.color_button.set_rgba(rgba)
            self.scale.set_value(level)
            self.updating = False

    class App(Adw.Application):
        def __init__(self):
            super().__init__(application_id="io.github.giordanowt.TecladoRGB")

        def do_startup(self):
            Adw.Application.do_startup(self)
            provider = Gtk.CssProvider()
            provider.load_from_string(base_css)
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

        def do_activate(self):
            window = self.get_active_window() or Window(self)
            window.present()

    return App().run([sys.argv[0]])


if __name__ == "__main__":
    if "--apply" in sys.argv[1:]:
        sys.exit(apply_saved_and_exit())
    sys.exit(run_gui())
