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
        self._base_style()
        self._control_handler = Control()

        self._regtree = RegBlock.RegTree(self._root, self._control_handler, para)
        self._regtree.grid_propagate(0)
        self._regtree.pack(fill="both", expand=True)

        self._root.mainloop()

    def _base_style(self):
        style = ttk.Style()
        style.configure("Stage.TButton",
                        font=("Helvetica", 18),
                        background="green",
                        foreground="green",
                        borderwidth="5",
                        relief="RAISED",
                        )
        style.configure("DisStage.TButton",
                        font=("Helvetica", 18),
                        background="red",
                        foreground="red",
                        borderwidth="5",
                        relief="RAISED",
                        )
        style.configure("Stage.TLabel",
                        font=("Helvetica", 14),
                        justify=tkinter.CENTER,
                        )
        style.configure("Stage.TRadiobutton",
                        font=("Helvetica", 18),
                        justify=tkinter.CENTER,
                        )


if __name__ == "__main__":
    pass
