import os
import json

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
raw_data_statistic_file_path = os.path.join(ROOT_PATH, "raw_data_statistic_CN.json")


class JSChart(object):
    def __init__(self, chart_series_list, chart_legend_list, chart_x_list):
        self.chart_series_list = chart_series_list
        self.chart_legend_list = chart_legend_list
        self.chart_x_list = chart_x_list

    def format2dic(self):
        series_dic = [chart_series.__dict__ for chart_series in self.chart_series_list]
        x_dic = [chart_x.data for chart_x in self.chart_x_list]
        legend_dic = [chart_legend.data for chart_legend in self.chart_legend_list]
        return {"regions_series": series_dic, "regions_x": x_dic, "regions_legend": legend_dic}


class ChartSeries(object):
    def __init__(self, name, type, data):
        self.name = name
        self.type = type
        self.data = data


class ChartLegend(object):
    def __init__(self, data):
        self.data = data


class ChartXAxis(object):
    def __init__(self, data):
        self.data = data


class VendorDataStat(object):
    chart_type = "line"

    def __init__(self, region, version, path, size, pretty_size):
        self.region = region
        self.version = version
        self.path = path
        self.pretty_size = pretty_size
        self.size = size

    @staticmethod
    def data2chart(vendor_data_list):
        region_version_size_dic = {}
        version_list = []
        for vendor_data in vendor_data_list:
            vendor_region = vendor_data.region
            vendor_version = vendor_data.version
            vendor_size = vendor_data.size
            region_version_size_dic.setdefault(vendor_region, {})[vendor_version] = vendor_size

            version_list.append(vendor_version)

        version_list = list(set(version_list))
        version_list.sort()
        # series
        chart_series_list = []
        for region, version_size_dic in region_version_size_dic.iteritems():
            region_version_list = version_size_dic.keys()
            chart_series_data = []
            for version in version_list:
                if version in region_version_list:
                    chart_series_data.append(version_size_dic[version])
                else:
                    chart_series_data.append(0)

            chart_series_list.append(ChartSeries(region, VendorDataStat.chart_type, chart_series_data))
        # x axis
        chart_x_list = [ChartXAxis(version) for version in version_list]
        #  legend
        chart_legend_list = [ChartLegend(region) for region in region_version_size_dic]
        return JSChart(chart_series_list, chart_legend_list, chart_x_list)


class ComponentStat(object):
    def __init__(self, name, path, size, pretty_size):
        self.name = name
        self.path = path
        self.size = size
        self.pretty_size = pretty_size


class StatisticJsonReader(object):
    @staticmethod
    def read_statistic_file(statistic_file_path):
        with open(statistic_file_path, "r") as f:
            data_json_list = json.load(f)
            data_json_list.sort(key=lambda d: d["version"])
            data_json_list.sort(key=lambda d: d["region"])
            # TODO remove same region same version data
            vendor_list = []
            vendor_components_dic = {}
            for vendor_data in data_json_list:
                region = vendor_data["region"]
                version = vendor_data["version"]
                data_path = vendor_data["data_path"]
                data_size = vendor_data["size"]
                vendor_pretty_size = vendor_data["vendor_pretty_size"]
                components = vendor_data["component_list"]
                vendor_list.append(VendorDataStat(region=region, version=version, path=data_path, size=data_size,
                                                  pretty_size=vendor_pretty_size))
                vendor_name = StatisticJsonReader.generate_vendor_name(region, version)
                component_list = []
                for component in components:
                    component_name = component["name"]
                    component_path = component["path"]
                    component_size = component["size"]
                    component_pretty_size = component["component_pretty_size"]
                    component_list.append(ComponentStat(name=component_name, path=component_path, size=component_size,
                                                        pretty_size=component_pretty_size))
                vendor_components_dic[vendor_name] = component_list
            return vendor_list, vendor_components_dic

    @staticmethod
    def generate_vendor_name(region, version):
        return "_".join([region, version])


REGIONS_VARIABLE_NAME = "regions"
REGIONS_JS_FILENAME = os.path.join(ROOT_PATH, "regions.js")


class JSUtils(object):
    @staticmethod
    def save_dic2js(file_name, data_dic):
        with open(file_name, "w") as f:
            for key, content in data_dic.iteritems():
                json_content = json.dumps(content, ensure_ascii=False)
                f.write("var {variable_name}={content};\n".format(variable_name=key, content=json_content))
            f.close()

    @staticmethod
    def generate_all_regions(vendor_data_list):
        js_chart = VendorDataStat.data2chart(vendor_data_list)
        #
        region_data_dic = js_chart.format2dic()
        JSUtils.save_dic2js(REGIONS_JS_FILENAME, region_data_dic)


def test_generate_regions_stat():
    vendor_data_list, vendor_components_dic = StatisticJsonReader.read_statistic_file(raw_data_statistic_file_path)
    JSUtils.generate_all_regions(vendor_data_list)


if __name__ == '__main__':
    test_generate_regions_stat()
