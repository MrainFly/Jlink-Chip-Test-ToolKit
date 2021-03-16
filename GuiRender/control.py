from SWDJlink import SelfSWD
from bitstring import BitArray
import logging
from functools import wraps


# Control widget
class Control:
    def __init__(self):
        # For SWD ********************
        self._SWD = None

        # For refresh ****************
        self.refresh_time = 100

        # For view handler ***********
        # Modify Tree Handler
        self._modify_tree_h = None
        # Check Button Handler
        self._check_button_h = None

        # For timer stage machine ****
        # Stage
        self.timer_sm = "None"
        self.timer_obj = None

        # For connect stage machine **
        self.connect_sm = "disconnected"

    def check_button_register(self, handler):
        self._check_button_h = handler

    def modify_tree_register(self, handler):
        self._modify_tree_h = handler

    def connect_stage_machine(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            func_name = func.__name__
            ret = True
            if self.connect_sm == "disconnected" and func_name == "connect":
                ret = func(self, *args, **kwargs)
                if ret:
                    self.connect_sm = "connected"

            elif self.connect_sm == "connected" and func_name == "disconnect":
                ret = func(self, *args, **kwargs)
                if ret:
                    self.connect_sm = "disconnected"

            elif self.connect_sm == "connected" and func_name in ("open_timer", "close_timer", "tree_refresh"):
                func(self, *args, **kwargs)

            return ret

        return wrapper

    @connect_stage_machine
    def connect(self):
        try:
            self._SWD = SelfSWD()
            logging.info("Connect to the target CORTEX-M33")
        except:
            # Can't open SWD
            self._SWD = None
            logging.error("Connect failed, check segger or reload chip")
            # Transmit to view level
            return False

        return True

    def connected(self):
        if self.connect_sm == "disconnected":
            return False
        elif self.connect_sm == "connected":
            return True

    @connect_stage_machine
    def disconnect(self):
        try:
            del self._SWD
            return True
        except:
            return False

    def write32_plus(self, tpl, data):
        if tpl[1] or tpl[2]:
            # Read address data
            mem32 = self._SWD.read32(int(tpl[0], base=16))
            if not mem32:
                return False
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
        if not mem32:
            return False
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

    def tree_refresh(self):
        # Get all the modify tree items
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

    def timer_stage_machine(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Connect and register check button
            if func.__name__ == "open_timer" and self.timer_sm == "None":
                logging.info("Running")
                func(self, *args, **kwargs)
                self.timer_sm = "running"
            elif func.__name__ == "close_timer" and self.timer_sm == "running":
                logging.info("Halt, waiting")
                func(self, *args, **kwargs)
                self.timer_sm = "None"
        return wrapper

    @connect_stage_machine
    @timer_stage_machine
    def open_timer(self):
        self.timer_obj = self._check_button_h.after(self.refresh_time, self._timer_refresh_callback)

    @connect_stage_machine
    @timer_stage_machine
    def close_timer(self):
        self._check_button_h.after_cancel(self.timer_obj)

    def _timer_refresh_callback(self):
        self.tree_refresh()
        self.timer_obj = self._check_button_h.after(self.refresh_time, self._timer_refresh_callback)
