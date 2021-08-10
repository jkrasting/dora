import base64
import glob
import io
from operator import itemgetter
import os
import traceback

import om4labs
from flask import render_template
from flask import request
from flask import send_file

from app import app
from .Experiment import Experiment

from .frepptools import Filegroup, in_daterange, optimize_filegroup_selection


def base64it(imgbuf):
    """Converts in-memory PNG image to inlined ASCII format

    Parameters
    ----------
    imgbuf : io.BytesIO
        Binary memory buffer cotaining PNG image

    Returns
    -------
    str
        Base64 representation of the image
    """
    imgbuf.seek(0)
    uri = "data:image/png;base64," + base64.b64encode(imgbuf.getvalue()).decode(
        "utf-8"
    ).replace("\n", "")
    return uri


class Diagnostic:
    """Container class for an OM4labs diagnostic"""

    def __init__(self, name, component, pptype="av", varlist=[]):
        """Initalize an OM4Labs diagnostic

        Parameters
        ----------
        name : str
            Diagnostic name
        component : str
            Post-processing component
        pptype : str, optional
            Post-processing stream to use, by default "av"
        """
        self.name = name
        self.name = self.name.replace("_z", "").replace("_rho", "")
        # Intialize and empty dictionary of options pertaining to the
        # requested diagnostic
        self.args = om4labs.diags.__dict__[self.name].parse(template=True)
        # Tell OM4Labs where to find the observational data
        self.args["platform"] = os.environ["OM4LABS_PLATFORM"]
        # Tell OM4Labs we want streaming image buffers back
        self.args["format"] = "stream"
        # Remove any cases where a diagnostic defines a default model
        # configuration and rely solely on the experiment's static file
        self.args["config"] = None
        # Assign component
        self.component = component
        # Assign pp type
        self.pptype = pptype
        # Assign variable list
        self.varlist = [varlist] if not isinstance(varlist, list) else varlist

    def _find_files(self):
        """Resolves paths to post-processing files

        Returns
        -------
        list
            List of files
        """
        ppdir = self.args["ppdir"][0] + self.component
        ppdir = f"{ppdir}/{self.pptype}"
        ncfiles = glob.glob(f"{ppdir}/**/*.nc", recursive=True)
        assert len(ncfiles) > 0, f"No files found in {ppdir}."
        ncfiles = [x for x in ncfiles if in_daterange(x, self.startyr, self.endyr)]
        ncfiles = optimize_filegroup_selection(ncfiles, self.startyr, self.endyr)
        if len(self.varlist) > 0:
            varlist = [f".{x}." for x in self.varlist]
            ncfiles = [x for x in ncfiles if any(var in x for var in varlist)]
            print(ncfiles)
        return ncfiles

    def update_component(self):
        """Use downsampled `_d2` output if available"""
        ppdir = self.args["ppdir"][0]
        _component1 = self.component + "_d2"
        _component2 = self.component.replace("_1x1deg", "_d2_1x1deg")
        if os.path.exists(ppdir + _component1):
            self.component = _component1
        elif os.path.exists(ppdir + _component2):
            self.component = _component2

    def resolve_files(self, ppdir, label, startyr, endyr, downsample=True):
        """Resolves what post-processing files to use

        Parameters
        ----------
        ppdir : str, path-like
            Path to post-processing directory
        label : str
            Experiment name
        startyr : int
            Start year
        endyr : int
            End year

        Returns
        -------
        Diagnostic
            Updated Diagnostic object with paths
        """

        try:
            # set name and post-processing dir
            self.args["label"] = label
            self.args["ppdir"] = [ppdir]

            # determine input files
            exclude_list = ["section_transports"]
            if self.name not in exclude_list:
                # look for _d2 files
                if downsample:
                    self.update_component()
                # determine the input files
                self.startyr = startyr
                self.endyr = endyr
                self.args["infile"] = self._find_files()
                # get the static file
                self.args[
                    "static"
                ] = f"{ppdir}/{self.component}/{self.component}.static.nc"
                self.args["topog"] = self.args["static"]
            else:
                self.args["infile"] = []

            self.success = True

        except Exception as e:
            self.error = traceback.format_exc()
            self.files = []
            self.figures = []
            self.success = False

        return self

    def run(self):
        """Runs the OM4Labs diagnostic

        Returns
        -------
        Diagnostic
            Updated diagnostic object with results
        """
        try:
            # run the diagnostic
            results = om4labs.diags.__dict__[self.name].run(self.args)

            # some diagnostics may return images and a file, separate them here
            if isinstance(results, tuple):
                self.files = results[1]
                self.figures = results[0]
            else:
                self.files = []
                self.figures = results

            self.figures = [base64it(x) for x in self.figures]

        except Exception as e:
            self.error = traceback.format_exc()
            self.files = []
            self.figures = []
            self.success = False

        return self


