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
        logging.info("Read the whole register: %s" % (hex(mem32)))
        if tpl[1] or tpl[2]:
            # Have trouble
            return (mem32 >> int(tpl[1])) & self._get_mask(int(tpl[2]) - int(tpl[1]) + 1)
        return mem32

    def write32(self, addr, data):
        self.memory_write32(addr, [data])

    def write32_plus(self, tpl, data):
        if tpl[1] or tpl[2]:
            # Read address data
            mem32 = self.read32(int(tpl[0], base=16))
            # Data & mask
            mask = self._get_mask(int(tpl[2]) - int(tpl[1]) + 1)
            logging.info("Generate mask: %s", hex(mask))
            # If input such as 1600, treat this value as dec
            # Else jump to the exception, and treat it as hex
            try:
                data = int(data) & mask
            except ValueError:
                data = int(data, base=16) & mask
            # Mem32 clean corresponding memory field
            mem32 &= ~(mask << int(tpl[1]))
            # Mem32 | Data << base
            mem32 |= data << int(tpl[1])
            # Write the word into memory
            logging.info("Write to the memory: %s --> %d" % (tpl[0], mem32))
            self.write32(int(tpl[0], base=16), mem32)
        else:
            self.write32(int(tpl[0], base=16), data)

    def _get_mask(self, lengh):
        mask = BitArray(bin(0x1 << lengh))
        mask.invert()
        mask = mask[1:]
        return mask.uint


if __name__ == "__main__":
    swd = SelfSWD()
    print(swd.read32_plus(("0x46000040", "23", "25")))
    swd.write32_plus(("0x46000040", "23", "25"), 0x3)
    print(swd.read32_plus(("0x46000040", "23", "25")))
