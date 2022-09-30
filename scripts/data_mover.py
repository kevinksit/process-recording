from pathlib import Path
from holofun.simple_guis import openfoldergui
from tqdm import tqdm
import shutil
import time

# note: assumes you are saving date/mouse/epoch on the server
use_gui = True
multithreaded = False

# not needed if using gui
mouse = 'w49_1'
date = '20220706'

# remote server location
remote = 'x:/will/scanimage data'

# daq file loc
daq_loc = 'x:/setupdaq'

# vis stim data loc
vis_loc = 'x:/stimdata'

# local destination
destination = 'f:/experiments'



###---- begin moving files ----###
if use_gui:
    pth = openfoldergui(rootdir=remote, title='Select experiment to move...')
    src = Path(pth)
    mouse = src.stem
    date = src.parent.stem
else:
    src = Path(remote, date, mouse)
        
dst = Path(destination, mouse, date)
daq_loc = Path(daq_loc)
vis_loc = Path(vis_loc, date[2:], mouse)

# make the direction locally if it doesn't exist for that mouse
if not dst.parent.exists():
    print(f'Making new folder for mouse {mouse}')
try:
    dst.mkdir(parents=True)
except FileExistsError:
    raise FileExistsError('Experiment already exists? Canceling...')

# find epoch folders
root_data = [fold for fold in src.iterdir()]
root_folders = [f for f in root_data if f.is_dir()]
root_files = [f for f in root_data if f.is_file()]
    
# move all the tiff and other SI files     
print('Moving root folder files...')
time.sleep(1) 
for item in tqdm(root_files):
    shutil.copy(item, dst)

print('Moving epoch folders...')
n = len(root_folders)
for i,item in enumerate(root_folders):
    dir_name = item.stem
    new_folder = dst/dir_name
    new_folder.mkdir()
    print(f"Moving folder '{item.stem}' ({i+1}/{n})...")
    files_in_folder = list(item.glob('*'))
    time.sleep(1)
    for f in tqdm(files_in_folder):
        if f.is_file():
            shutil.copy(f, new_folder)
        elif f.is_dir():
            # shutil.copytree(f, new_folder) # this errors because it tried to copy the whole tree
            pass
        
# download daq file, download multiple if they exist for the same day
print('Searching for DAQ file...')
daq_fname = date[2:] + '*'
daq_file = list(daq_loc.glob(daq_fname))
if len(daq_file) == 0:
    print('No DAQ file found, skipping.')
else:
    if len(daq_file) > 1:
        print(f'Multiple DAQ files found for {date}. Downloading them all.')
    else:
        print('Downloading DAQ file.')
    for df in daq_file:
        shutil.copy(df, dst)    

# search for PT files and download
if vis_loc.exists():
    print('Found PT vis stim file(s). Downloading...')
    # make a pt directory
    for f in vis_loc.iterdir():
        shutil.copy(f, dst)
else:
    print('No PT vis files found, skipping.')
    
print('Done moving files :)')
print('Have a nice day!')