import logging
from Excel2Json import E2J
import GuiRender


LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s - %(funcName)s - %(filename)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


def device_generator():
    memory_header = [{"Key": "Address Start", "Level": (1, ), "Priority": ("M", )},
                     {"Key": "Module", "Level": (1, ), "Priority": ("M", )},
                     {"Key": "Class", "Level": (1, ), "Priority": ("M", )}]
    memory_reheader = ("Address", "Name", "Class")
    memory_sheets = ("AP Peripheral AddrMapping", "CP Peripheral AddrMapping")
    memory_e2j = E2J(excel="Venus_SoC_Memory_Mapping.xls", header=memory_header, sheets=memory_sheets, reheader=memory_reheader)

    memory_e2j_list = [i for j in memory_e2j for i in j["Level"] if i["Class"]]
    for i in memory_e2j_list:
        i["Address"] = i["Address"].replace("_", "")

    header = [{"Key": "Sub-Addr\n(Hex)", "Level": (1,), "Priority": ("H", )},
              {"Key": "Start\nBit", "Level": (2,), "Priority": ("M", )},
              {"Key": "End\nBit", "Level": (2,), "Priority": ("M", )},
              {"Key": "R/W\nProperty", "Level": (2,), "Priority": ("M", )},
              {"Key": "Register\nName", "Level": (2, 1), "Priority": ("M", "M")},
              {"Key": "Register Description", "Level": (2, ), "Priority": ("L", )}
              ]

    reheader = ("Address", "Start", "End", "Property", "Name", "Description")

    e2j = E2J(excel="Venus_SoC_Memory_Mapping.xls", header=header, reheader=reheader)
    venus_device = []
    for dev in memory_e2j_list:
        for cla in e2j:
            if dev["Class"] == cla["Sheet_Name"]:
                dev["Level"] = cla["Level"]
                del dev["Class"]
                venus_device.append(dev)
                break

    def _sort_func(elem):
        return int(elem["Address"], base=16)

    venus_device.sort(key=_sort_func, reverse=False)

    return venus_device


if __name__ == "__main__":
    GuiRender.GUIBody(device_generator())
