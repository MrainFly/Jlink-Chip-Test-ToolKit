import pylink
import logging
from bitstring import BitArray


class SelfSWD(pylink.JLink):
    def __init__(self):
        pylink.JLink.__init__(self)
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

    def read32_plus(self, tpl):
        mem32 = self.read32(int(tpl[0], base=16))
        if tpl[1] or tpl[2]:
            # Have trouble
            return 0  # BitArray(bin(mem32))[int(tpl[1]):int(tpl[2])].hex
        return mem32

    def write32(self, addr, data):
        self.memory_write32(addr, data)

    def write32_plus(self, tpl, data):
        # Read address data
        mem32 = self.read32(int(tpl[0], base=16))


if __name__ == "__main__":
    swd = SelfSWD()
    print(swd.read32(0x46000000))
