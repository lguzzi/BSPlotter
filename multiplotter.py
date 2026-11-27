from cls.BSParser import BSParser
from cls.BSPlotter import BSPlot1DByTime, multiplot, multiaxes
from cls.MPUtils import MPManager

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--streams", default=1, type=int)
    parser.add_argument(
        "--flavour",
        default="default",
        help="set to 'vdm' if the output formatting is vdm-like (contains the PV cov. matrix)",
    )
    args = parser.parse_args()

    BSParser.DEBUG = args.debug
    bsparser = BSParser(file=args.input, threads=args.streams, flavour=args.flavour)
    bsparser.fetch_timestamps_from_OMS()

    bsplotters = {
        var: BSPlot1DByTime(yvariable=var, ylabel=lab, data=bsparser.beamspot)
        for var, lab in {
            "x": "x [cm]",
            "y": "y [cm]",
            "z": "z [cm]",
            "widthX": "#sigma_x [cm]",
            "widthY": "#sigma_y [cm]",
            "widthZ": "#sigma_z [cm]",
            "dxdz": "correlation x-z",
            "dydz": "correlation y-z",
        }.items()
    }
    multiaxes(
        left=[bsplotters["x"], bsplotters["y"]],
        right=[bsplotters["z"]],
        output=args.output,
    )
    multiaxes(
        left=[bsplotters["widthX"], bsplotters["widthY"]],
        right=[bsplotters["widthZ"]],
        output=args.output,
    )
    multiaxes(
        left=[bsplotters["dxdz"], bsplotters["dydz"]], right=[], output=args.output
    )

    # bsparser.elaborate_runnumbers()
    # bsparser.writeTxtFile(filename=args.output+'/BSFit_formatted.txt')
    # bsplotter = BSPlotterByTime(name=args.output, data=bsparser.beamspot)
    # bsplotter.save(args.output)
