import pylink
import logging


class SelfSWD(pylink.JLink):
    def __init__(self):
        super(SelfSWD, self).__init__()
        self.open()
        self.set_tif(pylink.enums.JLinkInterfaces.SWD)
        self.connect("CORTEX-M33")
        if self.connected():
            logging.info("Connect to the target")
        else:
            logging.error("Disconnect to the target")

    def __del__(self):
        self.close()

    def read32(self, addr):
        return self.memory_read32(addr, num_words=1)[0]

    def write32(self, addr, data):
        self.memory_write32(addr, [data])


if __name__ == "__main__":
    pass
