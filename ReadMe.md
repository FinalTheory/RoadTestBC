# RoadTestBC

A simple script to help your road test.

## How to use

1. Install necessary python packages.
1. Set your ICBC credentials as hard coded at begining of the script; also the desired date range, test location, etc.
1. `python3 road_test.py`
1. You should see some credentials keep printing out and trying to search for a valid road test.
1. If a spot is found, you'll hear audio notification and also receive SMS for verification code.
1. Ignore the printed `curl` command as it seems not working; once you receive SMS, you can simply redo the booking from ICBC web UI, as this spot is locked for you and guaranteed to be available there.
1. Ready to go!

Notice: macOS only.
