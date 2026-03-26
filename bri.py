from pathlib import Path
from argparse import ArgumentParser

from loadi import Vandrey2026Experiment
from spikeinterface_gui import run_mainwindow
import spikeinterface.full as si
import pandas as pd

def main():

    parser = ArgumentParser()

    parser.add_argument('--mouse')
    parser.add_argument('--day')
    parser.add_argument('--session')
    parser.add_argument('--recording', action='store_true', default=False)
    parser.add_argument('--curation', default='curationA')

    args = parser.parse_args()

    mouse, day, session, curation  = args.mouse, args.day, args.session, args.curation

    active_projects_folder = Path('/run/user/1000/gvfs/smb-share:server=cmvm.datastore.ed.ac.uk,share=cmvm/sbms/groups/CDBS_SIDB_storage/NolanLab/ActiveProjects/')

    experiment = Vandrey2026Experiment(active_projects_folder)
    session = experiment.get_session(mouse, day, session)

    position = session.load_position()

    units = session.load_units(output="spikeinterface")
    recording = session.load_ephys()

    pp_rec = si.bandpass_filter(recording)

    analyzer = si.create_sorting_analyzer(units, pp_rec)
    analyzer.compute(['random_spikes', 'noise_levels', 'templates', 'quality_metrics', 'template_metrics', 'spike_amplitudes'])

    no_spikes_units = analyzer.unit_ids[(analyzer.get_extension('quality_metrics').get_data()['num_spikes'] == 0).values]
    analyzer_removed = analyzer.remove_units(no_spikes_units)

#    analyzer_removed._recording = None
#    analyzer_removed.save_as(format='binary_folder', folder='bri_analyzer')

#    analyzer_removed = si.load('bri_analyzer')

    video_path = Path(session.path_dict['video'])
    opto_path = video_path.parent / 'MountainSort/DataFrames/opto_pulses.pkl'

    opto_pulses = pd.read_pickle(active_projects_folder / opto_path)

    events = {
        'start': {
            'samples': opto_pulses['opto_start_times'].values,
        },
        'stop': {
            'samples': opto_pulses['opto_end_times'].values,
        },
    }

    bri_layout = dict(
        zone1=['spikelist', 'curation'],
        zone2=['ratemapview', 'merge'],
        zone3=['trace', 'tracemap', 'spikeamplitude'],
        zone4=[],
        zone5=['unitlist'],
        zone6=['probe'],
        zone7=['waveform'],
        zone8=['correlogram', 'metrics', 'mainsettings', 'event'],
    )

    overlap = False
    # if args.recording:
    #     overlap = True

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
        verbose=True,
        layout=bri_layout,
        user_settings=user_settings,
        recording=None,
        external_data={'position': position},
        events=events
    )

if __name__ == "__main__":
    main()