"""Collect metrics from Eyepower PDU using TCP socket protocol

Pass the IP address as sys.argv[1]"""

import sys
import socket

def send_command(sock: socket.socket, cmd: bytearray) -> bytearray:
    # remote_host = sock.getpeername()[0]
    # logger.info(f"TX {remote_host}: {cmd.hex(' ')}")
    sock.send(cmd)
    data = sock.recv(1024)

    # DLE (10H) is known as the Data Link Exception (or Escape) character, with STX or ETX preceded by DLE.
    # Where the data itself is 10H, two DLE’s are transmitted so we need to strip the second one.
    data = data.replace(b'\x10\x10', b'\x10')

    # logger.info(f"RX {remote_host}: {data.hex(' ')}")
    return data


def collect():
    host = sys.argv[1]
    port = 1243

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect((host, port))

    # read voltage
    data = send_command(sock, bytes.fromhex('10 02 FB 41 3C 10 03'))

    print(f"eyepower,source={host},inlet=main supply_volts_rms={int.from_bytes(data[4:6], byteorder='big') / 10}")
    if data[6:8] != b'\xff\xff':
        print(f"eyepower,source={host},inlet=backup supply_volts_rms={int.from_bytes(data[6:8], byteorder='big') / 10}")
    print(f"eyepower,source={host},inlet=main peak_volts={int.from_bytes(data[8:10], byteorder='big') / 10}")
    if data[10:12] != b'\xff\xff':
        print(f"eyepower,source={host},inlet=backup peak_volts={int.from_bytes(data[10:12], byteorder='big') / 10}")
    print(f"eyepower,source={host},inlet=main neutral_volts_rms={int.from_bytes(data[12:14], byteorder='big') / 10}")
    if data[14:16] != b'\xff\xff':
        print(f"eyepower,source={host},inlet=backup neutral_volts_rms={int.from_bytes(data[14:16], byteorder='big') / 10}")
    print(f"eyepower,source={host} neutral_bus_volts_rms={int.from_bytes(data[16:18], byteorder='big') / 10}")
    # I don't know how to interpret DC offset
    # print(f"eyepower,source={host} dc_offset_volts={int.from_bytes(data[18:20], signed=True, byteorder='little') / 1000}")
    print(f"eyepower,source={host},inlet=main frequency={int.from_bytes(data[20:22], byteorder='big') / 100}")
    if data[22:24] != b'\xff\xff':
        print(f"eyepower,source={host},inlet=backup frequency={int.from_bytes(data[22:24], byteorder='big') / 100}")
    # print(f"eyepower,source={host},outlet=1 outlet_amps={int.from_bytes(data[24:26], byteorder='big') / 1000}")
    # print(f"eyepower,source={host},outlet=2 outlet_amps={int.from_bytes(data[26:28], byteorder='big') / 1000}")
    # print(f"eyepower,source={host},outlet=3 outlet_amps={int.from_bytes(data[28:30], byteorder='big') / 1000}")
    # print(f"eyepower,source={host},outlet=4 outlet_amps={int.from_bytes(data[30:32], byteorder='big') / 1000}")
    # print(f"eyepower,source={host},outlet=5 outlet_amps={int.from_bytes(data[32:34], byteorder='big') / 1000}")
    # print(f"eyepower,source={host},outlet=6 outlet_amps={int.from_bytes(data[34:36], byteorder='big') / 1000}")
    # print(f"eyepower,source={host},outlet=7 outlet_amps={int.from_bytes(data[36:38], byteorder='big') / 1000}")
    # print(f"eyepower,source={host},outlet=8 outlet_amps={int.from_bytes(data[38:40], byteorder='big') / 1000}")
    # print(f"eyepower,source={host},outlet=9 outlet_amps={int.from_bytes(data[40:42], byteorder='big') / 1000}")
    # print(f"eyepower,source={host},outlet=10 outlet_amps={int.from_bytes(data[42:44], byteorder='big') / 1000}")
    # print(f"eyepower,source={host},outlet=11 outlet_amps={int.from_bytes(data[44:46], byteorder='big') / 1000}")
    # print(f"eyepower,source={host},outlet=12 outlet_amps={int.from_bytes(data[46:48], byteorder='big') / 1000}")
    # print(f"eyepower,source={host},outlet=13 outlet_amps={int.from_bytes(data[48:50], byteorder='big') / 1000}")
    # print(f"eyepower,source={host},outlet=14 outlet_amps={int.from_bytes(data[50:52], byteorder='big') / 1000}")
    print(f"eyepower,source={host} total_amps={int.from_bytes(data[52:54], byteorder='big') / 1000}")
    print(f"eyepower,source={host},inlet=main earth_leakage_amps={int.from_bytes(data[54:56], byteorder='big') / 1000}")
    if data[56:58] != b'\xff\xff':
        print(f"eyepower,source={host},inlet=backup earth_leakage_amps={int.from_bytes(data[56:58], byteorder='big') / 1000}")


    # read environment
    # This works with a basic 1-Wire configuration with no more than a single temperature or temp/humidity sensor.
    # Firmware version 1.4.3 onwards supports a maximum 16 external sensors which extends the basic reply
    # for each additional sensor live/min/max, giving 81H a variable length reply. See the eyePower
    # Windows software user manual for sensor configuration and fixing the sensor order in memory.
    data = send_command(sock, bytes.fromhex('10 02 FA 81 7B 10 03'))

    print(f"eyepower,source={host} dc_volts={data[10] / 10}")
    print(f"eyepower,source={host},sensor=internal temperature={data[17]}i")
    if data[20] != 255:
        print(f"eyepower,source={host},sensor=external temperature={data[20]}i")
    if data[23] != 255:
        print(f"eyepower,source={host},sensor=external humidity={data[23]}i")

    # read outlet/fuse/relay states
    data = send_command(sock, bytes.fromhex('10 02 FA 31 2B 10 03'))

    relay_state = ''.join(format(byte, '08b') for byte in data[4:6])
    outlet_state = ''.join(format(byte, '08b') for byte in data[7:9])
    fuse_state = ''.join(format(byte, '08b') for byte in data[9:11])
    print(f"eyepower,source={host} changeover_state={relay_state[0]}i")
    print(f"eyepower,source={host} alarm_state={relay_state[1]}i")
    print(f"eyepower,source={host},inlet=main fuse_state={fuse_state[1]}i")
    print(f"eyepower,source={host},inlet=backup fuse_state={fuse_state[0]}i")
    for i in range(1,15):
        #print(f"eyepower,source={host},outlet={i} relay_state={relay_state[16-i]}i")
        print(f"eyepower,source={host},outlet={i} outlet_state={outlet_state[16-i]}i")
        print(f"eyepower,source={host},outlet={i} fuse_state={fuse_state[16-i]}i")


if __name__ == "__main__":
    # import logging
    # logger = logging.getLogger(__name__)
    # logging.basicConfig(
    #     filename="/tmp/eyepower_pdu.log",
    #     encoding="utf-8",
    #     level=logging.INFO,
    #     format="%(asctime)s [%(levelname)s] %(message)s",
    #     datefmt="%Y-%m-%d %H:%M:%S%z",
    # )

    try:
        collect()
    except Exception as e:
        raise SystemExit(e)
