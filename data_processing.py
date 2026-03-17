import fastf1
import pandas as pd
import numpy as np

def clean_race_data(year, race_name):
    session = fastf1.get_session(year, race_name, "R")
    session.load()

    df = session.laps.copy()
    df = df.dropna(subset=['LapTime'])
    df['LapTime'] = df['LapTime'].dt.total_seconds()

    # filter non-representative laps
    df = df[df['LapNumber'] != 1]
    df = df[df['PitInTime'].isna()]
    df = df[df['PitOutTime'].isna()]
    df = df[df['TrackStatus'] == '1']

    # dirty air flagging
    df = flag_dirty_air(df)

    # fuel correction
    starting_fuel = 110
    total_race_laps = session.total_laps
    fuel_per_lap = starting_fuel / total_race_laps
    fuel_time_per_kg = 0.035

    fuel_correction = df['LapNumber'] * fuel_per_lap * fuel_time_per_kg
    df['FuelCorrectionLapTime'] = df['LapTime'] + fuel_correction

    # add identifiers
    df['Circuit'] = session.event['EventName']
    df['Year'] = year
    
    # select columns
    cols_to_keep = [
        'Driver', 'LapNumber', 'Stint', 'Compound', 'TyreLife',
        'Team', 'Position', 'DirtyAir', 'LapTime',
        'FuelCorrectedLapTime', 'Circuit', 'Year'
    ]

    return df[cols_to_keep]

def flag_dirty_air(df):
    # sort by lap number and track position
    df = df.sort_values(['LapNumber', 'Position'])

    # get LapStartDate of the car directly ahead (one pos higher)
    ahead_start = df.groupby('LapNumber')['LapStartDate'].shift(1)

    #compute gap in seconds
    gap_to_ahead = (df['LapStartDate'] - ahead_start).dt.total_seconds()

    # flag dirty air: gap < 1.5s (and not null, which handles p1)
    df['DirtyAir'] = gap_to_ahead < 1.5

    return df