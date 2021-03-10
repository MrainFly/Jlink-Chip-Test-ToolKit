from Excel2Json import E2J
import GuiRender
import logging

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


def device_generator():
    memory_header = [{"Key": "Address Start", "Level": (1, )},
                     {"Key": "Module", "Level": (1, 0)},
                     {"Key": "Class", "Level": (1, 0)}]
    memory_sheets = ("AP Peripheral AddrMapping", "CP Peripheral AddrMapping")
    memory_e2j = E2J(excel="Venus_SoC_Memory_Mapping.xls", header=memory_header, sheets=memory_sheets)

    memory_e2j_list = [i for j in memory_e2j for i in j["Level"] if i["Class"]]
    for i in memory_e2j_list:
        i["Address Start"] = i["Address Start"].replace("_", "")
        del i["Level"]

    header = [{"Key": "Sub-Addr\n(Hex)", "Level": (1,)},
              {"Key": "Start\nBit", "Level": (2,)},
              {"Key": "End\nBit", "Level": (2,)},
              {"Key": "R/W\nProperty", "Level": (2,)},
              {"Key": "Register\nName", "Level": (2, 1)},
              ]
    e2j = E2J(excel="Venus_SoC_Memory_Mapping.xls", header=header)
    venus_device = []
    for cla in e2j:
        for dev in memory_e2j_list:
            if dev["Class"] == cla["Sheet_Name"]:
                dev["Class"] = cla["Level"]
                venus_device.append(dev)

    def _sort_func(elem):
        return int(elem["Address Start"], base=16)

    venus_device.sort(key=_sort_func, reverse=True)

    return venus_device


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    GuiRender.GUIBody(device_generator())
