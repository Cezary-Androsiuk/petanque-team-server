import os
import re
from datetime import datetime

from constants import DATA_DIRECTORY_VALID

def files_count_in_data_directory():
    try:
        return len([f for f in os.listdir(DATA_DIRECTORY_VALID)])
    except FileNotFoundError:
        return -1
    

def get_newest_data_file(category: int):
    pattern = re.compile(rf".*-{category}-(\d{{8}}_\d{{6}})\.json$")
    latest_file = None
    latest_dt = None
    
    for filename in os.listdir(DATA_DIRECTORY_VALID):
        match = pattern.match(filename)
        if match:
            dt_str = match.group(1)
            try:
                dt = datetime.strptime(dt_str, "%Y%m%d_%H%M%S")
                if latest_dt is None or dt > latest_dt:
                    latest_dt = dt
                    latest_file = filename
            except ValueError:
                continue # skip errors
            
    return os.path.join(DATA_DIRECTORY_VALID, latest_file);