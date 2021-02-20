# Cheese Watch - Don't Move The Cheese

![Change Monitor](https://github.com/pauldoomgov/cheesewatch/workflows/Change%20Monitor/badge.svg)


![Mouse minding its cheese](misc/mouse-with-cheese.png)

Simple public information change monitor - Each task is run and
the output is stored under the `results/` directory in the repo.
The nest time the tasks are run the new output is compared to the old.

If the result is different, notifications are sent.   The next time
the job runs it will expect whatever was returned last time.

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
