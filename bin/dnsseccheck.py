#!/usr/bin/env python3
# Check DNSSEC related records and validation for a domain

import sys
from dns import exception, resolver, rrset
import json


def rrserialize(obj):
    if isinstance(obj, rrset.RRset):
        return sorted(obj.to_text().split("\n"))
    return obj.__dict__


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("Please specify at least one name to resolve\n")
        sys.exit(1)

    out = {}

    for name in sorted(sys.argv[1:]):
        try:
            result = resolver.resolve(name, "DS")
        except resolver.NXDOMAIN:
            out[name] = [f"No DS records found for: {name}"]
            continue
        except exception.DNSException as err:
            out[name] = [f"{err}"]
            continue

        for rr in result.response.answer:
            # Zero out the TTLs for consistency
            rr.ttl = 0

        out[name] = {"ds_records": result.response.answer}

    # All that to get a fully sorted record dump.  :sigh:
    print(json.dumps(out, indent=4, default=rrserialize))

    sys.exit(0)


if __name__ == "__main__":
    main()
