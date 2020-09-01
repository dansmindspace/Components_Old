#!/usr/bin/env python3
__app_name__    = 'Etv'
__author__      = ['Dan Dahl']
__version__     = 1.0
__copyright__   = 'GNU GPLv3'


"""

    TODO:
    - Refactor JSON Template
    - Simplify Row Color Implementation
    - Add PyDoc Comments

"""


import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, Gdk, GLib, GObject

prev_text = ''


class TreeView(Gtk.TreeView):
    '''Enhanced TreeView
    Simply handles row bgcolor(Gdk.RGBA) - Wip
    Handles Cell based Context Menus - Finished
    Handles Tool Tips for Text overflow/elipsisation - Mostly Finished
    JSON template to describe columns - Wip
    '''

    def __init__(self, store=None, templates=None, *, tooltip_func=None):

        Gtk.TreeView.__init__(self, store)
        self.ROW_COLOR = dict()
        self.menu = None
        self.connect('button_press_event', self._show_context_menu)

        if tooltip_func:
            self._tooltip_func = tooltip_func
            self.props.has_tooltip = True
            self.connect('query-tooltip', self._on_query_tooltip)

        if templates:
            for i, template in enumerate(templates):
                title = template['title'] if 'title' in template else ''
                renderer = template['renderer']()
                props = template['properties'] if 'properties' in template else {}
                attrs = template['attributes'] if 'attributes' in template else {}
                connections = template['connect'] if 'connect' in template else {}

                for prop, val in props.items():
                    renderer.set_property(prop, val)
                for signal, callback in connections.items():
                    renderer.connect(signal, callback)
                col = Gtk.TreeViewColumn(title, renderer)
                for attr, idx in attrs.items():
                    col.add_attribute(renderer, attr, idx)
                if 'fixed-width' in template:
                    col.set_fixed_width(template['fixed-width'])
                if 'sort-column' in template:
                    col.set_sort_column_id(template['sort-column'])
                self.append_column(col)

    # ========================================
    # =           Handle Row Color           =
    # ========================================

    # ROW_COLOR = [[Gdk.RGBA(0,0,0,.2), Gdk.RGBA(0,0,0,.1)], [Gdk.RGBA(255,0,0,.2), Gdk.RGBA(255,0,0,.1)]]

    def __cell_data_func(self, column, cell, model, iter, data):
        # -----------  Tooltip Index  -----------
        
        if not hasattr(column, 'tooltip_idx'):
            for i, entry in enumerate(model[iter]):
                if isinstance(entry, str) and cell.props.text in entry:
                    column.tooltip_idx = i

        # -----------  Row Color  -----------
        
        siter = model.get_string_from_iter(iter).split(':')
        depth = len(siter) - 1
        eo = int(siter[depth]) % 2
        bgrgba = None

        if depth in self.ROW_COLOR:
            if len(self.ROW_COLOR[depth]) == 2:
                bgrgba = self.ROW_COLOR[depth][eo]
            elif len(self.ROW_COLOR[depth]) == 1:
                bgrgba = self.ROW_COLOR[depth][0]

        cell.set_property('cell_background_rgba', bgrgba)

    def append_column(self, col):
        for cell in col.get_cells():
            col.set_cell_data_func(cell, self.__cell_data_func)
        super().append_column(col)

    def set_cell_background_rgba(self, rgba, depth=0):
        if isinstance(rgba, Gdk.RGBA):
            rgba = [rgba]
        elif not isinstance(rgba, (list, tuple)):
            raise ValueError(
                f'Expected either a single Gdk.RGBA or a List/Tuple of two Gdk.RGBAs. Got {rgba}')

        self.ROW_COLOR[depth] = rgba

    # ======  End of Handle Row Color  =======

    # =======================================
    # =           Scrolled Window           =
    # =======================================

    def asScrolledWindow(self):
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.add(self)
        scrolled_window.set_policy(
            Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        return scrolled_window

    # ======  End of Scrolled Window  =======

    # ====================================
    # =           Context Menu           =
    # ====================================

    def attatchContextMenu(self, menu_func):
        self.menu = menu_func

    def _show_context_menu(self, widget, event):
        if self.menu and event.button == 3:
            result = self.get_path_at_pos(event.x, event.y)
            if result:
                path, column, _, _ = result
                menu = self.menu(column, path)
                menu.show_all()
                menu.popup(None, None, None, None, event.button, event.time)

    # ======  End of Context Menu  =======

    # ================================
    # =           Tool Tip           =
    # ================================

    def _on_query_tooltip(self, treeview, x, y, keyboard_mode, tooltip):
        if keyboard_mode:
            path, column = self.get_cursor()
            if not path:
                return False
        else:
            bin_x, bin_y = self.convert_widget_to_bin_window_coords(x, y)
            result = self.get_path_at_pos(bin_x, bin_y)
            if result is None:
                return False
            path, column, _, _ = result

        tooltip_idx = column.tooltip_idx
        show = self._tooltip_func(treeview, path, column, tooltip_idx, tooltip)
        self.set_tooltip_cell(tooltip, path, column, column.get_cells()[0])
        return show

    @staticmethod
    def tooltip_ellisized_text(treeview, path, col, tooltip_idx, tooltip):
        font_desc = col.get_cells()[0].props.font_desc
        text = treeview.get_model()[path][tooltip_idx]
        text_size = TreeView._get_pango_text_size(text, font_desc)
        if text_size[0] > col.get_width() - TreeView._get_pango_text_size('...', font_desc)[0]:
            tooltip.set_markup(text)
            return True
        return False

    @staticmethod
    def _get_pango_text_size(text, font_description):
        pango_layout = Gtk.Label().get_layout()
        pango_layout.set_markup(text)
        pango_layout.set_font_description(font_description)
        return pango_layout.get_pixel_size()

    # ======  End of Tool Tip  =======


if __name__ == '__main__':
    class Window(Gtk.Window):
        def __init__(self):
            super(Window, self).__init__(title='ETV Test')
            self.set_default_size(200, 200)
            self.set_position(Gtk.WindowPosition.CENTER)

            s = Gtk.ListStore(str, str, str)
            for i, name in enumerate(['$5.01kjngfskljnKDLNFAKNSFDKNDA', '$4.99', '$12', '$5.00', '$1']):
                s.append(
                    [name, str(i), f'<span fgcolor="red">OOOOOOOOOOOOOOOOOOO</span>'])

            t = [{'title': 'Sortable', 'renderer': Gtk.CellRendererText, 'attributes': {'text': 0}, 'properties': {'ellipsize': 3}, 'fixed-width': 100, 'sort-column': 0},
                 {'title': 'Unsortable', 'renderer': Gtk.CellRendererText,
                     'attributes': {'text': 1}, 'fixed-width': 100},
                 {'title': 'Markup', 'renderer': Gtk.CellRendererText, 'attributes': {'markup': 2}, 'fixed-width': 50}]
            tv = TreeView(s, t, tooltip_func=TreeView.tooltip_ellisized_text)

            self.add(tv.asScrolledWindow())
            self.show_all()

    win = Window()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
