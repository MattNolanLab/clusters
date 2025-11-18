from pathlib import Path
from argparse import ArgumentParser
import json

from spikeinterface_gui import run_mainwindow
import spikeinterface.full as si


def main():

    parser = ArgumentParser()

    parser.add_argument('mouse')
    parser.add_argument('day')
    parser.add_argument('session')
    parser.add_argument('--protocol', default='kilosort4A')
    parser.add_argument('--curation', default='curationA')
    parser.add_argument('--deriv_folder', default=None)

    args = parser.parse_args()
    
    mouse, day, session, protocol, curation, deriv_folder = int(args.mouse), int(args.day), args.session, args.protocol, args.curation, args.deriv_folder

    if deriv_folder is None:
        deriv_folder = Path('/run/user/1000/gvfs/smb-share:server=cmvm.datastore.ed.ac.uk,share=cmvm/sbms/groups/CDBS_SIDB_storage/NolanLab/ActiveProjects/Wolf/MMNAV/derivatives')


    mouseday_path = deriv_folder / f'M{mouse:02d}/D{day:02d}/{session}/{protocol}'
    
    analyzer_path = mouseday_path / f'sub-{mouse:02d}_day-{day:02d}_ses-{session}_srt-{protocol}_analyzer.zarr'
    curation_path = mouseday_path / f'sub-{mouse:02d}_day-{day:02d}_ses-{session}_srt-{protocol}_{curation}.json'

    with open(curation_path) as f:
        curation_dict = json.load(f)

    analyzer = si.load_sorting_analyzer(analyzer_path)

    no_spikes_units = analyzer.unit_ids[(analyzer.get_extension('quality_metrics').get_data()['num_spikes'] == 0).values]
    analyzer_removed = analyzer.remove_units(no_spikes_units)
    kept_unit_ids = analyzer_removed.unit_ids

    curation_dict['unit_ids'] = list(kept_unit_ids)

    new_manual_labels = []
    for manual_labels in curation_dict['manual_labels']:
        if manual_labels['unit_id'] in kept_unit_ids:
            new_manual_labels.append(manual_labels)

    curation_dict['manual_labels'] = new_manual_labels

    new_removed = []
    for removed_unit_id in curation_dict['removed']:
        if removed_unit_id in kept_unit_ids:
            new_removed.append(removed_unit_id)

    curation_dict['removed'] = new_removed

    wolf_layout = dict(
        zone1=['curation'],
        zone2=['unitlist', 'merge'],
        zone3=['spikeamplitude'],
        zone4=[],
        zone5=['spikerate'],
        zone6=['probe'],
        zone7=['waveform'],
        zone8=['correlogram', 'metrics', 'mainsettings'],
    )

    user_settings = {
        "waveform": {
            "overlap": False,
            "plot_selected_spike": False,
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
    )


if __name__ == '__main__':
    main()
