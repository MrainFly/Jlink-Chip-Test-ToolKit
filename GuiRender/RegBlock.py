import random
import tkinter
import os
from tkinter import ttk
from PIL import Image, ImageTk


class RegTree(ttk.Frame):
    # Insert a tree
    def __init__(self, master, _tree=None):
        self._columns_seq = ("Address", "Field", "Property")
        ttk.Frame.__init__(self, master)

        # create view tree
        self._tree = ttk.Treeview(self, columns=self._columns_seq, padding=1)

        self._tree.column("#0", width=150, minwidth=25, anchor="center")
        self._tree.column("Address", width=150, minwidth=25, anchor="center")
        self._tree.column("Field", width=150, minwidth=25, anchor="center")
        self._tree.column("Property", width=50, minwidth=25, anchor="center")

        tkinter.Grid.columnconfigure(self, 0, weight=1)
        tkinter.Grid.rowconfigure(self, 0, weight=1)
        self._tree.grid(column=0, row=0, sticky="nsew")
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
        print(self._tree.item(self._tree.focus()))
        return 'break'


class RegBlock(ttk.Frame):
    def __init__(self, master):
        ttk.Frame.__init__(master)


if __name__ == "__main__":
    _columns_seq = ("Name", "Address", "Field", "Property")
    root = tkinter.Tk()
    tree = ttk.Treeview(root, columns=_columns_seq)
    tree.insert("", 0, "Level1", text="Level1")
    tree.insert("Level1", 1, "Level2", text="Level2")
    tree.insert("Level2", 2, "Level3", text="Level3\nwode")
    tree.grid()

    tree = ttk.Treeview(root, columns=_columns_seq)
    tree.insert("", 0, "Level1-1", text="Level1")
    tree.insert("Level1", 1, "Level2-1", text="Level2")
    tree.insert("Level2", 2, "Level3-1", text="Level3\nwode")
    tree.grid()

    root.mainloop()
