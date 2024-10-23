# iBoot PDU returns SNMP values of 999.99 for sensors which don't exist.
# This Starlark script drops any field with a value of 999.99.

def apply(metric):
    for field, value in metric.fields.items():
        if value == 999.99:
            metric.fields.pop(field)
    return metric
