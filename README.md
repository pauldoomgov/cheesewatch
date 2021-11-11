# CheeseWatch - Don't Move The Cheese

![Global Cheese Positioning System](https://github.com/pauldoomgov/cheesewatch/workflows/Global%20Cheese%20Positioning%20System/badge.svg)


![Mouse minding its cheese](misc/mouse-with-cheese.png)

**CheeseWatch** is a public information change monitor that performs
a series of tasks on a schedule and alerts if the output changes.

The CheeseWatch process:
* The mouse is awakened by Octocat (at 15 minutes past the hour by default)
* The mouse checks the position of the cheese (runs scripts, dumps output to `results/`,
  uses `git diff` to detect changes)
* If things have changed the mouse gets angry, sends notifications,
  and then updates its mental model (`git commit && git push`)
* The mouse goes back to sleep

<!-- TOC -->

- [CheeseWatch - Don't Move The Cheese](#cheesewatch---dont-move-the-cheese)
  - [Cloning](#cloning)
  - [Modifying](#modifying)
  - [Checks](#checks)
    - [namecheck](#namecheck)
    - [certcheck](#certcheck)
    - [dnsseccheck](#dnsseccheck)
  - [Security and Privacy](#security-and-privacy)
  - [Jobs](#jobs)
  - [Local Testing](#local-testing)

<!-- /TOC -->
## Cloning

You can fork this repo!  Make sure to update `.github/workflows/cheesecheck.yml`
as follows:

* (Optional) Update the schedule by adjusting the `cron` entry:
~~~
  schedule:
    - cron: "15 * * * *"
~~~
* Update `NAMELIST` with a space delimited list of the fully qualified DNS names you wish to monitor
  for changes.  A and CNAME record types are allowed
* Update `CERTLIST` with a space delimited list of the FQDNs (and optionally :PORT) you wish to monitor
  for certificate changes.

Your `results/` directory will be updated on the next push to GitHub.

## Modifying

Remember that Cheese Watch modifies its own repo as it makes checks.
Pull a fresh copy of the branch you wish to modify before committing
changes.

* New scripts can be added under `bin/` and just need to dump out consistent
  output.  JSON is recommended to allow easy ingestion later.
* If you add Python, don't forget to update `requirements.txt`!
* Add a step to the `runchecks` job in `.github/workflows/cheesecheck.yml` somewhere
 between the `### START CHECKS` and `### END CHECKS` comments like:
~~~
      ### START CHECKS
      - name: Lookup DNS Records
        run: bin/namecheck.py ${NAMELIST} > temp/namecheck.json
      - name: Lookup DNSSEC Records
        run: bin/dnsseccheck.py ${DNSSECLIST} > temp/dnsseccheck.json
      - name: Gather TLS Certificate Chains
        run: bin/certcheck.py ${CERTLIST} > temp/certcheck.json
      - name: MY NEW CHECK
        run: bin/my-new-check.py ${SOMETHING} > temp/my-new-check.json
      ### END CHECKS
~~~
* In the example we add a variable named `SOMETHING` - Make sure that
  is defined in the `env` section at the top of `.github/workflows/cheesecheck.yml`

Commit, push, and watch Github Actions.

## Checks

### namecheck

`namecheck.py` takes a list of FQDNs (Fully Qualified Domain Names) and returns
the current IP addresses for those names.   CNAME records are resolved to A records.

What is this good for?
* Monitoring dynamic IPs for services like AWS Application Load Balancer which change over
  time due to maintenance
* Making sure certain names always resolve

**What does good look like?**

~~~json
{
    "github.com": [
        [
            "github.com. 0 IN A 140.82.113.4"   <-- A record including IP address
        ]
    ]
}
~~~

**What changes are probably normal?**

IP address changes are normal if the destination is an AWS load balancer or other system
that automatically manages the list of IP addresses serving the target, these will change
as the provider conducts maintenance or upgrades.

If the destination is dynamically addressed, which is the case for more residential Internet
connections, the IP will change as the ISP assigns a new address.

**What might be incredibly bad?**

~~~json
{
    "github.com": [
        "The DNS operation timed out after 5.00583815574646 seconds"
    ]
}
~~~

### certcheck

`certcheck.py` takes a list of FDQNs (with optional `:PORT`) and fetches the TLS
certificate from the server:port, returning expiration and the chain of trust.

NOTE - Certificate validation is NOT performed by this check.

What is this good for?
* Monitoring automatically updated certificates from providers like Let's Encrypt
  or AWS ACM
* Keeping track of TLS certificate changes that may relate to sudden problems

**What does good look like?**

~~~json
{
    "github.com": {
        "expiration": "2022-03-30T23:59:59",   <-- Not expired
        "chain": {
            "/C=US/ST=California/L=San Francisco/O=GitHub, Inc./CN=github.com": {
                "serial": 19335859262210987870682549325523936958,
                "issuer": "/C=US/O=DigiCert, Inc./CN=DigiCert High Assurance TLS Hybrid ECC SHA256 2020 CA1"
            },
            "/C=US/O=DigiCert, Inc./CN=DigiCert High Assurance TLS Hybrid ECC SHA256 2020 CA1": {
                "serial": 8510242666029254186823484260964302358,
                "issuer": "/C=US/O=DigiCert Inc/OU=www.digicert.com/CN=DigiCert High Assurance EV Root CA"
            }
        }
    }
}
~~~

**What changes are probably normal?**

Before the expiration, the `serial` of the first certificate (CN=FQDN) should change.

If the new certificate is acquired from a different provider, or signed with a new
intermediate (middle) or root (last) certificate, the `issuer` in the first record
will change, as long as the remaining certificates.

**What might be incredibly bad?**

Here is an expired certificate:

~~~json
{
    "github.com": {
        "expiration": "1999-12-31T23:59:59",      <--- EXPIRED!
        "chain": {
            "/C=US/ST=California/L=San Francisco/O=GitHub, Inc./CN=github.com": {
                "serial": 19335859262210987870682549325523936958,
                "issuer": "/C=US/O=DigiCert, Inc./CN=DigiCert High Assurance TLS Hybrid ECC SHA256 2020 CA1"
            },
            "/C=US/O=DigiCert, Inc./CN=DigiCert High Assurance TLS Hybrid ECC SHA256 2020 CA1": {
                "serial": 8510242666029254186823484260964302358,
                "issuer": "/C=US/O=DigiCert Inc/OU=www.digicert.com/CN=DigiCert High Assurance EV Root CA"
            }
        }
    }
}
~~~

Or what if someone accidentally replaced your usual cert with a self-signed internal one?

~~~json
{
    "github.com": {
        "expiration": "2022-09-19T05:08:42",
        "chain": {
            "/O=Acme Co/CN=Kubernetes Ingress Controller Fake Certificate": {
                "serial": 294929072338281157892513874388366759449,
                "issuer": "/O=Acme Co/CN=Kubernetes Ingress Controller Fake Certificate" <-- Self signed
            }
        }
    }
}
~~~

### dnsseccheck

`dnsseccheck.py` takes a list of DNS zone names and returns the DNSKEY records and
DS (trust anchor) records for each.  DS records are checked to ensure each refers
to an available DNSKEY and has a correct digest value.

What is this good for?
* Ensuring proper DNSSEC records exist
* Keeping an eye on activities like KSK (Key Signing Key) rotations

Note that `dnsseccheck.py` uses `etc/insecure-resolv.conf` to override
DNS resolver settings.   This allows it to bypass DNSSEC validation which could
interfere with some lookups.   Quad9's 9.9.9.10 insecure resolver is used
for this purpose.  Update `etc/insecure-resolv.conf` to use an alternate
resolver if desired, and kids: **Never** use an insecure resolver for normal use!

**What does good look like?**

Here is a DNSSEC enabled zone working properly:

~~~json
{
    "internetsociety.org": {
        "_errors": [],
        "dnskey_records": [
            [
                2371,   <-- Key Signing Key (KSK) with key ID 2371
                {
                    "value": "257 3 13 mdsswUyr3DPW132mOi8V9xESWE8jTo0d xCjjnopKl+GqJxpVXckHAeF+KkxLbxIL fDLUT0rAK9iUzy1L53eKGQ==",
                    "type": "KSK"
                }
            ],
            [
                34505,
                {
                    "value": "256 3 13 oJMRESz5E4gYzS/q6XDrvU1qMPYIjCWz JaOau8XNEZeqCYKD5ar0IRd8KqXXFJkq mVfRvMGPmM1x8fGAa2XhSA==",
                    "type": "ZSK"
                }
            ]
        ],
        "ds_records": [
            [
                "2371_SHA256",  <-- DS record pointing to KSK ID 2371 noted above
                {
                    "value": "2371 13 2 39fdc63793db261f978f59086a5d1d17bde3b5a32e2a4d55c8ece6027d969c33",
                    "valid_key_digest": true
                }
            ]
        ]
    }
}
~~~

It is also valid to not have DNSSEC.  You may want to monitor a non-DNSSEC zone to
see if they add it later.   Here is a happy non-DNSSEC zone:

~~~json
{
    "github.com": {
        "_errors": [
            "No DNSKEY records found for github.com",
            "No DS records found for github.com - DNSSEC not active for zone"
        ],
        "dnskey_records": [],
        "ds_records": []
    }
}
~~~

It is also valid to have DNSKEY records but no DS record.  This indicates the zone
may be preparing to enable signing, but has not yet.

~~~json
{
    "eventually.com": {
        "_errors": [
            "No DS records found for eventually.com - DNSSEC not active for zone"
        ],
        "dnskey_records": [
            [
                12875,
                {
                    "value": "257 3 13 FpqfahowrOrGC1eiVNmZ5VMiFTG0+Bio yyLZSFe9hcVCD0v5hXg/wpLXMI0qoutM /yIIHQosHq3e5cSKf59Hag==",
                    "type": "KSK"
                }
            ],
            [
                46078,
                {
                    "value": "256 3 13 qAu6QvJi7JEr3Q0kJ1iS6koD7BPdf0A0 09Z4SCB4f0Crvh5G5PkRS27G0xYU1KLJ 0q8N6ft53W53LO7tlloZKA==",
                    "type": "ZSK"
                }
            ],
            [
                64552,
                {
                    "value": "256 3 13 dehbDoM+X7d0YM5kAz9YZVoiSZOsIZyi ioCWYiMcXr71ou4WCathnq72SHJPOEJG 8HUipnfJDv0bq38kTat3pQ==",
                    "type": "ZSK"
                }
            ]
        ],
        "ds_records": []    <-- No DS records, so validating DNS servers will not try to validate this zone
    }
}
~~~

**What changes are probably normal?**

The most common change with be DNSKEY records with a type of ZSK (Zone Signing Key).
These are often rotated automatically.

KSK type DNSKEYs are generally rotated less frequently.  The following pattern is
normal for a key rotation:

1. New KSK added
1. DS record updated to reference the new KSK ID with a correct digest to match
1. At least 2 times the DS record TTL passes...
1. Old KSK removed

**What might be incredibly bad?**

Here is a zone with two DS records, both pointing to KSKs that do not exist:

~~~json
{
    "dnssec-failed.org": {
        "_errors": [
            "DS record in dnssec-failed.org for key ID 106 does not match a DNSKEY!",
            "DS record in dnssec-failed.org for key ID 106 does not match a DNSKEY!"
        ],
        "dnskey_records": [
            [
                29521,
                {
                    "value": "257 3 5 AwEAAb/f/pB/FLWoYp3j+HtldGkbUMT6 caAw2rej0DZkgXVFOKn4PWi3BYjCozjE qxeramt+9b1SMuOSJ8vGKWr0YKrfyfJi gsVxpsMgJ7QWcxeMACjC/oM8BPjDFBby /CgQQE63nPVX2SfDWCRhEhTOnsPZpKJv q66IHF/w+3u0IpyeplQWvO+HJ9OQPOQr stM7d/IPa7yKEtqS2nhBT0GWX2/GYhT6 oE7F4vc2VF9f6MjpB/pWPzkcx636YaxG 9P0QRBvzdD/Wztcbz1Scgxw5sUlIkQAz WV1mJfvXF+7NqzGcc94/kMt1VUzN2kYA SRyn1ALiFPfNLz4VMUvSw5fpNS0=",
                    "type": "KSK"
                }
            ],
            [
                44973,
                {
                    "value": "256 3 5 AwEAAewq/QcrsNX3C/nAAWyNY74f/q9R b2dGLc3LOIkQBATwzIcDTDHNRjtRDxjq uImNpoDKybI2hZ2e8mNKvCK/F/QXV5La fLwSzscqwvzJxEGZUA+JuiGu6kq/8OjE 6EEAdYlk4ztN6OWfwuqj4ZolBjKPXCPo dYvhj8gl7kqpopqr",
                    "type": "ZSK"
                }
            ]
        ],
        "ds_records": [
            [
                "106_SHA1",
                {
                    "value": "106 5 1 4f219dce274f820ea81ea1150638dabe21eb27fc",
                    "dangling": true     <-- Does NOT match a KSK :(
                }
            ],
            [
                "106_SHA256",
                {
                    "value": "106 5 2 ae3424c9b171af3b202203767e5703426130d76ef6847175f2eed355f86ef1ce",
                    "dangling": true
                }
            ]
        ]
    }
}
~~~

If any DS record shows as either `"dangling": true` or `"valid_key_digest": false`, validating DNS
resolvers will refuse to resolve anything in the zone.   If there is a mix of valid and invalid
DS records, resolution may be inconsistent, but expect a ratio of at least INVALID / TOTAL requests
to fail.
## Security and Privacy

All information monitored by CheeseWatch must be **public** and
well known.

**Good Use**:
* External DNS queries
* Public TLS Certificate information
* Something you would be comfortable putting on a billboard

**Bad Use**:
* Anything requiring authentication to access
* Anything identifying a person (email address, name, home IP address, etc)
* Something you would not be comfortable putting on a billboard

## Jobs

Each job must return a consistent result.   Sort your output,
don't include time or other things that change, etc.

Keep the mouse happy.

## Local Testing

Use `act` - https://github.com/nektos/act
