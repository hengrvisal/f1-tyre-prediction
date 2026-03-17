import time
import fastf1
import pandas as pd
import os

from data_processing import clean_race_data
from fastf1.exceptions import RateLimitExceededError

cache_dir = "cache_data"
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)
fastf1.Cache.enable_cache(cache_dir)

def build_dataset(year_range=(2022, 2023)):
    all_frames = []

    for year in range(year_range[0], year_range[1] + 1):
        schedule = None
        while schedule is None:
            try:
                schedule = fastf1.get_event_schedule(year, include_testing=False)
                schedule = schedule[schedule['RoundNumber'] > 0]
            except RateLimitExceededError:
                print(f"Rate limited on {year} schedule. Waiting 10 min...")
                time.sleep(600)

        for _, event in schedule.iterrows():
            race_name = event['EventName']
            success = False
            while not success:
                try:
                    clean = clean_race_data(year, race_name)
                    all_frames.append(clean)
                    print(f"OK: {year} {race_name} ({len(clean)} laps)")
                    success = True
                except RateLimitExceededError:
                    print(f"Rate limited on {year} {race_name}. Waiting 10 min...")
                    time.sleep(600)
                except Exception as e:
                    print(f"FAILED: {year} {race_name}: {e}")
                    success = True  # skip this race, move on

    dataset = pd.concat(all_frames, ignore_index=True)
    print(f"\nDone: {len(all_frames)} races, {len(dataset)} total laps")
    return dataset

dataset = build_dataset(year_range=(2022, 2025))
dataset.to_csv('clean_f1_data.csv', index=False)