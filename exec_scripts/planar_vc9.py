from time import time_ns
from influx_line_protocol import Metric
import sys
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TIMESTAMP = time_ns()


def power_outlet(block):
    metric = Metric("planar_vc9_power_outlet")
    metric.with_timestamp(TIMESTAMP)
    metric.add_value("breaker_open", to_binary(block["attributes"]["breaker_open"]))
    metric.add_value("current", float(block["attributes"]["current"] or -1))
    metric.add_tag("power_distribution", block["relations"]["power_distribution"])
    metric.add_tag("position", block["attributes"]["position"])
    print(metric)


def video_controller(block):
    metric = Metric("planar_vc9_video_controller")
    metric.with_timestamp(TIMESTAMP)

    metric.add_tag("genlock_status", block["attributes"]["genlock_status"])
    metric.add_tag("input_board", block["relations"]["input_board"])
    metric.add_tag("input_option", block["attributes"]["input_option"])
    metric.add_tag("model_name", block["attributes"]["model_name"])
    metric.add_tag("output_board", block["relations"]["output_board"])
    metric.add_tag("output_mode", block["attributes"]["output_mode"])
    metric.add_tag("output_option", block["attributes"]["output_option"])
    metric.add_tag("package_version", block["attributes"]["package_version"])
    metric.add_tag("serial_number", block["attributes"]["serial_number"])
    metric.add_tag("version_fpga_main", block["attributes"]["version_fpga_main"])
    metric.add_tag("version_micro", block["attributes"]["version_micro"])

    metric.add_value("fan_speed_1", float(block["attributes"]["fan_speed_1"] or -1))
    metric.add_value("fan_speed_2", float(block["attributes"]["fan_speed_2"] or -1))
    metric.add_value("fan_status", block["attributes"]["fan_status"])
    metric.add_value("fpga_temp", float(block["attributes"]["fpga_temp"] or -1))
    metric.add_value("intake_temp", float(block["attributes"]["intake_temp"] or -1))
    print(metric)


def system(block):
    metric = Metric("planar_vc9_system")
    metric.with_timestamp(TIMESTAMP)

    metric.add_tag("master", block["relations"]["master"])
    metric.add_tag("package_version", block["attributes"]["package_version"])
    metric.add_tag("panel_fw_version", block["attributes"]["panel_fw_version"])
    metric.add_tag("preset_status", block["attributes"]["preset_status"])
    metric.add_tag("wall", block["relations"]["wall"])

    metric.add_value("active_preset", block["attributes"]["active_preset"])
    print(metric)


def power_rectifier(block):
    metric = Metric("planar_vc9_power_rectifier")
    metric.with_timestamp(TIMESTAMP)

    metric.add_tag("power_distribution", block["relations"]["power_distribution"])
    metric.add_tag("position", block["attributes"]["position"])

    metric.add_value("fan_fault_1", float(block["attributes"]["fan_fault_1"] or 0))
    metric.add_value("fan_fault_2", float(block["attributes"]["fan_fault_2"] or 0))
    metric.add_value("fan_speed_1", float(block["attributes"]["fan_speed_1"] or -1))
    metric.add_value("fan_speed_2", float(block["attributes"]["fan_speed_2"] or -1))
    metric.add_value("in_current", float(block["attributes"]["in_current"] or -1))
    metric.add_value("in_voltage", float(block["attributes"]["in_voltage"] or -1))
    metric.add_value("out_current", float(block["attributes"]["out_current"] or -1))
    metric.add_value("out_voltage", float(block["attributes"]["out_voltage"] or -1))
    metric.add_value("present", int(block["attributes"]["present"] or -1))
    metric.add_value("state", int(block["attributes"]["state"] or -1))
    metric.add_value("temp_ambient", float(block["attributes"]["temp_ambient"] or -1))
    metric.add_value("valid", int(block["attributes"]["valid"] or -1))
    print(metric)


