from GuiRender import RegBlock
from .control import Control
from tkinter import ttk
import tkinter


class GUIBody:
    def __init__(self, para):
        self._root = tkinter.Tk()
        self._root.title("ListenAI Jlink Tool")
        self._root.geometry("1600x800")
        self._root.resizable(width=False, height=False)
        self._root.wm_attributes("-topmost", 1)

        # Configure style
        # self._base_style()
        self._control_handler = Control()

        self._regtree = RegBlock.RegTree(self._root, self._control_handler, para)
        self._regtree.grid_propagate(0)
        self._regtree.pack(fill="both", expand=True)

        self._root.mainloop()

    # def _base_style(self):
        # style = ttk.Style()
        # style.configure("TButton",
        #                 background="#3c3f41",
        #                 relief=tkinter.FLAT,
        #                 highlightcolor="#3c3f41"
        #                 )
        # style.map("Flat.TButton",
        #           highlightcolor=[("!focus", "#3c3f41"),
        #                           ("focus", "#4c5052")],
        #           )


if __name__ == "__main__":
    pass
