from ttkthemes import ThemedTk
from GuiRender import RegBlock


class GUIBody:
    def __init__(self, para):
        self._root = ThemedTk("blue")
        self._root.title("ListenAI Jlink Tool")
        self._root.geometry("1600x800")
        self._root.resizable(width=False, height=False)

        self._regtree = RegBlock.RegTree(self._root, para)
        self._regtree.grid(row=0, column=0, sticky="news")

        self._root.mainloop()


if __name__ == "__main__":
    pass
