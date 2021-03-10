import pylink
import logging


class SelfSWD(pylink.JLink):
    def __init__(self):
        pylink.JLink.__init__(self)
        self.open()
        self.set_tif(pylink.enums.JLinkInterfaces.SWD)
        self.connect("CORTEX-M33")
        # logging.info("Connect to the target")

    def __del__(self):
        self.close()

    def read32(self, addr):
        return self.memory_read32(addr, num_words=1)


if __name__ == "__main__":
    swd = SelfSWD()
    print(swd.read32(0x45000000))
