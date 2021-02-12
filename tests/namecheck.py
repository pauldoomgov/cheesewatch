#!/usr/bin/env python3
# Lookup a DNS name and return a consistent sorted result output

import sys
from dns import resolver, rrset
import json


def rrserialize(obj):
    if isinstance(obj, rrset.RRset):
        return sorted(obj.to_text().split("\n"))
    return obj.__dict__


if len(sys.argv) < 2:
    sys.stderr.write("Please specify at least one name to resolve\n")
    sys.exit(1)

out = {}

for name in sorted(sys.argv[1:]):
    try:
        result = resolver.resolve(name)
    except resolver.NXDOMAIN as err:
        out[name] = [f"No DNS records found for: {name}"]
        continue

    for rr in result.response.answer:
        # Zero out the TTLs for consistency
        rr.ttl = 0

    out[name] = result.response.answer

# All that to get a fully sorted record dump.  :sigh:
print(json.dumps(out, indent=4, default=rrserialize))

sys.exit(0)
