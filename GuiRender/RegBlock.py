import tkinter
import logging
from tkinter import ttk
from PIL import Image, ImageTk
import re


class EntryPopup(ttk.Entry):
    def __init__(self, parent, iid, text, control, **kw):
        ''' If relwidth is set, then width is ignored '''
        super().__init__(parent, **kw)
        self.tv = parent
        self.iid = iid
        self._control_handler = control

        self.insert(0, text)

        self['exportselection'] = False

        self.focus_force()
        self.bind("<Return>", self.on_return)
        self.bind("<Control-a>", self.select_all)
        self.bind("<Escape>", lambda *ignore: self.destroy())

    def on_return(self, event):
        values = list(self.tv.item(self.iid, "values"))
        # Write the value from the entry into corresponding address
        # Get the address information
        tpl = self.tv.parse_address(values[0])

        self._control_handler.write32_plus(tpl, self.get())
        # Read the corresponding address again
        values[-1] = hex(self._control_handler.read32_plus(tpl))

        self.tv.item(self.iid, values=values)
        self.destroy()

    def select_all(self, *ignore):
        ''' Set selection on the whole text '''
        self.selection_range(0, 'end')

        # returns 'break' to interrupt default key-bindings
        return 'break'


class ScrollbarFrame(ttk.Frame):
    """
    Extends class tkinter.Frame to support a scrollable Frame
    This class is independent from the widgets to be scrolled and
    can be used to replace a standard tkinter.Frame
    """
    def __init__(self, parent, **kwargs):
        ttk.Frame.__init__(self, parent, **kwargs)

        # The Scrollbar, layout to the right
        vsb = tkinter.Scrollbar(self, orient="vertical", width="16")
        vsb.pack(side="right", fill="y")

        # The Canvas which supports the Scrollbar Interface, layout to the left
        self.canvas = tkinter.Canvas(self, borderwidth=0, background="#ffffff",
                                     width=str(int(float(kwargs["width"])) - 24))
        self.canvas.pack(side="left", fill="both", expand=True)

        # Bind the Scrollbar to the self.canvas Scrollbar Interface
        self.canvas.configure(yscrollcommand=vsb.set)
        vsb.configure(command=self.canvas.yview)

        # The Frame to be scrolled, layout into the canvas
        # All widgets to be scrolled have to use this Frame as parent
        self.scrolled_frame = tkinter.Frame(self.canvas, background=self.canvas.cget('bg'),
                                            width=str(int(float(kwargs["width"])) - 24))
        self.canvas.create_window((0, 0), window=self.scrolled_frame, anchor="nw")

        # Configures the scrollregion of the Canvas dynamically
        self.scrolled_frame.bind("<Configure>", self.on_configure)

    def on_configure(self, event):
        """Set the scroll region to encompass the scrolled frame"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


class ModifyTree(ttk.Treeview):
    def __init__(self, master, control, **kwargs):
        self._top_columns = ("Address | Field", "Property", "Value")
        self._top_columns_width = ("250", "200", "100", "250")  # name, address, prop, value
        super(ModifyTree, self).__init__(master, columns=self._top_columns, **kwargs)

        self.bind("<Button-1>", self._one_click_modify)
        self.bind("<Double-1>", self._double_click_)
        # Pop up entry handler
        self._entryPopup = None
        # SWD class
        self._control_handler = control

        # Image
        self._image_tag = (ImageTk.PhotoImage(Image.open("./GuiRender/.image/.treeview/device.png").resize((20, 20), Image.ANTIALIAS)),
                           ImageTk.PhotoImage(Image.open("./GuiRender/.image/.treeview/register.png").resize((20, 20), Image.ANTIALIAS)),
                           ImageTk.PhotoImage(Image.open("./GuiRender/.image/.treeview/field.png").resize((20, 20), Image.ANTIALIAS))
                           )

        # Edit the heading
        self.heading("#0", text="Name", anchor="center")
        self.column("#0", width=self._top_columns_width[0], minwidth="25", anchor="center")

        self.heading(self._top_columns[0], text=self._top_columns[0], anchor="center")
        self.column(self._top_columns[0], width=self._top_columns_width[1], minwidth="25", anchor="center")

        self.heading(self._top_columns[1], text=self._top_columns[1], anchor="center")
        self.column(self._top_columns[1], width=self._top_columns_width[2], minwidth="25", anchor="center")

        self.heading(self._top_columns[2], text=self._top_columns[2], anchor="center")
        self.column(self._top_columns[2], width=self._top_columns_width[3], minwidth="25", anchor="center")

        # Tree root
        self._tree_root = None
        # Reserve the current tree item parent
        self._parent = ""
        # Current item iid
        self._cur_iid = 0
        # The depth of the level
        self._level = 0

        # re parse pattern
        self._pattern = re.compile(r"(?P<Address>0x[0-9a-fA-F]+)[\s\|]*(?P<Field0>[0-9]*):*(?P<Field1>[0-9]*)")

        # Registe the handler to control widget
        self._control_handler.modify_tree_register(self)

    def generate(self, mid_value, level):
        self._level = level
        self._tree_root = mid_value
        self._gen_level(self._tree_root)
        self._parent = ""
        self._level = 0

    def parse_address(self, address):
        # r"(?P<Address>0x[0-9a-fA-F]+)[\s\|]*(?P<Field0>[0-9]*):*(?P<Field1>[0-9]*)"
        rslt = self._pattern.match(address)
        addr = rslt.group("Address")
        field0 = rslt.group("Field0")
        field1 = rslt.group("Field1")
        logging.debug("The parse result: %s -> %s:%s" % (addr, field0, field1))
        return addr, field0, field1

    def _gen_level(self, root):
        for i in root:
            value = "NA"
            if self._level != 0:
                value = str(hex(self._control_handler.read32_plus(self.parse_address(i["Address"]))))
                # Trigger error return False
                if not value:
                    return
            self._cur_iid = self.insert(self._parent, "end", iid=None, text=i["Name"], image=self._image_tag[self._level], values=(i["Address"], i["Property"], value), tags=self._level)
            if i["Level"]:
                self._level += 1
                self._parent = self._cur_iid
                self._gen_level(i["Level"])
        self._parent = self.parent(self._parent)
        self._level -= 1

    def _one_click_modify(self, event):
        ''' Executed, when a row is one-clicked. Opens
        editable EntryPopup above the item's column, so it is possible
        to select text '''

        # close previous popups
        self._destroy_pop_up()

        # what row and column was clicked on
        rowid = self.identify_row(event.y)
        column = self.identify_column(event.x)
        if column != "#3" or not rowid:
            return
        tags = self.item(rowid, "tags")[0]
        logging.info("Click the row:%s, column:%s, tags:%s" % (rowid, column, tags))
        if tags == "0":
            return

        # get column position info
        x, y, width, height = self.bbox(rowid, column)
        logging.info("The location information --> x:%d, y:%d, width:%d, height:%d" % (x, y, width, height))

        # y-axis offset
        pady = height // 2

        # place Entry popup properly
        text = self.item(rowid, "values")

        self._entryPopup = EntryPopup(self, rowid, text[-1], control=self._control_handler, width=self._top_columns_width[-1], justify=tkinter.CENTER)
        self._entryPopup.place(x=x, y=y + pady, anchor=tkinter.W, width=self._top_columns_width[-1])

    def _double_click_(self, event):
        item = self.focus()
        if item:
            self.delete(item)
        return 'break'

    def _destroy_pop_up(self):
        if self._entryPopup:
            self._entryPopup.destroy()
            self._entryPopup = None


class DisplayTree(ttk.Treeview):
    def __init__(self, master, tree, modify_tree, control, **kwargs):
        self._top_columns = ("Address", "Field", "Property")
        self._top_columns_width = ("250", "200", "200", "150")
        super(DisplayTree, self).__init__(master, columns=self._top_columns, **kwargs)

        self.bind("<Double-1>", self._double_click)

        # Edit the heading
        self.heading("#0", text="Name", anchor="center")
        self.column("#0", width=self._top_columns_width[0], minwidth="25", anchor="center")

        self.heading(self._top_columns[0], text=self._top_columns[0], anchor="center")
        self.column(self._top_columns[0], width=self._top_columns_width[1], minwidth="25", anchor="center")

        self.heading(self._top_columns[1], text=self._top_columns[1], anchor="center")
        self.column(self._top_columns[1], width=self._top_columns_width[2], minwidth="25", anchor="center")

        self.heading(self._top_columns[2], text=self._top_columns[2], anchor="center")
        self.column(self._top_columns[2], width=self._top_columns_width[3], minwidth="25", anchor="center")

        # Image
        self._image_tag = (ImageTk.PhotoImage(Image.open("./GuiRender/.image/.treeview/device.png").resize((20, 20), Image.ANTIALIAS)),
                           ImageTk.PhotoImage(Image.open("./GuiRender/.image/.treeview/register.png").resize((20, 20), Image.ANTIALIAS)),
                           ImageTk.PhotoImage(Image.open("./GuiRender/.image/.treeview/field.png").resize((20, 20), Image.ANTIALIAS))
                           )

        # Tree root
        self._tree_root = tree
        # Reserve the current tree item parent
        self._parent = ""
        # Current item iid
        self._cur_iid = 0
        # The depth of the level
        self._level = 0
        # The address pointer
        self._address = 0
        # The modify tree handler
        self._modify_tree = modify_tree
        # Transmit middle value
        self._mid_value = []
        self._mid_value_pointer = self._mid_value
        # Get the control handler
        self._control_handler = control

        # Expand re
        self._find_indexs_pattern = re.compile(r"\[(?P<Number>[0-9]+)\]")
        self._locate_indexs_pattern = re.compile(r"<ARRAY_INDEX>")

        # Construct the TreeView
        for _sub in self._tree_root:
            if _sub:
                self._gen_level(_sub)

    def _gen_level(self, root):
        # In first level, the module level
        if self._level == 0:
            self._cur_iid = self.insert(self._parent, "end", iid=None, text=root["Module"], image=self._image_tag[self._level], values=(root["Address Start"], "", ""), tags=self._level)

            # Exist the children
            if root["Class"]:
                self._address = int(root["Address Start"], base=16)
                self._level += 1
                self._parent = self._cur_iid
                self._gen_level(root["Class"])
            else:
                # restore
                self._level = 0
                self._parent = ""
                self._address = 0
        # Level 1, 2 have another function to deal
        else:
            for i in root:
                # Collect the key in dictionary
                if 'Sub-Addr\n(Hex)' in i.keys():
                    sub_addr = int(i['Sub-Addr\n(Hex)'], base=16) + self._address
                else:
                    sub_addr = ""

                if 'Start\nBit' and 'End\nBit' in i.keys():
                    field = "%d:%d" % (int(i['Start\nBit']), int(i['End\nBit']))
                else:
                    field = ""

                if 'R/W\nProperty' in i.keys():
                    prop = i['R/W\nProperty']
                else:
                    prop = ""

                if self._level == 1:
                    level = self._level
                    parent = self._parent
                    address = self._address
                    if self._expand(i):
                        self._level = level
                        self._parent = parent
                        self._address = address
                        continue

                # Insert information into tree view
                self._cur_iid = self.insert(self._parent, "end", iid=None,
                                            text=i["Register\nName"], image=self._image_tag[self._level],
                                            values=(hex(sub_addr) if sub_addr else sub_addr, field, prop),
                                            tags=self._level)

                # Exist the children
                if i["Level"]:
                    self._parent = self._cur_iid
                    self._level += 1
                    # Recursive into the next level
                    self._gen_level(i["Level"])
            # Reserve parameter
            # The current _parent value point to the current level, so use the parent function
            # to get the current parent iid
            self._parent = self.parent(self._parent)
            self._level -= 1

    def _expand(self, i):
        rslt = self._find_indexs_pattern.search(i["Register\nName"])

        # Search the indexs
        if rslt:
            # Collect the key in dictionary
            if 'Sub-Addr\n(Hex)' in i.keys():
                sub_addr = int(i['Sub-Addr\n(Hex)'], base=16) + self._address
            else:
                sub_addr = ""

            if 'Start\nBit' and 'End\nBit' in i.keys():
                field = "%d:%d" % (int(i['Start\nBit']), int(i['End\nBit']))
            else:
                field = ""

            if 'R/W\nProperty' in i.keys():
                prop = i['R/W\nProperty']
            else:
                prop = ""

            for num in range(int(rslt.group("Number"))):

                name = i["Register\nName"][0: rslt.span()[0]] + str(num)

                self._cur_iid = self.insert(self._parent, "end", iid=None,
                                            text=name,
                                            image=self._image_tag[self._level],
                                            values=(hex(sub_addr + 4*num) if sub_addr else sub_addr, field, prop),
                                            tags=self._level
                                            )

                # Exist the children
                if i["Level"]:
                    self._parent = self._cur_iid
                    self._level += 1
                    # Recursive into the next level
                    self._subexpand(i["Level"], num)

            self._parent = self.parent(self._parent)
            self._level -= 1

            return True

        else:
            return False

    def _subexpand(self, root, num):
        for i in root:
            # Collect the key in dictionary
            if 'Sub-Addr\n(Hex)' in i.keys():
                sub_addr = int(i['Sub-Addr\n(Hex)'], base=16) + self._address
            else:
                sub_addr = ""

            if 'Start\nBit' and 'End\nBit' in i.keys():
                field = "%d:%d" % (int(i['Start\nBit']), int(i['End\nBit']))
            else:
                field = ""

            if 'R/W\nProperty' in i.keys():
                prop = i['R/W\nProperty']
            else:
                prop = ""

            name = self._locate_indexs_pattern.sub(str(num), i["Register\nName"])

            # Insert information into tree view
            self._cur_iid = self.insert(self._parent, "end", iid=None,
                                        text=name, image=self._image_tag[self._level],
                                        values=(hex(sub_addr) if sub_addr else sub_addr, field, prop),
                                        tags=self._level)

        self._parent = self.parent(self._parent)
        self._level -= 1

    def _item_recursive(self, items):
        if not items:
            return

        for item in items:
            info = self.item(item)
            if not info["values"][0]:
                address = "%s | %s" % (self.item(self.parent(item))["values"][0], info["values"][1])
            else:
                address = info["values"][0]

            if not info["values"][-1]:
                prop = "NA"
            else:
                prop = info["values"][-1]

            name = info["text"]

            pointer_parent = self._mid_value_pointer
            cur_pointer = {"Name": name, "Address": address, "Property": prop, "Level": []}
            self._mid_value_pointer.append(cur_pointer)
            # Reserve the parent pointer
            self._mid_value_pointer = cur_pointer["Level"]
            # Recursive the chlidren tree
            self._item_recursive(self.get_children(item))
            # Restore the pointer
            self._mid_value_pointer = pointer_parent

    def _double_click(self, event):
        # Check if SWD connected
        if not self._control_handler.connected():
            return 'break'

        # Empty middle transmit value
        self._mid_value = []
        self._mid_value_pointer = self._mid_value
        # Remove the first row click
        item = self.focus()
        if not item:
            return 'break'

        self._item_recursive((item, ))

        # Deliver the display-tree information to modify-tree
        self._modify_tree.generate(self._mid_value, self.item(item)["tags"][0])

        return 'break'


class FlatButton(tkinter.Button):
    def __init__(self, master, **kwargs):
        self._hover_color = "#4c5052"
        self._default_bg_color = "#3c3f41"
        super(FlatButton, self).__init__(master, relief=tkinter.FLAT, activebackground="#4c5052", bg="#3c3f41", highlightcolor="#4c5052", takefocus=True, **kwargs)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_level)

    def _on_enter(self, event):
        self.configure(bg=self._hover_color)

    def _on_level(self, event):
        self.configure(bg=self._default_bg_color)


class DarkLabel(tkinter.Label):
    def __init__(self, master, **kwargs):
        super(DarkLabel, self).__init__(master, relief=tkinter.FLAT, bg="#3c3f41", **kwargs)


class AutoCheck(tkinter.Checkbutton):
    def __init__(self, master, control, **kwargs):
        self._default_font_color = "#a7a7a7"
        self._inner_bg_color = "#43494a"
        self._default_bg_color = "#3c3f41"
        self.autovar = tkinter.StringVar()
        super(AutoCheck, self).__init__(master, bg=self._default_bg_color, fg=self._default_font_color,
                                        selectcolor=self._inner_bg_color,
                                        activebackground=self._default_bg_color,
                                        variable=self.autovar,
                                        onvalue="auto",
                                        offvalue="bluntness",
                                        command=self._click_callback,
                                        **kwargs)
        self.deselect()
        self._control_handler = control
        # Register itself to control module
        self._control_handler.check_button_register(self)

    def _click_callback(self):
        if self.autovar.get() == "auto":
            self._control_handler.open_timer()
        elif self.autovar.get() == "bluntness":
            self._control_handler.close_timer()
        else:
            logging.error("Undefine value")


class StageButton(ttk.Frame):
    def __init__(self, master, control, **kwargs):

        super(StageButton, self).__init__(master, **kwargs)

        self._control_handler = control

        # Open image
        self._open_image = ImageTk.PhotoImage(Image.open("./GuiRender/.image/.connect/play.png").resize((16, 16), Image.ANTIALIAS))
        self._open_dark_image = ImageTk.PhotoImage(
            Image.open("./GuiRender/.image/.connect/play-dark.png").resize((16, 16), Image.ANTIALIAS))
        self._connect_image = ImageTk.PhotoImage(
            Image.open("./GuiRender/.image/.connect/connect.png").resize((16, 16), Image.ANTIALIAS))

        # Stop image
        self._stop_image = ImageTk.PhotoImage(Image.open("./GuiRender/.image/.disconnect/stop.png").resize((16, 16), Image.ANTIALIAS))
        self._stop_dark_image = ImageTk.PhotoImage(
            Image.open("./GuiRender/.image/.disconnect/stop-dark.png").resize((16, 16), Image.ANTIALIAS))
        self._disconnect_image = ImageTk.PhotoImage(
            Image.open("./GuiRender/.image/.disconnect/disconnect.png").resize((16, 16), Image.ANTIALIAS))

        # Refresh image
        self._refresh_image = ImageTk.PhotoImage(Image.open("./GuiRender/.image/.refresh/refresh.png").resize((16, 16), Image.ANTIALIAS))
        self._refresh_dark_image = ImageTk.PhotoImage(
            Image.open("./GuiRender/.image/.refresh/refresh-dark.png").resize((16, 16), Image.ANTIALIAS))

        # Control frame
        self._control_button_frame = tkinter.Frame(self, bg="#3c3f41")
        self._control_button_frame.pack(side="right", padx="4", fill="x")

        # Connect button
        self._connect_button = FlatButton(self._control_button_frame, image=self._open_image, command=self._connect)
        self._connect_button.grid(row=0, column=0, sticky="nswe", padx="4", pady="2")

        # Stop button
        self._disconnect_button = FlatButton(self._control_button_frame, image=self._stop_dark_image, command=self._disconnect)
        self._disconnect_button.grid(row=0, column=1, sticky="nswe", padx="4", pady="2")

        # Separator
        ttk.Separator(self._control_button_frame, orient=tkinter.VERTICAL).grid(row=0, column=2, sticky="ns", pady="4")

        # Refresh button
        self._refresh_button = FlatButton(self._control_button_frame, image=self._refresh_dark_image, command=self._refresh)
        self._refresh_button.grid(row=0, column=3, sticky="nswe", padx="4", pady="2")

        self._auto_check_button = AutoCheck(self._control_button_frame, self._control_handler)
        self._auto_check_button.grid(row=0, column=4, sticky="nswe", padx="4", pady="2")

        ttk.Separator(self._control_button_frame, orient=tkinter.VERTICAL).grid(row=0, column=5, sticky="ns", pady="4")

        # Stage label
        self._stage_label = DarkLabel(self._control_button_frame, image=self._disconnect_image)
        self._stage_label.grid(row=0, column=6, sticky="nswe", padx="4", pady="2")

    def _connect(self):
        if self._control_handler.connect():
            self._connect_button.configure(image=self._open_dark_image)
            self._refresh_button.configure(image=self._refresh_image)
            self._disconnect_button.configure(image=self._stop_image)
            self._stage_label.configure(image=self._connect_image)

    def _refresh(self):
        self._control_handler.tree_refresh()

    def _disconnect(self):
        if self._control_handler.disconnect():
            self._connect_button.configure(image=self._open_image)
            self._refresh_button.configure(image=self._refresh_dark_image)
            self._disconnect_button.configure(image=self._stop_dark_image)
            self._stage_label.configure(image=self._disconnect_image)


class DscpFrame(ttk.Frame):
    def __init__(self, master, control, **kwargs):
        super(DscpFrame, self).__init__(master, **kwargs)

        self._control_handler = control


class RegTree(ttk.Frame):
    # Insert a tree
    def __init__(self, master, control, _tree=None, **kwargs):  # -------------------level0
        self.REGBLOCK_WIDTH = 1600
        self.REGBLOCK_HEIGHT = 800
        self.REGBLOCK_BUTTON_HEIGHT = 40
        self.REGBLOCK_DSCP_HEIGHT = 100
        # Base Frame -----------------level 0
        ttk.Frame.__init__(self, master, width=str(self.REGBLOCK_WIDTH), height=str(self.REGBLOCK_HEIGHT), **kwargs)
        self.grid_propagate(0)

        # Create frame tree and modify tree -----------------level 1
        self._tree_frame = ttk.Frame(self, width=str(self.REGBLOCK_WIDTH/2), height=str(self.REGBLOCK_HEIGHT))
        self._modify_frame = ttk.Frame(self, width=str(self.REGBLOCK_WIDTH/2), height=str(self.REGBLOCK_HEIGHT))
        self._tree_frame.grid_propagate(0)
        self._modify_frame.grid_propagate(0)
        # Place the block into corresponding grid -----------------level 1
        self._tree_frame.pack(fill="y", expand=True, side=tkinter.LEFT)
        self._modify_frame.pack(fill="y", expand=True, side=tkinter.RIGHT)
        # Create stuff into frame -----------------level 2
        self._stage_button_frame = StageButton(self._modify_frame, control, width=str(self.REGBLOCK_WIDTH / 2), height=str(self.REGBLOCK_BUTTON_HEIGHT))
        self._stage_button_frame.grid_propagate(0)

        self._modify_tree_vessel_frame = ttk.Frame(self._modify_frame, width=str(self.REGBLOCK_WIDTH / 2), height=str(self.REGBLOCK_HEIGHT - self.REGBLOCK_BUTTON_HEIGHT - self.REGBLOCK_DSCP_HEIGHT))
        self._modify_tree_vessel_frame.grid_propagate(0)

        self._description_frame = DscpFrame(self._modify_frame, control, width=str(self.REGBLOCK_WIDTH / 2),
                                            height=str(self.REGBLOCK_DSCP_HEIGHT))
        self._description_frame.grid_propagate(0)

        self._stage_button_frame.pack(side=tkinter.TOP, fill="x")
        self._modify_tree_vessel_frame.pack(fill="both", expand=True)
        self._description_frame.pack(side=tkinter.BOTTOM, fill="x")

        # Insert tree into frame -----------------level 3
        self._modify_tree = ModifyTree(self._modify_tree_vessel_frame, control)
        self._display_tree = DisplayTree(self._tree_frame, _tree, self._modify_tree, control)

        self._modify_tree.pack(fill="both", expand=True)
        self._display_tree.pack(fill="both", expand=True)


if __name__ == "__main__":
    pass
