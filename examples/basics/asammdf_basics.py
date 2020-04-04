"""
About: Load MDF log files & DBCs from an input folder and showcase various operations
Test: Last tested with asammdf v5.19.9 + MDF4 J1939 samples from the CANedge Intro docs
"""
from asammdf import MDF
import matplotlib.pyplot as plt
from datetime import timedelta
import glob, sys


# load MDF/DBC files from input folder
mdf_extension = ".mf4"
logfiles = glob.glob("input/*" + mdf_extension)
dbc = glob.glob("input/*.dbc")
signals = ["EngineSpeed", "WheelBasedVehicleSpeed"]
print("Log file(s): ", logfiles, "\nDBC(s): ", dbc)


# concatenate MDF files from input folder and export as CSV incl. timestamps (localized time)
mdf = MDF.concatenate(logfiles)
mdf.save("concatenated", overwrite=True)
mdf.export("csv", filename="concatenated", time_as_date=True, time_from_zero=False)

# extract info from meta header - e.g. to get correct start time of a file
session_start = mdf.header.start_time
delta_seconds = mdf.select(["CAN_DataFrame.BusChannel"])[0].timestamps[0]
split_start = session_start + timedelta(seconds=delta_seconds)
split_start_str = split_start.strftime("%Y%m%d%H%M%S")

# filter an MDF
mdf_filter = mdf.filter(["CAN_DataFrame.ID", "CAN_DataFrame.DataBytes"])
mdf.save("filtered", overwrite=True)

# DBC convert the unfiltered MDF + save & export
mdf_scaled = mdf.extract_can_logging(dbc, ignore_invalid_signals=True)
mdf_scaled.save("scaled", overwrite=True)
mdf_scaled.export(
    "csv",
    filename="scaled",
    time_as_date=True,
    time_from_zero=False,
    single_time_base=True,
)

# extract a list of signals from a scaled MDF
mdf_scaled_signal_list = mdf_scaled.select(signals)

# extract a filtered MDF based on a signal list
mdf_scaled_signals = mdf_scaled.filter(signals)

# extract a single signal from the unscaled MDF
mdf_scaled_signal = mdf.get_can_signal(name=signals[0], database=dbc[0])

# create pandas dataframe from the scaled MDF and perform operations
pd = mdf_scaled.to_dataframe(time_as_date=True)

# filter the dataframe based on the timestamp (UTC) and column values
pd["ratio"] = pd.loc[:, signals[0]] / pd.loc[:, signals[1]]
pd_f = pd.loc["2020-01-13 13:58:35":"2020-01-13 13:59:56"]
pd_f = pd_f[(pd_f[signals[0]] > 640)]
print("\nFiltered pandas dataframe:\n", pd_f)


# trigger an action if a condition is satisfied
signal_stats = pd_f[signals[0]].agg(["count", "min", "max", "mean", "std"])
signal_diff = signal_stats["max"] - signal_stats["min"]
max_diff = 300

if signal_diff > max_diff:
    print(f"Filtered {signals[0]} max difference of {signal_diff} is above {max_diff}")
    pd_f.plot(y=signals[0])
    plt.savefig(f"signal_{signals[0]}.png")
    # do something, e.g. send a warning mail with a plot
