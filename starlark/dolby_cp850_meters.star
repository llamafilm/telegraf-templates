"""Split MeterLevels string into 10 separate numbers and drop the original"""
load("logging.star", "log")

def apply(metric):
    if 'MeterLevels' not in metric.fields:
        return metric

    other_fields = deepcopy(metric)
    for k,v in other_fields.fields.items():
        if k == 'MeterLevels':
            other_fields.fields.pop(k)

    new_metrics = [other_fields]

    log.debug("Parsing Dolby meter level string: " + metric.fields['MeterLevels'])
    all_levels = metric.fields['MeterLevels'].split(' ')

    channels = ['L', 'R', 'C', 'LFE', 'Lss', 'Rss', 'Lrs', 'Rrs', 'Lts', 'Rts']

    for idx, channel in enumerate(channels):
        m = deepcopy(metric)
        m.fields.clear()
        m.tags['channel'] = channel
        m.fields['meter_level_dbfs'] = int(all_levels[idx])
        new_metrics.append(m)

    return new_metrics
