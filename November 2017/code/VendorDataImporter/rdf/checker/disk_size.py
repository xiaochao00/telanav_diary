class DiskSize:
    UNIT_FORMAT = "MB"

    UNIT_MB = "MB"
    UNIT_B = "B"
    UNIT_KB = "KB"
    UNIT_GB = "GB"
    UNIT_RATE_RULES = {UNIT_MB: 1, UNIT_KB: (1.0 / 1024), UNIT_GB: 1024, UNIT_B: (1.0 / 1024 / 1024)}

    def __init__(self, size, unit):
        self.size = size
        self.unit = unit

    def __str__(self):
        if not self.size:
            return "size is None"

        return "%s%s" % (self.size, self.unit)

    @staticmethod
    def format_size_unit(unit, size):
        """
        transform size by unit. standard unit is MB : UNIT_FORMAT
        :param unit: unit,size
        :param size:
        :return:
        the size after transform to MB
        return the format DiskSize object (size: , unit: UNIT_FORMAT)
        """

        if not size or not (unit.upper() in DiskSize.UNIT_RATE_RULES.keys()):
            return None

        rule = DiskSize.UNIT_RATE_RULES[unit.upper()]

        size = int(size * rule)

        # transform to the format unit
        return DiskSize(size=size, unit=DiskSize.UNIT_FORMAT)


if __name__ == '__main__':
    d = DiskSize(None, "MB")
    print d
