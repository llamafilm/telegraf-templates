import sys
import asyncio
import csv

from bscpylgtv import WebOsClient
from influx_line_protocol import Metric, MetricCollection

TV_IP = sys.argv[1]
TV_SERIAL = sys.argv[2]

async def collect(client_key):
    collection = MetricCollection()

    client = await WebOsClient.create(TV_IP, get_hello_info=True, ping_interval=None, client_key=client_key)
    await client.connect()

    audio_status = await client.get_audio_status()
    configs = await client.get_configs()

    metric = Metric("webos")
    metric.add_tag('source', TV_IP)
    metric.add_tag("audio_volume_mode", audio_status['volumeStatus']['mode'])
    metric.add_tag('audio_output', client.sound_output)
    metric.add_tag('power_state', client.power_state.get('state'))
    metric.add_tag('current_app', client.current_appId)
    metric.add_tag('model_name', client.system_info.get('modelName'))
    metric.add_tag('firmware_version', f"{client.software_info.get('major_ver')}.{client.software_info.get('minor_ver')}")
    metric.add_tag('webos_ReleaseVersion', f"{client.hello_info.get('deviceOSReleaseVersion')}")
    metric.add_tag('webos_Version', f"{client.hello_info.get('deviceOSVersion')}")
    metric.add_tag('serial', f"{client.system_info.get('serialNumber')}")
    metric.add_tag('cell_type', f"{configs['configs'].get('tv.model.cellType')}")
    metric.add_tag('edid_type', f"{configs['configs'].get('tv.model.edidType')}")
    metric.add_tag('lvdsBits', f"{configs['configs'].get('tv.model.lvdsBits')}")
    metric.add_tag('moduleBackLightType', f"{configs['configs'].get('tv.model.moduleBackLightType')}")
    metric.add_tag('panelGamutType', f"{configs['configs'].get('tv.model.panelGamutType')}")
    metric.add_tag('panelLedBarType', f"{configs['configs'].get('tv.model.panelLedBarType')}")
    metric.add_tag('soundModeType', f"{configs['configs'].get('tv.model.soundModeType')}")
    metric.add_tag('panelGamutType', f"{configs['configs'].get('tv.model.panelGamutType')}")
    metric.add_tag('panelGamutType', f"{configs['configs'].get('tv.model.panelGamutType')}")
    metric.add_value('info', 1)
    collection.append(metric)

    metric = Metric("webos")
    metric.add_tag('source', TV_IP)
    metric.add_value('audio_volume', client.volume)
    collection.append(metric)

    metric = Metric("webos")
    metric.add_tag('source', TV_IP)
    metric.add_value('audio_mute_state', int(client.muted))
    collection.append(metric)

    metric = Metric("webos")
    metric.add_tag('source', TV_IP)
    metric.add_value('picture_backlight', client.picture_settings.get('backlight'))
    collection.append(metric)

    metric = Metric("webos")
    metric.add_tag('source', TV_IP)
    metric.add_value('picture_brightness', client.picture_settings.get('brightness'))
    collection.append(metric)

    metric = Metric("webos")
    metric.add_tag('source', TV_IP)
    metric.add_value('picture_color', client.picture_settings.get('color'))
    collection.append(metric)

    metric = Metric("webos")
    metric.add_tag('source', TV_IP)
    metric.add_value('picture_contrast', client.picture_settings.get('contrast'))
    collection.append(metric)

    for input in ['hdmi1', 'hdmi2', 'hdmi3', 'hdmi4']:
        spd_vendor = client.inputs[f'com.webos.app.{input}'].get('spdVendorName')
        spd_description = client.inputs[f'com.webos.app.{input}'].get('spdProductDescription')
        spd_info = client.inputs[f'com.webos.app.{input}'].get('spdSourceDeviceInfo')

        metric = Metric("webos")
        metric.add_tag('source', TV_IP)
        metric.add_tag('input', input)
        metric.add_tag('spd_device', f"{spd_vendor} {spd_description}")
        metric.add_tag('spd_info', spd_info)
        metric.add_tag('label', client.inputs[f'com.webos.app.{input}']['label'])
        metric.add_value('input_info', 1)
        collection.append(metric)

        metric = Metric("webos")
        metric.add_tag('source', TV_IP)
        metric.add_tag('input', input)
        metric.add_tag('label', client.inputs[f'com.webos.app.{input}']['label'])
        metric.add_value('input_connected', int(client.inputs[f'com.webos.app.{input}']['connected']))
        collection.append(metric)

        metric = Metric("webos")
        metric.add_tag('source', TV_IP)
        metric.add_tag('input', input)
        metric.add_tag('label', client.inputs[f'com.webos.app.{input}']['label'])
        metric.add_value('hdmiPlugIn', int(client.inputs[f'com.webos.app.{input}']['hdmiPlugIn']))
        collection.append(metric)

    print(collection)

    await client.disconnect()


def to_binary(str: str) -> int:
    """Convert string representation of bool or 0/1 to integer"""
    if str.lower() in ["true", "1"]:
        return 1
    else:
        return 0


async def obtain_credentials():
    """Run interactively to obtain and print credentials for new TV"""

    print(f"Connecting to {TV_IP}. Please accept prompt on TV.")
    client = await WebOsClient.create(TV_IP, get_hello_info=True)
    await client.connect()

    #print(f"Connected to {client.proto}://{client.ip}:{client.port}")
    #print(client.hello_info)
    #print(client.system_info)
    print("Connected! Add this key to SecretsManager.")
    print("\n#############################################")
    print("Serial       Client Key")
    print(f"{client.system_info.get('serialNumber')},{client.client_key},{client.system_info.get('modelName')}")
    print("#############################################\n")


if __name__ == '__main__':
    # example command: python3 lg_webos.py 192.168.20.13 init
    if len(sys.argv) == 3 and sys.argv[2] == 'init':
        asyncio.run(obtain_credentials())

    else:
        keyfile = '/run/webos_keys.csv'

        try:
            with open(keyfile, mode='r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['serial'] == TV_SERIAL:
                        client_key = row['key']
                        break
                else:
                    raise SystemExit(f"Unable to read key for serial: {TV_SERIAL}")

        except (FileNotFoundError):
            raise SystemExit(f"Unable to read key file: {keyfile}")

        try:
            asyncio.run(collect(client_key))
        except Exception as e:
            raise SystemExit(e)
