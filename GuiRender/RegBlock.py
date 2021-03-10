import random
import tkinter
import os
from tkinter import ttk
from PIL import Image, ImageTk


class RegTree(ttk.Frame):
    # Insert a tree
    def __init__(self, master, _tree=None):  # -------------------level0
        self._columns_seq = ("Address", "Field", "Property")
        ttk.Frame.__init__(self, master, width=800, height=800)

        # Configure master frame grid -----------------------level0
        tkinter.Grid.columnconfigure(self, 0, weight=1)
        tkinter.Grid.columnconfigure(self, 1, weight=1)
        tkinter.Grid.rowconfigure(self, 0, weight=1)

        # Create frame tree and modify tree -----------------level 1
        self._tree_frame_label = ttk.LabelFrame(self, text="Device & Register Tree", width=400, height=800)
        self._modify_frame_label = ttk.LabelFrame(self, text="Block Modify Frame", width=400, height=800)
        # Place the block into corresponding grid -----------------level 1
        self._tree_frame_label.grid(column=0, row=0, sticky="nsew")
        self._modify_frame_label.grid(column=1, row=0, sticky="nsew")
        # Configure master frame grid -----------------level 1
        # Left frame -----------------level 1
        tkinter.Grid.columnconfigure(self._tree_frame_label, 0, weight=1)
        tkinter.Grid.rowconfigure(self._tree_frame_label, 0, weight=1)
        # Right frame -----------------level 1
        tkinter.Grid.columnconfigure(self._modify_frame_label, 0, weight=1)
        # tkinter.Grid.rowconfigure(self._modify_frame_label, 0, weight=1)

        self._generator = RegBlockGen(self._modify_frame_label)

        # create view tree -----------------------level2
        self._tree = ttk.Treeview(self._tree_frame_label, columns=self._columns_seq, padding=1)
        self._tree.grid(column=0, row=0, sticky="nsew")

        self._tree.column("#0", width=150, minwidth=25, anchor="center")
        self._tree.column("Address", width=150, minwidth=25, anchor="center")
        self._tree.column("Field", width=150, minwidth=25, anchor="center")
        self._tree.column("Property", width=50, minwidth=25, anchor="center")
        self._tree.bind("<Double-1>", self._double_click)
        self._device_full_image = ImageTk.PhotoImage(Image.open("./GuiRender/device.png").
                                                     resize((20, 20), Image.ANTIALIAS))
        self._register_full_image = ImageTk.PhotoImage(Image.open("./GuiRender/register.png").
                                                       resize((20, 20), Image.ANTIALIAS))
        self._field_full_image = ImageTk.PhotoImage(Image.open("./GuiRender/field.png").
                                                    resize((20, 20), Image.ANTIALIAS))

        self._root = _tree
        self._level = 0
        self._parent = [""]
        self._address = 0

        self._tree.heading("#0", text="Name", anchor="center")
        for item in self._columns_seq:
            self._tree.heading(item, text=item.title())

        for item in self._root:
            self._gen_level(item)

    # The tree preorder traversal
    def _gen_level(self, root):
        # root not an empty list
        if root:
            if self._level == 0:
                self._tree.insert(self._parent[self._level], self._level, iid=root["Module"],
                                  text=root["Module"],
                                  image=self._device_full_image,
                                  values=(root["Address Start"], "", ""))
                try:
                    self._parent[self._level + 1] = root["Module"]
                except IndexError:
                    self._parent.append(root["Module"])

                self._address = int(root["Address Start"], base=16)
                self._level += 1
                if root["Class"]:
                    self._gen_level(root["Class"])
                else:
                    # restore
                    self._level = 0
                    self._parent = [""]
                    self._address = 0
            else:
                for i in root:
                    # key in dictionary
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

                    _image = None
                    if self._level == 1:
                        _image = self._register_full_image
                    elif self._level == 2:
                        _image = self._field_full_image
                    else:
                        print("Error")

                    # insert information into tree view
                    try:
                        self._tree.insert(self._parent[self._level], self._level,
                                          iid=str(self._parent[self._level] + i["Register\nName"]),
                                          text=i["Register\nName"],
                                          image=_image,
                                          values=(hex(sub_addr) if sub_addr else sub_addr, field, prop))
                    except tkinter.TclError:
                        self._random_num = random.randint(0, 99999999)
                        self._tree.insert(self._parent[self._level], self._level,
                                          iid=str(self._parent[self._level] + i["Register\nName"]
                                                  + str(self._random_num)),
                                          text=i["Register\nName"],
                                          image=_image,
                                          values=(hex(sub_addr) if sub_addr else sub_addr, field, prop))

                    if i["Level"]:
                        # push or modify the stack
                        try:
                            if not i["Register\nName"]:  # register name empty
                                self._parent[self._level + 1] = str(self._parent[self._level] + i["Register\nName"]
                                                                    + str(self._random_num))
                            else:
                                self._parent[self._level + 1] = str(self._parent[self._level] + i["Register\nName"])
                        except IndexError:
                            if not i["Register\nName"]:  # register name empty
                                self._parent.append(str(self._parent[self._level] + i["Register\nName"])
                                                    + str(self._random_num))
                            else:
                                self._parent.append(str(self._parent[self._level] + i["Register\nName"]))

                        self._level += 1
                        self._gen_level(i["Level"])
                    else:
                        # break current loop
                        continue
                self._level -= 1
        else:
            return True

    def _expand(self):
        pass

    def _double_click(self, event):
        item = self._tree.focus()
        output = self._tree.item(item)
        print(output)
        # Empty string
        if not output["values"][0]:
            address = "%s | %s" % (self._tree.item(self._tree.parent(item))["values"][0], output["values"][1])
        else:
            address = output["values"][0]
        self._generator.generate([output["text"], address, output["values"][-1], output["image"][-1]])
        return 'break'


