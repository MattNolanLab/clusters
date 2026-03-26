from pathlib import Path
from argparse import ArgumentParser
import json

from spikeinterface_gui import run_mainwindow
import spikeinterface.full as si


parser = ArgumentParser()

parser.add_argument('--mouse')
parser.add_argument('--day')
parser.add_argument('--session')
parser.add_argument('--recording', action='store_true', default=False)
parser.add_argument('--protocol', default='kilosort4A')
parser.add_argument('--curation', default='curationA')
parser.add_argument('--MMNAV_folder', default=None)

args = parser.parse_args()

mouse, day, session, protocol, curation, NPehys_folder = int(args.mouse), int(args.day), args.session, args.protocol, args.curation, args.MMNAV_folder

active_projects_folder = Path('/run/user/1000/gvfs/smb-share:server=cmvm.datastore.ed.ac.uk,share=cmvm/sbms/groups/CDBS_SIDB_storage/NolanLab/ActiveProjects/')

if NPehys_folder is None:
    NPehys_folder = active_projects_folder / 'Harry/EphysNeuropixelData/'
NPehys_folder = Path(NPehys_folder)

deriv_folder = active_projects_folder / 'Chris/Cohort12/derivatives_for_split_analyzers'

pp_recording = None
if args.recording:
    if session in ['OF1', 'OF2']: 
        raw_folder = NPehys_folder / 'of'
    elif session == 'VR':
        raw_folder = NPehys_folder / 'vr'
    rec_folder = list(raw_folder.glob(f'M{mouse:02d}_D{day:02d}_*_{session}*'))[0]
    recording = si.read_openephys(rec_folder)
    grouped_pp_recording = si.common_reference(si.bandpass_filter(recording.split_by('group')))
    pp_recording = si.aggregate_channels(grouped_pp_recording)

mouseday_path = deriv_folder / f'M{mouse:02d}/D{day:02d}/{session.lower()}/{protocol}'

analyzer_path = mouseday_path / f'sub-M{mouse:02d}_ses-D{day:02d}_typ-{session}_srt-{protocol}_analyzer.zarr'

analyzer = si.load_sorting_analyzer(analyzer_path)

no_spikes_units = analyzer.unit_ids[(analyzer.get_extension('quality_metrics').get_data()['num_spikes'] == 0).values]
analyzer_removed = analyzer.remove_units(no_spikes_units)
kept_unit_ids = analyzer_removed.unit_ids

curation_dict=None

wolf_layout = dict(
    zone1=['unitlist','spikelist', 'curation'],
    zone2=['maintemplate', 'merge'],
    zone3=['trace', 'tracemap', 'spikeamplitude'],
    zone4=[],
    zone5=['spikerate'],
    zone6=['probe'],
    zone7=['waveform'],
    zone8=['correlogram', 'metrics', 'mainsettings'],
)

overlap = False
if args.recording:
    overlap = True

user_settings = {
    "waveform": {
        "overlap": overlap,
        "plot_selected_spike": True,
        "plot_waveforms_samples": False,
        "y_scalebar": True,
    },
    "spikeamplitude": {
        "max_spikes_per_unit": 10000,
    },
    "spikerate": {
        "bin_s": 30
    },
}

run_mainwindow(
    analyzer_removed,
    mode="desktop",
    curation=True,
    curation_dict = curation_dict,
    skip_extensions = ['waveforms', 'spike_locations'],
    verbose=True,
    layout=wolf_layout,
    user_settings=user_settings,
    recording=pp_recording,
)


