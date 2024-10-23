"""Collect metrics from AJA Kumo router and return influx line protocol"""
import sys
import time
import asyncio

from aiohttp import ClientSession
from influx_line_protocol import Metric, MetricCollection

NOW = time.time_ns()

async def fetch_json(session: ClientSession, url: str) -> dict:
    resp = await session.request(method="GET", url=url)
    resp.raise_for_status()
    return await resp.json(content_type=None)


def get_value(response, param):
    """Return 0 if param doesn't exist. Parse string as int if possible."""

    try:
        value = response['configevents'][0][param]
        parsed_value = int(value)
    except KeyError:
        parsed_value = 0
    except ValueError:
        parsed_value = value

    return parsed_value


async def collect():
    collection = MetricCollection()
    session = ClientSession()

    url = f"http://{sys.argv[1]}/config?action=connect"
    response = await fetch_json(url=url, session=session)

    router_size = int(response['configevents'][0]['eParamID_NumberOfSources'])

    metric = Metric('kumo')
    metric.with_timestamp(NOW)
    metric.add_tag('serial', get_value(response, 'eParamID_FormattedSerialNumber'))
    metric.add_tag('sysname', get_value(response, 'eParamID_SysName'))
    metric.add_tag('sw_version', get_value(response, 'eParamID_SWVersion'))
    metric.add_tag('serial', get_value(response, 'eParamID_FormattedSerialNumber'))
    metric.add_value('info', 1)
    collection.append(metric)

    for i in range(1, router_size+1):
        metric = Metric("kumo")
        metric.with_timestamp(NOW)
        metric.add_tag('dest', str(i))

        dest_line1 = get_value(response, f'eParamID_XPT_Destination{i}_Line_1')
        dest_line2 = get_value(response, f'eParamID_XPT_Destination{i}_Line_2')
        metric.add_tag('dest_label', f"{dest_line1} {dest_line2}".strip())

        metric.add_value('src', get_value(response, f'eParamID_XPT_Destination{i}_Status'))
        collection.append(metric)

    pairs = [
        ('reference_format', 'eParamID_DetectReferenceFormat'),
        ('temperature', 'eParamID_Temperature'),
        ('ps_alarm', 'eParamID_PSAlarm'),
        ('temperature_alarm', 'eParamID_TemperatureAlarm'),
        ('reference_alarm', 'eParamID_ReferenceAlarm'),
        ('panel_locked', 'eParamID_PanelLocked'),
        ('connected_panels', 'eParamID_Connected_Panels'),
        ('authentication', 'eParamID_Authentication'),
    ]

    for label, param in pairs:
        metric = Metric("kumo")
        metric.with_timestamp(NOW)
        metric.add_value(label, get_value(response, param))
        collection.append(metric)

    print(collection)
    await session.close()


if __name__ == '__main__':
    try:
        asyncio.run(collect())
    except Exception as e:
        raise SystemExit(e)
