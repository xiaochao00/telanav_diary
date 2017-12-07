import xlwt

from common_utils import print_standout


class CSVSave:
    def __init__(self):
        pass

    @staticmethod
    def save_csv(data_list, header_list, filename):
        with open(filename, 'w') as f:
            f.write("\t".join(header_list) + "\n")
            for data in data_list:
                f.write("\t".join(data) + "\n")
            f.close()
            print_standout("write to [%s] finished." % filename)


class XLSSave:
    def __init__(self):
        pass

    @staticmethod
    def save_xls(data_list, header_list, filename, sheet_name=u'sheet1'):
        f = xlwt.Workbook()
        sheet1 = f.add_sheet(sheet_name, cell_overwrite_ok=True)
        i, j = 0, 0
        for j in range(len(header_list)):
            sheet1.write(i, j, header_list[j])
        i = 1
        for row in data_list:
            for j in range(len(row)):
                sheet1.write(i, j, row[j])
            i += 1

        f.save(filename)