@app.route("/analysis/om4labs", methods=["GET"])
def om4labs_start():
    """Flask route for calling OM4Labs

    Returns
    -------
    Jinja template name and variables for rendering
    """

    # Get the experiment ID number from the URL or provide user with
    # a form to enter a post-processing path directly
    idnum = request.args.get("id")
    if idnum is None:
        return render_template("om4labs-splash.html")

    # Fetch an Experiment object that houses all of the
    # experiment metadata
    experiment = Experiment(idnum)

    # Make sure the experiment is valid
    if experiment.validate_path("pathPP") is False:
        return render_template(
            "page-500.html", msg=f"{idnum} is not a valid experiment or path."
        )

    # Get the requested analysis from the URL or provide user with
    # a menu of available diagnostics in OM4Labs
    analysis = request.args.getlist("analysis")
    if analysis == []:
        year_range = experiment.year_range()
        avail_diags = [x for x in dir(om4labs.diags) if not x.startswith("__")]
        exclude = ["avail", "generic"]
        avail_diags = [x for x in avail_diags if not any(diag in x for diag in exclude)]
        avail_diags = [
            (diag, eval(f"om4labs.diags.{diag}.__description__"))
            for diag in avail_diags
        ]
        moc_diags = [x for x in avail_diags if x[0] == "moc"]
        avail_diags = [x for x in avail_diags if x[0] != "moc"]
        moc_diags = [
            (moc_diags[0][0] + "_rho", moc_diags[0][1]),
            (moc_diags[0][0] + "_z", moc_diags[0][1]),
        ]

        avail_diags = sorted(avail_diags + moc_diags)

        return render_template(
            "om4labs-start.html",
            avail_diags=avail_diags,
            idnum=idnum,
            experiment=experiment,
            year_range=year_range,
        )

    # get the start and end years for the analysis
    # (rely on browser to make sure user enters values)
    startyr = int(request.args.get("startyr"))
    endyr = int(request.args.get("endyr"))

    # default directories
    default_dirs = {
        "enso": ("ocean_monthly_1x1deg", "ts", ["tos"]),
        "heat_transport": ("ocean_monthly", "av", []),
        "moc_z": ("ocean_annual_z", "av", []),
        "moc_rho": ("ocean_annual_rho2", "av", []),
        "seaice": ("ice_1x1deg", "av", []),
        "section_transports": (None, None, []),
        "so_yz_annual_bias_1x1deg": ("ocean_annual_z_1x1deg", "av", []),
        "sss_annual_bias_1x1deg": ("ocean_annual_z_1x1deg", "av", []),
        "sst_annual_bias_1x1deg": ("ocean_annual_z_1x1deg", "av", []),
        "thetao_yz_annual_bias_1x1deg": ("ocean_annual_z_1x1deg", "av", []),
    }

    # Create a Diagnostic object for each requested analysis
    diags = [
        Diagnostic(
            x, default_dirs[x][0], pptype=default_dirs[x][1], varlist=default_dirs[x][2]
        )
        for x in analysis
    ]

    # Resolve the needed files for each diagostic
    downsample = True if request.args.get("downsample") == "True" else False
    diags = [
        x.resolve_files(
            experiment.pathPP, experiment.expName, startyr, endyr, downsample=downsample
        )
        for x in diags
    ]

    # Separate into those that passed and failed file resolution
    passed = [x for x in diags if x.success is True]
    failed = [x for x in diags if x.success is False]

    # See if the user acknowleged the need to pre-dmget the files
    validated = request.args.get("validated")

    # Handle special case when section transports do not need to be validated
    validated = (
        "True"
        if (validated is None and analysis == ["section_transports"])
        else validated
    )

    # If the user has *not* validated the files, display a list
    # of files that the user should dmget on their own
    if validated is None:
        infiles = [x.args["infile"] for x in passed]
        infiles = [x for sublist in infiles for x in sublist]
        infiles = [x.replace(experiment.pathPP, "") for x in infiles]

    elif validated == "True":
        # set infiles to an empty list - Jinja template will see this
        # and not display the dmget card
        infiles = []

        # carry over diagnostics that failed the file resolution,
        # do not attempt to run them
        failed_resolve = failed

        # *** run the diagnostics ****
        diags = [x.run() for x in diags if x.success is True]

        # separate into those that passed and those that failed
        passed = [x for x in diags if x.success is True]
        failed = [x for x in diags if x.success is False]
        failed = failed + failed_resolve

    download_flag = False
    return render_template(
        "om4labs-results.html",
        args=request.args,
        analysis=analysis,
        infiles=infiles,
        experiment=experiment,
        download_flag=download_flag,
        passed=passed,
        failed=failed,
    )
