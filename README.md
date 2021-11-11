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
      - name: Gather TLS Certificate Chains
        run: bin/certcheck.py ${CERTLIST} > temp/certcheck.json
      - name: MY NEW CHECK
        run: bin/my-new-check.py ${SOMETHING} > temp/my-new-check.json
      ### END CHECKS
~~~
* In the example we add a variable named `SOMETHING` - Make sure that
  is defined in the `env` section at the top of `.github/workflows/cheesecheck.yml`

Commit, push, and watch Github Actions.

## CHECKS

### namecheck

`namecheck.py` takes a list of FQDNs (Fully Qualified Domain Names) and returns
the current IP addresses for those names.   CNAME records are resolved to A records.

What is this good for?
* Monitoring dynamic IPs for services like AWS Application Load Balancer which change over
  time due to maintenance
* Making sure certain names always resolve

### certcheck

`certcheck.py` takes a list of FDQNs (with optional `:PORT`) and fetches the TLS
certificate from the server:port, returning expiration and the chain of trust.

What is this good for?
* Monitoring automatically updated certificates from providers like Let's Encrypt
  or AWS ACM
* Keeping track of TLS certificate changes that may relate to sudden problems

#### dnsseccheck

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
resolver if desired, and kids: NEVER use an insecure resolver for normal use!

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
