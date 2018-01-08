import os
import json

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
raw_data_statistic_file_path = os.path.join(ROOT_PATH, "raw_data_statistic_CN.json")


def reader_raw_stat():
    with open(raw_data_statistic_file_path, "r") as f:
        data_json_list = json.load(f)
        data_json_list.sort(key=lambda d: d["version"])
        for vendor_data in data_json_list:
            region = vendor_data["region"]
            version = vendor_data["version"]
            data_size = vendor_data["size"]
            vendor_pretty_size = vendor_data["vendor_pretty_size"]
            components = vendor_data["component_list"]
            print "\t".join([region, version, str(data_size), vendor_pretty_size, "components"])
            for component in components:
                component_name = component["name"]
                component_path = component["path"]
                component_size = component["size"]
                component_pretty_size = component["component_pretty_size"]
                print u"\t".join(["", "", "", "", component_name, component_path, str(component_size),
                                  component_pretty_size])




if __name__ == '__main__':
    reader_raw_stat()
