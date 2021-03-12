import tkinter
import logging
from tkinter import ttk
from PIL import Image, ImageTk
from SWDJlink import SelfSWD
import re

REGBLOCK_WIDTH = 1600
REGBLOCK_HEIGHT = 800


class EntryPopup(ttk.Entry):
    def __init__(self, parent, iid, text, **kw):
        ''' If relwidth is set, then width is ignored '''
        super().__init__(parent, **kw)
        self.tv = parent
        self.iid = iid

        self.insert(0, text)

        # self['state'] = 'readonly'
        # self['readonlybackground'] = 'white'
        # self['selectbackground'] = '#1BA1E2'

        self['exportselection'] = False

        self.focus_force()
        self.bind("<Return>", self.on_return)
        self.bind("<Control-a>", self.select_all)
        self.bind("<Escape>", lambda *ignore: self.destroy())

    def on_return(self, event):
        values = list(self.tv.item(self.iid, "values"))
        # Write the value from the entry into corresponding address
        # Get the address information
        tpl = self.tv._parse_address(values[0])
        self.tv._SWD.write32_plus(tpl, self.get())
        # Read the corresponding address again
        values[-1] = hex(self.tv._SWD.read32_plus(tpl))

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
    def __init__(self, master, **kwargs):
        self._top_columns = ("Address | Field", "Property", "Value")
        self._top_columns_width = ("250", "200", "100", "250")  # name, address, prop, value
        super(ModifyTree, self).__init__(master, columns=self._top_columns, **kwargs)

        self.bind("<Button-1>", self._one_click_modify)
        self.bind("<Double-1>", self._double_click_)
        # Pop up entry handler
        self._entryPopup = None
        # SWD class
        try:
            self._SWD = SelfSWD()
        except:
            # Can't open SWD
            self._SWD = None

        # Image
        self._image_tag = (ImageTk.PhotoImage(Image.open("./GuiRender/device.png").resize((20, 20), Image.ANTIALIAS)),
                           ImageTk.PhotoImage(Image.open("./GuiRender/register.png").resize((20, 20), Image.ANTIALIAS)),
                           ImageTk.PhotoImage(Image.open("./GuiRender/field.png").resize((20, 20), Image.ANTIALIAS))
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

    def generate(self, mid_value, level):
        self._level = level
        self._tree_root = mid_value
        self._gen_level(self._tree_root)
        self._parent = ""
        self._level = 0

    def _parse_address(self, address):
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
                value = str(hex(self._SWD.read32_plus(self._parse_address(i["Address"]))))
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

        self._entryPopup = EntryPopup(self, rowid, text[-1], width=self._top_columns_width[-1], justify=tkinter.CENTER)
        self._entryPopup.place(x=x, y=y + pady, anchor=tkinter.W, width=self._top_columns_width[-1])

    def _double_click_(self, event):
        return 'break'

    def _destroy_pop_up(self):
        if self._entryPopup:
            self._entryPopup.destroy()
            self._entryPopup = None


class DisplayTree(ttk.Treeview):
    def __init__(self, master, tree, modify_tree, **kwargs):
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
        self._image_tag = (ImageTk.PhotoImage(Image.open("./GuiRender/device.png").resize((20, 20), Image.ANTIALIAS)),
                           ImageTk.PhotoImage(Image.open("./GuiRender/register.png").resize((20, 20), Image.ANTIALIAS)),
                           ImageTk.PhotoImage(Image.open("./GuiRender/field.png").resize((20, 20), Image.ANTIALIAS))
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
                self._parent = [""]
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


class RegTree(ttk.Frame):
    # Insert a tree
    def __init__(self, master, _tree=None, **kwargs):  # -------------------level0
        # self._columns_seq = ("Address", "Field", "Property")
        ttk.Frame.__init__(self, master, width=str(REGBLOCK_WIDTH), height=str(REGBLOCK_HEIGHT), **kwargs)
        self.grid_propagate(0)

        # Create frame tree and modify tree -----------------level 1
        self._tree_frame = ttk.Frame(self, width=str(REGBLOCK_WIDTH/2), height=str(REGBLOCK_HEIGHT))
        self._modify_frame = ttk.Frame(self, width=str(REGBLOCK_WIDTH/2), height=str(REGBLOCK_HEIGHT))
        self._tree_frame.grid_propagate(0)
        self._modify_frame.grid_propagate(0)
        # Place the block into corresponding grid -----------------level 1
        self._tree_frame.grid(column=0, row=0, sticky="nsew")
        self._modify_frame.grid(column=1, row=0, sticky="nsew")
        self._tree_frame.rowconfigure(0, weight=1)
        self._modify_frame.rowconfigure(0, weight=1)
        # Configure master frame grid -----------------level 1
        self._modify_tree = ModifyTree(self._modify_frame)
        self._display_tree = DisplayTree(self._tree_frame, _tree, self._modify_tree)

        self._modify_tree.grid(column=0, row=0, sticky="nsew")
        self._display_tree.grid(column=0, row=0, sticky="nsew")
        # self._generator = RegBlockGen(self._modify_frame_label)

        # create view tree -----------------------level2
        # self._tree = ttk.Treeview(self._tree_frame_label, columns=self._columns_seq)
        # self._tree.grid(column=0, row=0, sticky="nsew")
        # self._tree_frame_label.rowconfigure(0, weight=1)

        # self._tree.column("#0", width="250", minwidth="25", anchor="center")
        # self._tree.column("Address", width="200", minwidth="25", anchor="center")
        # self._tree.column("Field", width="200", minwidth="25", anchor="center")
        # self._tree.column("Property", width="150", minwidth="25", anchor="center")
        # self._tree.bind("<Double-1>", self._double_click)
        # self._device_full_image = ImageTk.PhotoImage(Image.open("./GuiRender/device.png").
        #                                              resize((20, 20), Image.ANTIALIAS))
        # self._register_full_image = ImageTk.PhotoImage(Image.open("./GuiRender/register.png").
        #                                                resize((20, 20), Image.ANTIALIAS))
        # self._field_full_image = ImageTk.PhotoImage(Image.open("./GuiRender/field.png").
        #                                             resize((20, 20), Image.ANTIALIAS))

        # self._root = _tree
        # self._level = 0
        # self._parent = [""]
        # self._address = 0

        # self._tree.heading("#0", text="Name", anchor="center")
        # for item in self._columns_seq:
        #     self._tree.heading(item, text=item.title())

        # for item in self._root:
        #     self._gen_level(item)

    # The tree preorder traversal
    # def _gen_level(self, root):
    #     # root not an empty list
    #     if root:
    #         if self._level == 0:
    #             self._tree.insert(self._parent[self._level], self._level, iid=root["Module"],
    #                               text=root["Module"],
    #                               image=self._device_full_image,
    #                               values=(root["Address Start"], "", ""))
    #             try:
    #                 self._parent[self._level + 1] = root["Module"]
    #             except IndexError:
    #                 self._parent.append(root["Module"])
    #
    #             self._address = int(root["Address Start"], base=16)
    #             self._level += 1
    #             if root["Class"]:
    #                 self._gen_level(root["Class"])
    #             else:
    #                 # restore
    #                 self._level = 0
    #                 self._parent = [""]
    #                 self._address = 0
    #         else:
    #             for i in root:
    #                 # key in dictionary
    #                 if 'Sub-Addr\n(Hex)' in i.keys():
    #                     sub_addr = int(i['Sub-Addr\n(Hex)'], base=16) + self._address
    #                 else:
    #                     sub_addr = ""
    #
    #                 if 'Start\nBit' and 'End\nBit' in i.keys():
    #                     field = "%d:%d" % (int(i['Start\nBit']), int(i['End\nBit']))
    #                 else:
    #                     field = ""
    #
    #                 if 'R/W\nProperty' in i.keys():
    #                     prop = i['R/W\nProperty']
    #                 else:
    #                     prop = ""
    #
    #                 _image = None
    #                 if self._level == 1:
    #                     _image = self._register_full_image
    #                 elif self._level == 2:
    #                     _image = self._field_full_image
    #                 else:
    #                     logging.info("Error")
    #
    #                 # insert information into tree view
    #                 try:
    #                     self._tree.insert(self._parent[self._level], "end",
    #                                       iid=str(self._parent[self._level] + i["Register\nName"]),
    #                                       text=i["Register\nName"],
    #                                       image=_image,
    #                                       values=(hex(sub_addr) if sub_addr else sub_addr, field, prop))
    #                 except tkinter.TclError:
    #                     self._random_num = random.randint(0, 99999999)
    #                     self._tree.insert(self._parent[self._level], "end",
    #                                       iid=str(self._parent[self._level] + i["Register\nName"]
    #                                               + str(self._random_num)),
    #                                       text=i["Register\nName"],
    #                                       image=_image,
    #                                       values=(hex(sub_addr) if sub_addr else sub_addr, field, prop))
    #
    #                 if i["Level"]:
    #                     # push or modify the stack
    #                     try:
    #                         if not i["Register\nName"]:  # register name empty
    #                             self._parent[self._level + 1] = str(self._parent[self._level] + i["Register\nName"]
    #                                                                 + str(self._random_num))
    #                         else:
    #                             self._parent[self._level + 1] = str(self._parent[self._level] + i["Register\nName"])
    #                     except IndexError:
    #                         if not i["Register\nName"]:  # register name empty
    #                             self._parent.append(str(self._parent[self._level] + i["Register\nName"])
    #                                                 + str(self._random_num))
    #                         else:
    #                             self._parent.append(str(self._parent[self._level] + i["Register\nName"]))
    #
    #                     self._level += 1
    #                     self._gen_level(i["Level"])
    #                 else:
    #                     # break current loop
    #                     continue
    #             self._level -= 1
    #     else:
    #         return True
    #
    # def _expand(self):
    #     pass
    #
    # def _double_click(self, event):
    #     # Remove the first row click
    #     item = self._tree.focus()
    #     if not item:
    #         return 'break'
    #     output = self._tree.item(item)
    #     logging.info(output)
    #     # Empty string
    #     if not output["values"][0]:
    #         address = "%s | %s" % (self._tree.item(self._tree.parent(item))["values"][0], output["values"][1])
    #     else:
    #         address = output["values"][0]
    #
    #     if not output["values"][-1]:
    #         prop = "NA"
    #     else:
    #         prop = output["values"][-1]
    #     self._generator.generate([output["text"], address, prop, output["image"][-1]])
    #     return 'break'


# class RegBlockGen:
#     def __init__(self, master):
#         self._row = 0
#         self._master = master
#         self._header = ttk.Frame(self._master)
#
#     def generate(self, para):
#         RegBlock(self._master, para).grid(column=0, row=self._row, sticky="nsew")
#         self._row += 1
#
#     def _read_value(self):
#         pass


# # Create 5 lable: "Name", "Address/Field", "Property", "Value", empty for operate
# class RegBlock(ttk.Frame):
#
#     # MY_SWD = SelfSWD()
#
#     def __init__(self, master, para):  # name, af, prop, image
#         ttk.Frame.__init__(self, master)
#         self._device_full_image = ImageTk.PhotoImage(Image.open("./GuiRender/device.png").
#                                                      resize((20, 20), Image.ANTIALIAS))
#         self._register_full_image = ImageTk.PhotoImage(Image.open("./GuiRender/register.png").
#                                                        resize((20, 20), Image.ANTIALIAS))
#         self._field_full_image = ImageTk.PhotoImage(Image.open("./GuiRender/field.png").
#                                                     resize((20, 20), Image.ANTIALIAS))
#         self._image_mapping = {"pyimage1": self._device_full_image, "pyimage2": self._register_full_image,
#                                "pyimage3": self._field_full_image}
#
#         # Name label
#         self._name_label = ttk.Label(self, text=para[0], borderwidth=5, relief=tkinter.GROOVE, width="20",
#                                      compound="left", image=self._image_mapping[para[3]])
#         self._name_label.grid(row=0, column=0, sticky="nwse")
#
#         # Address & Field label
#         self._address_field_label = ttk.Label(self, text=para[1], borderwidth=5, relief=tkinter.GROOVE, width="20")
#         self._address_field_label.grid(row=0, column=1, sticky="nwse")
#
#         # Property label
#         self._property_label = ttk.Label(self, text=para[2], borderwidth=5, relief=tkinter.GROOVE, width="6")
#         self._property_label.grid(row=0, column=2, sticky="nwse")
#
#         # Input entry
#         self._input_entry = ttk.Entry(self, width="25")
#         self._input_entry.grid(row=0, column=3, sticky="nwse")
#         self._input_entry.bind("<Return>", self._regblock_return)
#
#         # Write button
#         self._write_button = ttk.Button(self, text="Write", command=self._regblock_write, width="10")
#         self._write_button.grid(row=0, column=4, sticky="nwse")
#
#         # Read button
#         self._read_button = ttk.Button(self, text="Read", command=self._regblock_read, width="10")
#         self._read_button.grid(row=0, column=5, sticky="nwse")
#
#         # Delete button
#         self._delete_button = ttk.Button(self, text="Delete", command=self._regblock_delete, width="10")
#         self._delete_button.grid(row=0, column=6, sticky="nwse")
#
#     def _regblock_return(self, event):
#         self._regblock_write()
#
#     def _regblock_write(self):
#         logging.info("write")
#
#     def _regblock_read(self):
#         addr = int(re.sub(r"\|.*", "", self._address_field_label.cget("text")).strip(), base=16)
#         value = RegBlock.MY_SWD.read32(addr)
#         logging.info("Read address: %s --> %s" % (str(hex(addr)), str(hex(value[-1]))))
#         self._input_entry.delete(first=0, last=tkinter.END)
#         self._input_entry.insert(0, hex(value[-1]))
#
#     def _regblock_delete(self):
#         logging.info("delete")
#         self.grid_forget()


if __name__ == "__main__":
    pass
