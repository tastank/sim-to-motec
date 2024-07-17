from stm import motec
from stm.channels import get_channel_definition
from stm.event import STMEvent

import argparse
import csv
from datetime import datetime
import re

channels = [
    "system_time","rpm","oil_press","oil_temp","water_press","water_temp","volts","fuel",
    # I'm not sure these can be used since they're not numerical data
    #"gps_utc_date","gps_utc_time",
    "lat","lon","alt","mph"#,"track"
#    { "name": "fuellevel", "units": "%" },
]

def update_event(event=None, log=None):
    if not event or not log:
        return
    
    # convert the event datetime to MoTeC format
    dt = datetime.fromisoformat(event.datetime)
    log.date = dt.strftime('%d/%m/%Y')
    log.time = dt.strftime('%H:%M:%S')
    
    log.datetime = event.datetime
    log.driver = event.driver
    log.vehicle = event.vehicle
    log.venue = event.venue
    log.comment = event.shortcomment
    log.event = motec.ld.MotecEvent({
        "name": event.name,
        "session": event.session,
        "comment": event.comment,
        "venuepos": 0
    })

    template_vars = {}
    for k, v in vars(event).items():
        if v is not None:
            v = str(v).replace(' ', '_')
            v = re.sub(r'(?u)[^-\w.]', '', v)
        else: 
            v = ""

        template_vars[k] = v


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Convert RPi data to MoTeC i2")
    parser.add_argument("input_filename", type=str, help="Name of CSV file to convert")
    parser.add_argument("output_filename", type=str, help="Name of MoTeC ld file output")
    parser.add_argument("--driver", type=str, default="Tyler Stank", help="Driver name")
    parser.add_argument("--session", type=str, default="", help="Session e.g. Practice, Qualify, Race")
    parser.add_argument("--vehicle", type=str, default="MX-3", help="Override name of vehicle")
    parser.add_argument("--venue", type=str, default="", help="Venue/Track name, MoTeC will not generate a track map without this")
    parser.add_argument("--metric", action="store_true", help="use metric units (currently unsupported)")
    parser.add_argument("--freq", type=int, default=10, help="frequency to collect samples, currently ignored")
    args = parser.parse_args()
    if args.input_filename == args.output_filename:
        raise ValueError("Input filename is the same as output filename!")

    event = STMEvent(
        name="test",
        session="test_session",
        vehicle="MX-3",
        driver="Tyler A Stank",
        venue="Black Earth",
        comment="",
        shortcomment=""
    )

    log = motec.ld.MotecLog()
    update_event(event, log)
    logx = motec.ldx.MotecLogExtra()

    # where does channels come from? it's a parameter for new_log
    for channel in channels:
        # params are channel, frequency (Hz), imperial units (boolean)
        cd = get_channel_definition(channel, 10, True)
        log.add_channel(cd)

    with open(args.input_filename, newline="") as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter=",", quotechar="\"")
        for row in csvreader:
            samples = [row[channel] for channel in channels]
            for i in range(len(samples)):
                if samples[i] == "":
                    samples[i] = 0
                samples[i] = float(samples[i])

            log.add_samples(samples)

    with open(args.output_filename, "wb") as fout:
        fout.write(log.to_string())
