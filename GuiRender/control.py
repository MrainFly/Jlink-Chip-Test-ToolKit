from SWDJlink import SelfSWD
from bitstring import BitArray
import logging


# Control widget
class Control:
    def __init__(self):
        self._SWD = None
        self._connected = False
        # Modify Tree Handler
        self._modify_tree_h = None

    def connect(self):
        try:
            self._SWD = SelfSWD()
            self._connected = True
            logging.info("Connect to the target CORTEX-M33")
        except:
            # Can't open SWD
            self._SWD = None
            logging.error("Connect failed, check segger or reload chip")
            # Transmit to view level
            return False

        return True

    def connected(self):
        return self._connected

    def disconnect(self):
        if self.connected():
            del self._SWD
            self._connected = False
            logging.info("Disconnect success")
            return True
        else:
            logging.error("Need connect target first")
            return False

    def write32_plus(self, tpl, data):
        if tpl[1] or tpl[2]:
            # Read address data
            mem32 = self._SWD.read32(int(tpl[0], base=16))
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
            self._SWD.write32(int(tpl[0], base=16), mem32)
        else:
            self._SWD.write32(int(tpl[0], base=16), data)

    def read32_plus(self, tpl):
        mem32 = self._SWD.read32(int(tpl[0], base=16))
        logging.info("Read the whole register: %s" % (hex(mem32)))
        if tpl[1] or tpl[2]:
            # Have trouble
            return (mem32 >> int(tpl[1])) & self._get_mask(int(tpl[2]) - int(tpl[1]) + 1)
        return mem32

    def _get_mask(self, lengh):
        mask = BitArray(bin(0x1 << lengh))
        mask.invert()
        mask = mask[1:]
        return mask.uint

    def modify_tree_register(self, handler):
        self._modify_tree_h = handler

    def tree_refresh(self):
        # Connect and obtain the modify tree handler
        if self._modify_tree_h and self._connected:
            # Get all the modify tree items
            logging.info("Get the tree values")
            self._sub_tree_refresh()

    def _sub_tree_refresh(self, p=None):
        items = self._modify_tree_h.get_children(p)
        if not items:
            return
        for item in items:
            # Get corresponding tree item information
            dct = self._modify_tree_h.item(item)
            # Ignore the level0
            if dct["tags"][0] == 0:
                pass
            else:
                # Get the corresponding address value again
                value = str(hex(self.read32_plus(self._modify_tree_h.parse_address(dct["values"][0]))))
                values = dct["values"]
                values[-1] = value
                # Reload
                self._modify_tree_h.item(item, values=values)
            self._sub_tree_refresh(item)
