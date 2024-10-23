# Move all string fields to a new "info" metric as tags for Prometheus
load("logging.star", "log")

def apply(metric):
    info = deepcopy(metric)
    info.fields.clear()
    info.fields["info"] = 1
    popped = None
    for k, v in metric.fields.items():
        if type(v) == "string":
            popped = metric.fields.pop(k)
            log.debug("Removed string field: {} from {}".format(k, metric.name))
            info.tags[k] = v
    if popped == None:
        return metric
    else:
        return [metric, info]
