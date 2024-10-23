"""Collect metrics from Lightware MX2 matrix using LW3 protocol"""

import os
import sys
import socket

from influx_line_protocol import Metric, MetricCollection


def collect():
    host = sys.argv[1]
    port = 6107
    collection = MetricCollection()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((host, port))

    # read CPU temperature
    fan_response = get_properties(sock, f"/SYS/HSMB/FANCONTROL")
    metric = Metric("mx2")
    metric.add_tag("source", host)
    metric.add_value("matrix_temperature", float(fan_response['MaximalCurrentTemperature']))
    collection.append(metric)

    # read average of 3 fan speeds
    metric = Metric("mx2")
    metric.add_tag("source", host)
    avg_fan_rpm = (float(fan_response['Fan1Pwm']) + float(fan_response['Fan2Pwm']) + float(fan_response['Fan3Pwm'])) / 3
    metric.add_value("matrix_fan_rpm", avg_fan_rpm)
    collection.append(metric)

    # read firmware version
    uid_response = get_properties(sock, f"/MANAGEMENT/UID")
    metric = Metric("mx2")
    metric.add_tag("source", host)
    metric.add_tag("serial", uid_response["ProductSerialNumber"])
    metric.add_tag("firmware_version", uid_response["FirmwareVersion"])
    metric.add_value("matrix_info", 1)
    collection.append(metric)

    # read names of each port
    response = get_properties(sock, "/MEDIA/NAMES/VIDEO")
    port_names = {}
    for port in response:
        port_names[port] = response[port].split(";")[1]

    # metric for which input is routed to each destination
    # value of 0 means no source is routed
    response = get(sock, "/MEDIA/XP/VIDEO.DestinationConnectionStatus")
    i = 0
    for value in response.split(";")[:-1]:
        port = f"O{i+1}"

        metric = Metric("mx2")
        metric.add_tag("source", host)
        metric.add_tag("port", port)
        metric.add_tag("port_name", port_names[port])
        if value == '0':
            metric.add_value("xpt_connection", 0)
        else:
            metric.add_value("xpt_connection", int(value[1:]))
        collection.append(metric)
        i += 1

    # metric for destination port locked/muted state
    response = get(sock, "/MEDIA/XP/VIDEO.DestinationPortStatus")
    i = 0
    for code in response.split(";")[:-1]:
        port = f"O{i+1}"
        port_name = port_names[port]

        metric = Metric("mx2")
        metric.add_tag("source", host)
        metric.add_tag("port", port)
        metric.add_tag("port_name", port_names[port])
        metric.add_value("dest_locked", 0 if code[0] in ["T", "M"] else 1)
        collection.append(metric)

        metric = Metric("mx2")
        metric.add_tag("source", host)
        metric.add_tag("port", port)
        metric.add_tag("port_name", port_names[port])
        metric.add_value("dest_muted", 0 if code[0] in ["T", "L"] else 1)
        collection.append(metric)

        i += 1

    # metric for source port locked/muted state
    response = get(sock, "/MEDIA/XP/VIDEO.SourcePortStatus")
    i = 0
    for code in response.split(";")[:-1]:
        port = f"I{i+1}"

        metric = Metric("mx2")
        metric.add_tag("source", host)
        metric.add_tag("port", port)
        metric.add_tag("port_name", port_names[port])
        metric.add_value("src_locked", 0 if code[0] in ["T", "M"] else 1)
        collection.append(metric)

        metric = Metric("mx2")
        metric.add_tag("source", host)
        metric.add_tag("port", port)
        metric.add_tag("port_name", port_names[port])
        metric.add_value("src_muted", 0 if code[0] in ["T", "L"] else 1)
        collection.append(metric)

        i += 1

    # metrics for properties of each port
    ports = get_nodes(sock, "/MEDIA/PORTS/VIDEO")
    for port in ports:
        status = get_properties(sock, f"/MEDIA/PORTS/VIDEO/{port}/STATUS")

        metric = Metric("mx2")
        metric.add_tag("source", host)
        metric.add_tag("port", port)
        metric.add_tag("port_name", port_names[port])
        metric.add_value(
            "port_connected", 0 if status["Connected"].lower() == "false" else 1
        )
        collection.append(metric)

        metric = Metric("mx2")
        metric.add_tag("source", host)
        metric.add_tag("port", port)
        metric.add_tag("port_name", port_names[port])
        metric.add_value("active_hdcp_version", int(status["ActiveHdcpVersion"]))
        collection.append(metric)

        metric = Metric("mx2")
        metric.add_tag("source", host)
        metric.add_tag("port", port)
        metric.add_tag("port_name", port_names[port])
        metric.add_value("color_depth", int(status["ColorDepth"]))
        collection.append(metric)

        metric = Metric("mx2")
        metric.add_tag("source", host)
        metric.add_tag("port", port)
        metric.add_tag("port_name", port_names[port])
        metric.add_value(
            "embedded_audio_present", to_binary(status["EmbeddedAudioPresent"])
        )
        collection.append(metric)

        metric = Metric("mx2")
        metric.add_tag("source", host)
        metric.add_tag("port", port)
        metric.add_tag("port_name", port_names[port])
        metric.add_value("hdcp2_stream_type", int(status["Hdcp2StreamType"]))
        collection.append(metric)

        metric = Metric("mx2")
        metric.add_tag("source", host)
        metric.add_tag("port", port)
        metric.add_tag("port_name", port_names[port])
        metric.add_value(
            "max_supported_hdcp_version", int(status["MaxSupportedHdcpVersion"])
        )
        collection.append(metric)

        metric = Metric("mx2")
        metric.add_tag("source", host)
        metric.add_tag("port", port)
        metric.add_tag("port_name", port_names[port])
        metric.add_value("pixel_clock", float(status["PixelClock"]))
        collection.append(metric)

        metric = Metric("mx2")
        metric.add_tag("source", host)
        metric.add_tag("port", port)
        metric.add_tag("port_name", port_names[port])
        metric.add_value("scrambling", to_binary(status["Scrambling"]))
        collection.append(metric)

        metric = Metric("mx2")
        metric.add_tag("source", host)
        metric.add_tag("port", port)
        metric.add_tag("port_name", port_names[port])
        metric.add_value("tmds_clock_rate", to_binary(status["TmdsClockRate"]))
        collection.append(metric)

        metric = Metric("mx2")
        metric.add_tag("source", host)
        metric.add_tag("port", port)
        metric.add_tag("port_name", port_names[port])
        metric.add_value("bch_error_count", int(status["BchErrorCounter"]))
        collection.append(metric)

        metric = Metric("mx2")
        metric.add_tag("source", host)
        metric.add_tag("port", port)
        metric.add_tag("port_name", port_names[port])
        metric.add_value("active_hdcp_version", int(status["ActiveHdcpVersion"]))
        collection.append(metric)

        metric = Metric("mx2")
        metric.add_tag("source", host)
        metric.add_tag("port", port)
        metric.add_tag("port_name", port_names[port])
        metric.add_value("signal_present", to_binary(status["SignalPresent"]))
        collection.append(metric)

        for ch in range(3):
            metric = Metric("mx2")
            metric.add_tag("source", host)
            metric.add_tag("port", port)
            metric.add_tag("port_name", port_names[port])
            metric.add_tag("tmds_ch", str(ch))
            metric.add_value(
                "tmds_error_count",
                to_binary(status["TmdsErrorCounters"].split(";")[ch]),
            )
            collection.append(metric)

            metric = Metric("mx2")
            metric.add_tag("source", host)
            metric.add_tag("port", port)
            metric.add_tag("port_name", port_names[port])
            metric.add_tag("tmds_ch", str(ch))
            metric.add_value(
                "rx_tmds_error_count",
                to_binary(status["RxTmdsErrorCounters"].split(";")[ch]),
            )
            collection.append(metric)

        # add info metric with static value 1
        metric = Metric("mx2")
        metric.add_tag("source", host)
        metric.add_tag("port", port)
        metric.add_tag("port_name", port_names[port])
        metric.add_tag("active_resolution", status["ActiveResolution"])
        metric.add_tag("total_resolution", status["TotalResolution"])
        metric.add_tag("color_space", status["ColorSpace"])
        metric.add_tag("color_range", status["ColorRange"])
        metric.add_tag("signal_type", status["SignalType"])
        metric.add_tag("avi_if", status["AviIf"])
        metric.add_tag("vs_if", status["VsIf"])
        metric.add_value("info", 1)
        collection.append(metric)

    sock.shutdown(socket.SHUT_RDWR)
    sock.close()
    print(collection)


