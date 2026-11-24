# BSPlotter

BSPlotter reads beam-spot fit results, enriches them with run, fill, and
lumisection information from the CMS Online Monitoring Service (OMS), and
produces ROOT plots and tabular text output.

## Setup

The project uses Python 3.11 and ROOT. Create the Conda environment from the
checked-in specification:

```bash
mamba env create -n beamspot-old -f env/python3.11.yaml
mamba activate beamspot-old
```

The environment pins ROOT 6.32.2. If you have not cloned the repository with
its submodules, initialize them before running the tools:

```bash
git submodule update --init --recursive
python -m pip install -e ./oms-api-client
```

The OMS API client is provided by the `oms-api-client` submodule. The first
run may require completing the OMS device-authentication flow; the tools need
network access to OMS to retrieve run, fill, and lumisection metadata.

## Command-line tools

All commands require an input fit-result text file and an output directory.
`--flavour` selects the input layout (`default` or `database`), `--streams`
sets the number of parallel OMS-fetch workers (default: `1`), and `--debug`
runs the fetch serially to make debugging easier.

```bash
python plotter_byrun.py \
  --input test/BSFit_Fill11740_BX72.txt \
  --output plots/by-run \
  --flavour default \
  --streams 4
```

| Script | Output |
| --- | --- |
| `plotter_byrun.py` | PDF and PNG plots of beam-spot variables versus fill |
| `plotter_bylumi.py` | PDF and PNG plots versus time, including a plot of failed-fit luminosity |
| `multiplotter.py` | Combined multi-axis plots of position, width, and slope variables versus time |

Use `python <script>.py --help` to see each script's options. The scripts use
fit type `2` for successful fits; `plotter_bylumi.py` also fetches fit types
`0` and `-1` for the failed-fit luminosity plot.

## Input and parsing

`BSParser` supports the standard beam-spot text layout (`default`) and the
database layout (`database`). The checked-in `test/BSFit_Fill11740_BX72.txt`
is an example of the standard format. The parser filters records by fit type
and represents each selected fit with a `(run, first_lumisection,
last_lumisection)` key.

```python
from cls.BSParser import BSParser

parser = BSParser(
    file="test/BSFit_Fill11740_BX72.txt",
    threads=4,
    flavour="default",
    fittype=2,
)
parser.fetch_timestamps_from_OMS()

for (run, lumi_start, lumi_end), fit in parser.beamspot.items():
    print(run, lumi_start, lumi_end, fit["timestamp"], fit["x"])
```

Before `fetch_timestamps_from_OMS()` is called, records contain fit results
only. After it returns, records that could not be matched to OMS data are
omitted; the remaining records also contain time, fill, luminosity, pileup,
and unique run/fill coordinates. Beam-spot widths corrected for the beam
slopes are added as `widthXTrue`, `widthYTrue`, and `widthZTrue`.

The default fit type is `2`. Fit type values follow the status codes in
[BeamFitter.cc](https://github.com/cms-sw/cmssw/blob/master/RecoVertex/BeamSpotProducer/src/BeamFitter.cc#L525-L533)
and
[BeamSpot.h](https://github.com/cms-sw/cmssw/blob/4417f8d1645a31988011de3b45776241ca7708e0/DataFormats/BeamSpot/interface/BeamSpot.h#L24).
Set `BSParser.DEBUG = True` to disable multiprocessing while fetching OMS
data.

## Plotting and text output

The plotting classes live in `cls/BSPlotter.py`. `BSPlot1DByTime`,
`BSPlot1DByRun`, and `BSPlot1DByFill` take a beam-spot mapping, the name of a
record field to plot, and its axis label. Call `save(dirout=...)` to write
both PDF and PNG versions. The `cls` modules also provide ROOT graph, canvas,
line, and text subclasses for consistent plot styling.

`BSParser.writeTabularTxt(dirout)` writes two tab-separated files from the
parsed records: a standard-format table and a primary-vertex (PV) table.
The standard table includes the unrotated laboratory-frame widths and the
slope-corrected transverse widths.
