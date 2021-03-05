import tkinter
from tkinter import ttk


class RegTree(ttk.Treeview):
    def __init__(self, master, root):
        ttk.Treeview.__init__(master)
        self._root = root
        self._level = 0
        self._parent = ""

        self._gen_level(self._root)

    def _gen_level(self, root):
        # root not an empty list
        if root:
            for i in root:
                if self._level == 0:
                    self.insert(self._parent, "end", text=self._root["Sheet_Name"])
                else:
                    pass
        else:
            return True


class RegBlock(ttk.Frame):
    def __init__(self, master):
        ttk.Frame.__init__(master)


if __name__ == "__main__":
    root = tkinter.Tk()
    tree = ttk.Treeview(root)
    tree.insert("", "end", "Level1", text="Level1")
    tree.insert("Level1", "end", "Level2", text="Level2")
    tree.insert("Level2", "end", "Level3", text="Level3")

    tree.grid()
    root.mainloop()