def to_binary(str: str) -> int:
    """Convert string representation of bool or 0/1 to integer"""
    if str.lower() in ["true", "1"]:
        return 1
    else:
        return 0


def get(sock: socket.socket, cmd: str) -> str:
    """Send command to device and return parsed response"""
    sock.sendall(f"GET {cmd}\r\n".encode())

    response = ""
    for _ in range(100):
        data = sock.recv(1024)
        response += data.decode()
        if data.decode().endswith("\r\n") or data.decode() == "":
            break

    return response.strip().split(cmd)[1][1:]


def get_nodes(sock: socket.socket, cmd: str) -> list:
    """Send command to device and return list of nodes"""
    sock.sendall(f"GET {cmd}\r\n".encode())

    response = ""
    for _ in range(100):
        data = sock.recv(1024)
        response += data.decode()
        if data.decode().endswith("\r\n") or data.decode() == "":
            break

    results = []
    for line in response.strip().split("\r\n"):
        results.append(line.split(cmd)[1][1:])

    return results


def get_properties(sock: socket.socket, cmd: str) -> list:
    """Send command to device and return list of properties"""
    signature = os.urandom(2).hex()
    sock.sendall(f"{signature}#GET {cmd}.*\r\n".encode())

    response = ""
    for _ in range(100):
        data = sock.recv(1024)
        response += data.decode()
        if data.decode().endswith("}\r\n") or data.decode() == "":
            break

    results = {}
    for line in response.strip()[7:-3].split("\r\n"):
        try:
            key = line.split(cmd)[1][1:].split("=")[0]
            value = line.split(cmd)[1][1:].split("=")[1] or None
            results[key] = value
        except IndexError:
            continue
    return results


if __name__ == "__main__":
    # import logging
    # logger = logging.getLogger(__name__)
    # logging.basicConfig(
    #     filename="/tmp/lightware_mx2.log",
    #     encoding="utf-8",
    #     level=logging.INFO,
    #     format="%(asctime)s [%(levelname)s] %(message)s",
    #     datefmt="%Y-%m-%d %H:%M:%S%z",
    # )

    try:
        collect()
    except Exception as e:
        # logger.error(e, exc_info=True)
        raise SystemExit(e)