def panel(block):
    metric = Metric("planar_vc9_panel")
    metric.with_timestamp(TIMESTAMP)

    metric.add_tag("device_input", block["attributes"]["device_input"])
    metric.add_tag("fw_version", block["attributes"]["fw_version"])
    metric.add_tag("x", block["attributes"]["x"])
    metric.add_tag("y", block["attributes"]["y"])

    metric.add_value("connected", int(block["attributes"]["connected"] or -1))
    metric.add_value("temperature", float(block["attributes"]["temperature"] or -1))
    metric.add_value("voltage_24", float(block["attributes"]["voltage_24"] or -1))
    metric.add_value("voltage_48", float(block["attributes"]["voltage_48"] or -1))
    metric.add_value("watts", float(block["attributes"]["watts"] or -1))

    print(metric)


def power_supply(block):
    metric = Metric("planar_vc9_power_supply")
    metric.with_timestamp(TIMESTAMP)

    metric.add_tag("cpu_board", block["relations"]["cpu_board"])
    metric.add_tag("name", block["attributes"]["name"])
    metric.add_tag("power_distribution", block["relations"]["power_distribution"])
    metric.add_tag("system", block["relations"]["system"])

    metric.add_value("connected", int(block["attributes"]["connected"]))
    metric.add_value("rtc_battery_ok", int(block["attributes"]["rtc_battery_ok"] or -1))
    metric.add_value("temperature", float(block["attributes"]["temperature"] or -1))

    print(metric)


def planar_input(block):
    # if block["relations"]["source_port"] is None:
    #     return

    metric = Metric("planar_vc9_input")
    metric.with_timestamp(TIMESTAMP)

    metric.add_tag("source_port", block["relations"]["source_port"])
    metric.add_tag("type", block["attributes"]["type"])
    metric.add_tag("position", block["attributes"]["position"])

    metric.add_value("connected", int(block["attributes"]["connected"] or -1))

    print(metric)


def source_port(block):
    metric = Metric("planar_vc9_source_port")
    metric.with_timestamp(TIMESTAMP)

    metric.add_tag("key", block["key"])
    metric.add_tag("input", block["relations"]["input"])

    metric.add_value("height", block["attributes"]["height"])
    metric.add_value("pixel_depth", int(block["attributes"]["pixel_depth"]))
    metric.add_value("source_presence", int(block["attributes"]["source_presence"]))

    print(metric)


def output_expansion(block):
    metric = Metric("planar_vc9_output_expansion")
    metric.with_timestamp(TIMESTAMP)

    metric.add_tag("video_controller", block["relations"]["video_controller"])

    metric.add_value("fpga_temp", float(block["attributes"]["fpga_temp"] or -1))

    print(metric)


def process(item_class, block):
    processors = {
        "Input": planar_input,
        "OutputExpansion": output_expansion,
        "Panel": panel,
        "PowerOutlet": power_outlet,
        "PowerRectifier": power_rectifier,
        "PowerSupply": power_supply,
        "System": system,
        "VideoController": video_controller,
        "SourcePort": source_port,
    }
    return processors.get(item_class)(block)


def get_objects(data, item_class):
    return [
        process(item_class, data[i])
        for i, block in enumerate(data)
        if block["class"] == item_class
    ]

def to_binary(value) -> int:
    """Convert string/bool to integer where null/None is -1"""
    if type(value) is str:
        if str.lower() in ["true", "1"]:
            return 1
        elif str.lower() in ["false", "0"]:
            return 0
        else:
            return -1
    elif type(value) is bool:
        return int(value)
    else:
        return -1


def get_data():
    host = sys.argv[1]
    try:
       req = requests.get(f"https://{host}/api/full_configuration", verify=False)
       req.raise_for_status()
       return req.json()["data"]
    except Exception as e:
       raise SystemExit(e)
    # import json
    # with open(sys.argv[1]) as f:
    #     raw_data = f.read()
    # return json.loads(raw_data)['data']


if __name__ == "__main__":
    data = get_data()
    lines = []
    classes = [
        "PowerOutlet",
        "VideoController",
        "System",
        "PowerRectifier",
        "Panel",
        "PowerSupply",
        "Input",
        "OutputExpansion",
        "SourcePort",
    ]
    for class_ in classes:
        get_objects(data, class_)
