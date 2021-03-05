from Excel2Json import E2J

if __name__ == "__main__":
    header = [{"Key": "Sub-Addr\n(Hex)", "Level": (1,)},
              {"Key": "Start\nBit", "Level": (2,)},
              {"Key": "End\nBit", "Level": (2,)},
              {"Key": "R/W\nProperty", "Level": (2,)},
              {"Key": "Register\nName", "Level": (2, 1)},
              ]
    e2j = E2J(excel="Venus_SoC_Memory_Mapping.xls", header=header)
    for i in e2j:
        print(i)