class RegBlockGen:
    def __init__(self, master):
        self._row = 0
        self._master = master
        self._header = ttk.Frame(self._master)

    def generate(self, para):
        RegBlock(self._master, para).grid(column=0, row=self._row, sticky="nsew")
        self._row += 1

    def _read_value(self):
        pass


# Create 5 lable: "Name", "Address/Field", "Property", "Value", empty for operate
class RegBlock(ttk.Frame):
    def __init__(self, master, para):  # name, af, prop, image
        ttk.Frame.__init__(self, master)
        self._device_full_image = ImageTk.PhotoImage(Image.open("./GuiRender/device.png").
                                                     resize((20, 20), Image.ANTIALIAS))
        self._register_full_image = ImageTk.PhotoImage(Image.open("./GuiRender/register.png").
                                                       resize((20, 20), Image.ANTIALIAS))
        self._field_full_image = ImageTk.PhotoImage(Image.open("./GuiRender/field.png").
                                                    resize((20, 20), Image.ANTIALIAS))
        self._image_mapping = {"pyimage1": self._device_full_image, "pyimage2": self._register_full_image,
                               "pyimage3": self._field_full_image}
        self.rowconfigure(0, weight=1)

        # Name label
        self._name_label = ttk.Label(self, text=para[0], borderwidth=5, relief=tkinter.GROOVE, width=20,
                                     compound="left", image=self._image_mapping[para[3]])
        self._name_label.grid(row=0, column=0, sticky="nwse")
        self.columnconfigure(0, weight=40)

        # Address & Field label
        self._address_field_label = ttk.Label(self, text=para[1], borderwidth=5, relief=tkinter.GROOVE, width=20)
        self._address_field_label.grid(row=0, column=1, sticky="nwse")
        self.columnconfigure(1, weight=40)

        # Property label
        self._property_label = ttk.Label(self, text=para[2], borderwidth=5, relief=tkinter.GROOVE, width=5)
        self._property_label.grid(row=0, column=2, sticky="nwse")
        self.columnconfigure(2, weight=20)

        # Input entry
        self._input_entry = ttk.Entry(self, width=20)
        self._input_entry.grid(row=0, column=3, sticky="nwse")
        self._input_entry.bind("<Return>", self._regblock_return)
        self.columnconfigure(3, weight=40)

        # Write button
        self._write_button = ttk.Button(self, text="Write", command=self._regblock_write, width=10)
        self._write_button.grid(row=0, column=4, sticky="nwse")
        self.columnconfigure(4, weight=20)

        # Read button
        self._read_button = ttk.Button(self, text="Read", command=self._regblock_read, width=10)
        self._read_button.grid(row=0, column=5, sticky="nwse")
        self.columnconfigure(5, weight=20)

        # Delete button
        self._delete_button = ttk.Button(self, text="Delete", command=self._regblock_delete, width=10)
        self._delete_button.grid(row=0, column=6, sticky="nwse")
        self.columnconfigure(6, weight=20)

    def _regblock_return(self, event):
        self._regblock_write()

    def _regblock_write(self):
        print("write")

    def _regblock_read(self):
        print("read")

    def _regblock_delete(self):
        print("delete")
        self.grid_forget()


if __name__ == "__main__":
    _columns_seq = ("Name", "Address", "Field", "Property")
    root = tkinter.Tk()
    # a = ttk.LabelFrame(root, text="HelloWorld")
    # a.pack()
    # ttk.Button(a, text="click").pack()
    tkinter.Grid.columnconfigure(root, 0, weight=1)
    # tkinter.Grid.rowconfigure(root, 0, weight=1)
    RegBlock(root, _columns_seq).grid(column=0, row=0, sticky="nsew")
    # tree = ttk.Treeview(root, columns=_columns_seq)
    # tree.insert("", 0, "Level1", text="Level1")
    # tree.insert("Level1", 1, "Level2", text="Level2")
    # tree.insert("Level2", 2, "Level3", text="Level3\nwode")
    # tree.grid()
    #
    # tree = ttk.Treeview(root, columns=_columns_seq)
    # tree.insert("", 0, "Level1-1", text="Level1")
    # tree.insert("Level1", 1, "Level2-1", text="Level2")
    # tree.insert("Level2", 2, "Level3-1", text="Level3\nwode")
    # tree.grid()

    root.mainloop()
