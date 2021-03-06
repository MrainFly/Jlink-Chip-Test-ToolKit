import pylink
from pylink import errors
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
        self.clear_error()
        try:
            return self.memory_read32(addr, num_words=1)[0]
        except errors.JLinkReadException:
            return False

    def write32(self, addr, data):
        self.clear_error()
        try:
            self.memory_write32(addr, [data])
        except errors.JLinkWriteException:
            return False


if __name__ == "__main__":
    pass
