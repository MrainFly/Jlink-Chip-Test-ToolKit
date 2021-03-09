import xlrd
import json
import os

__all__ = ["Excel2Json_ReleatePath", "E2J"]


Excel2Json_ReleatePath = os.getcwd()


class E2J:
    # eg: header=[{"Key": "x0", "Level": (1)}, {"Key": "x1", "Level": (1, 2)}, {"Key": "x2", "Level": 2},
    # {"Key": "x3", "Level": 2},]

    # [{"Sheet_Name": "sheet", "Level1": [{"Level1_x0": "_x0", "Level1_x1": "_x1", "Level2":
    # [{"Level2_x1": "_x1", "Level2_x2": "_x2", "Level2_x3": "_x3"}]},
    # {"Level1_x0": "_x0", "Level1_x1": "_x1", "Level2":
    # [{"Level2_x1": "_x1", "Level2_x2": "_x2", "Level2_x3": "_x3"}]}]}]
    def __init__(self, excel, header, sheets='all'):
        self._xlrd_handler = None
        self._dist = []
        self._pointer_stack = []
        # excel not None
        if excel:
            self._format = xlrd.inspect_format(excel)
            self.excel_path = excel
            self._xlrd_handler = xlrd.open_workbook(self.excel_path)

        self.header = header
        if sheets == "all":
            self.sheets = self._xlrd_handler.sheet_names()
        else:
            self.sheets = sheets

        # Init stack
        self._pointer_stack = [None for _ in range(1 + max(tuple(j for i in self.header for j in i["Level"])))]
        # Convert excel to json
        self._xl2strc()

    def _state_machine_level_check(self, row):
        temp_tuple = tuple(item+1 for item in range(max(tuple(j for i in self.header for j in i["Level"]))))
        for dct in self.header:
            # corresponding cell have value
            if row[dct["Num"]].value:
                temp_tuple = tuple(j for j in dct["Level"] if j in temp_tuple)
        # Only return the first element
        if temp_tuple:
            return temp_tuple[0]
        else:
            return None

    # 核心思想：发现同级别的数据单元时，将栈中同级的数据块填写到上一级块中的缓存单元中
    # eg：当前到Level2，又发现一个符合Level2的单元时，将当前的Level2压入上一层的Level1中的Level list中
    def _state_machine(self, rows):
        next(rows)
        for row in rows:
            level = self._state_machine_level_check(row)
            if level:
                if self._pointer_stack[level]:
                    try:
                        for i in reversed(range(1 + max(tuple(j for i in self.header for j in i["Level"])))):
                            if i == level:
                                self._pointer_stack[level - 1]["Level"].append(self._pointer_stack[level])
                                break
                            else:
                                self._pointer_stack[i - 1]["Level"].append(self._pointer_stack[i])
                                self._pointer_stack[i] = {}

                    except IndexError:
                        pass
                self._pointer_stack[level] = {}

                # get item of each header and corresponding number
                for num, dct in enumerate(self.header):
                    # check each item Level
                    if level in dct["Level"]:
                        # add an item to corresponding dictionary
                        # self._pointer_stack[level]
                        self._pointer_stack[level].update({dct["Key"]: row[dct["Num"]].value})

                self._pointer_stack[level].update({"Level": []})

        for i in reversed(range(1 + max(tuple(j for i in self.header for j in i["Level"])))):
            if i == 0:
                self._dist.append(self._pointer_stack[i])
            else:
                self._pointer_stack[i-1]["Level"].append(self._pointer_stack[i])

        return True

    def _locate_key(self, sheet):
        for f_num, dct in enumerate(self.header):
            for num, cell in enumerate(sheet.row(0)):
                if dct["Key"] == cell.value:
                    if "Num" in self.header[f_num].keys():
                        self.header[f_num]["Num"] = num
                    else:
                        self.header[f_num].update({"Num": num})
                    break
            else:
                # Not locate the key
                return False
        return True

    def _xl2strc(self):
        if not self._xlrd_handler:
            return False

        for sheet in self.sheets:
            # sheet handler
            handler = self._xlrd_handler.sheet_by_name(sheet)
            # locate all key
            if not self._locate_key(handler):
                continue

            for item in range(1 + max(tuple(j for i in self.header for j in i["Level"]))):
                self._pointer_stack[item] = None

            # add the dict into stack level0
            self._pointer_stack[0] = {"Sheet_Name": sheet, "Level": []}
            # state machine
            if not self._state_machine(handler.get_rows()):
                return False

        return True

    def dump(self, file=None):
        json.dump(self._dist, fp=file)

    def __getitem__(self, item):
        return self._dist[item]
