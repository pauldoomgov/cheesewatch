# Cheese Watch - Don't Move The Cheese

![Change Monitor](https://github.com/pauldoomgov/cheesewatch/workflows/Change%20Monitor/badge.svg)

Simple change monitor - Each task is run and the output is
stored as a GitHub Actions Artifact.  The nest time the task
is run the new output is compared to the old.

If the result is different, the job fails.   The next time
the job runs it will expect whatever was returned last time.

## Jobs

Each job must return a consistent result.   Sort your output,
don't include time or other things that change, etc.

Keep the mouse happy.

## Local Testing

Use `act` - https://github.com/nektos/act
