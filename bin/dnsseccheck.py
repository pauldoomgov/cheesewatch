#!/usr/bin/env python3
# Check DNSSEC related records and validation for a domain

import sys
from dns import dnssec, exception, resolver, rrset
import json

# File to overide system resolv.conf - Use alternate forwarder
RESOLV_CONF = "etc/insecure-resolv.conf"

# DNSSEC records are huge and prone to timeouts - Set above 5 sec default
LOOKUP_TIMEOUT = 30


def rrserialize(obj):
    if isinstance(obj, rrset.RRset):
        return sorted(obj.to_text().split("\n"))
    return obj.__dict__


def get_dnskeys(res, name):
    out = {"_errors": [], "dnskey_records": (), "ksk_records": {}}

    try:
        result = res.resolve(name, "DNSKEY")
        for rr in result.response.answer:
            # Zero out the TTLs for consistency
            rr.ttl = 0
        answer = result.response.answer[0]
    except resolver.NoAnswer:
        out["_errors"].append(f"No DNSKEY records found for {name}")
        answer = []
    except resolver.NXDOMAIN:
        out["_errors"].append(f"Domain not found: {name}")
        return out
    except exception.DNSException as err:
        out["_errors"].append(f"DNSKEY error for {name}: {err}")
        answer = []

    dnskey_records = {}
    for k in answer:
        id = dnssec.key_id(k)
        dnskey_records[id] = {"value": k.to_text()}
        if k.flags == 257:
            dnskey_records[id]["type"] = "KSK"
            # Stash for later signature checks
            out["ksk_records"][id] = {"name": name + ".", "record": k}
        elif k.flags == 256:
            dnskey_records[id]["type"] = "ZSK"
        else:
            out["_errors"].append(
                f"Unknown DNSSKEY flags for {name} key ID {id}: {k.flags}"
            )

    out["dnskey_records"] = sorted(dnskey_records.items())

    return out


def get_ds(res, name, ksk_records):
    out = {"_errors": [], "ds_records": ()}
    try:
        result = res.resolve(name, "DS")
        for rr in result.response.answer:
            # Zero out the TTLs for consistency
            rr.ttl = 0
        answer = result.response.answer[0]
    except resolver.NoAnswer:
        out["_errors"].append(
            f"No DS records found for {name} - DNSSEC not active for zone"
        )
        answer = []
    except resolver.NXDOMAIN:
        out["_errors"].append(f"Domain not found: {name}")
        return out
    except exception.DNSException as err:
        out["_errors"].append(f"DS error for {name}: {err}")
        answer = []

    ds_records = {}
    for ds in answer:
        digest_name = {1: "SHA1", 2: "SHA256", 3: "SHA384"}.get(
            ds.digest_type, "UNKNOWN"
        )
        id = f"{ds.key_tag}_{digest_name}"

        if id in ds_records:
            out["_errors"].append(
                f"Duplicate DS record with digest {digest_name} in {name} for {ds.key_tag}"
            )
            continue

        ds_records[id] = {"value": ds.to_text()}
        if ds.key_tag in ksk_records:
            if ds == dnssec.make_ds(
                ksk_records[ds.key_tag]["name"],
                ksk_records[ds.key_tag]["record"],
                ds.digest_type,
            ):
                ds_records[id]["valid_key_digest"] = True
            else:
                ds_records[id]["valid_key_digest"] = False
                out["_errors"].append(
                    f"Invalid DS key digest value in {name} for key ID {ds.key_tag}"
                )
        else:
            ds_records[id]["dangling"] = True
            out["_errors"].append(
                f"DS record in {name} for key ID {ds.key_tag} does not match a DNSKEY!"
            )

    out["ds_records"] = sorted(ds_records.items())

    return out


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("Please specify at least one name to resolve\n")
        sys.exit(1)

    out = {}

    res = resolver.Resolver(filename=RESOLV_CONF)
    res.timeout = LOOKUP_TIMEOUT
    res.lifetime = LOOKUP_TIMEOUT

    for name in sorted(sys.argv[1:]):
        out[name] = {"_errors": []}

        ret = get_dnskeys(res, name)
        out[name]["_errors"].extend(ret["_errors"])
        out[name]["dnskey_records"] = ret["dnskey_records"]

        ret = get_ds(res, name, ret["ksk_records"])
        out[name]["_errors"].extend(ret["_errors"])
        out[name]["ds_records"] = ret["ds_records"]

    # All that to get a fully sorted record dump.  :sigh:
    print(json.dumps(out, indent=4, default=rrserialize))

    sys.exit(0)


if __name__ == "__main__":
    main()
