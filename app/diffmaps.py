from app.project_util import list_projects
import base64
import glob
import io
from operator import itemgetter
from operator import attrgetter
import os
import traceback

import om4labs
from flask import render_template
from flask import request
from flask import send_file

from app import app
from .Experiment import Experiment


def list_components(ppdir, exclude=None):
    exclude_list = [".dec", ".checkpoint"]
    if exclude is not None:
        if isinstance(exclude, str):
            exclude = [exclude]
        else:
            assert isinstance(exclude, list), "exclude option must be str or list"
        exclude_list = exclude_list + exclude
    for entry in os.scandir(ppdir):
        if entry.is_dir() and entry.name not in exclude_list:
            yield (entry.name)


@app.route("/analysis/diffmaps", methods=["GET"])
def diffmaps_start():
    """Flask route model-model comparison maps

    Returns
    -------
    Jinja template name and variables for rendering
    """

    # Get the experiment ID number from the URL or provide user with
    # a form to enter a post-processing path directly
    idnum = request.args.getlist("id")
    if len(idnum) != 2:
        return render_template("diffmaps-splash.html")

    # Get postprocessing directories for each experiment
    experiments = [Experiment(x) for x in idnum]

    component = request.args.get("component")

    if component is None:
        # list components
        ppdirs = [x.pathPP for x in experiments]
        components = [set(list_components(x)) for x in ppdirs]
        components = list(components[0].intersection(components[1]))
        components = sorted(components)
        # filter out passage flow components
        components = [x for x in components if not x.split("_")[1][0].isupper()]
        return render_template(
            "diffmaps-selector.html",
            component=component,
            components=components,
            idnum=idnum,
        )

    common = True if request.args.get("common") is not None else False

    def daterange(fname):
        fname = fname.split(".")[1]
        return tuple([int(x) for x in fname.split("-")])

    def in_daterange(fname, startyr, endyr):
        try:
            fname = daterange(os.path.basename(fname))
            if (fname[1] < int(startyr)) or (fname[0] > int(endyr)):
                result = False
            else:
                result = True
        except:
            result = False
        return result

    class Filegroup:
        def __init__(self, rootpath, filelist):

            assert isinstance(filelist, list), "A list must be provided"

            # setup pp directory path and get number of files
            self.rootpath = rootpath
            self.filelist = filelist
            self.nfiles = len(filelist)
            self.paths = sorted([f"{rootpath}/{x}" for x in filelist])

            # determine the range of years in the file group
            ranges = [daterange(x) for x in self.filelist]
            span = [list(range(x[0], x[1] + 1)) for x in ranges]
            ranges = [x for sublist in ranges for x in sublist]
            self.span = sorted([x for sublist in span for x in sublist])
            self.range = (min(ranges), max(ranges))
            gap_len = len(set(range(self.range[0], self.range[1])) - set(self.span))
            self.monotonic = True if (gap_len == 0) else False

        def compare(self, startyr, endyr):
            local_set = set(range(self.range[0], self.range[1]))
            expected_set = set(range(int(startyr), int(endyr)))
            self.mismatched = max(
                len(local_set - expected_set), len(expected_set - local_set)
            )

            return self

    class Componentgroup:
        def __init__(self, ppdir, component, experiment=None, pptype="av"):
            self.ppdir = ppdir
            self.component = component
            self.pptype = pptype
            self.experiment = experiment

        def resolve_files(self):
            ppdir = f"{self.ppdir}{self.component}"
            ppdir = f"{ppdir}/{self.pptype}"
            ncfiles = glob.glob(f"{ppdir}/**/*.nc", recursive=True)
            ncfiles = [tuple(os.path.split(x)) for x in ncfiles]
            groups = {}
            for x in ncfiles:
                if x[0] not in groups.keys():
                    groups[x[0]] = [x[1]]
                else:
                    groups[x[0]].append(x[1])
            self.filegroups = [
                Filegroup(k.replace(self.ppdir, ""), v) for k, v in groups.items()
            ]
            return self

    def compare_compgroups(comp1, comp2):
        filegroups1 = set([x.rootpath for x in comp1.filegroups])
        filegroups2 = set([x.rootpath for x in comp2.filegroups])
        filegroups = list(filegroups1.intersection(filegroups2))
        comp1.filegroups = [x for x in comp1.filegroups if x.rootpath in filegroups]
        comp2.filegroups = [x for x in comp2.filegroups if x.rootpath in filegroups]

        for grp in [filegroups[0]]:
            filelist1 = set(
                [x.filelist for x in comp1.filegroups if x.rootpath == grp][0]
            )
            filelist2 = set(
                [x.filelist for x in comp2.filegroups if x.rootpath == grp][0]
            )
            filelist = sorted(list(filelist1.intersection(filelist2)))

            for x in comp1.filegroups:
                x.filelist = filelist if x.rootpath == grp else sorted(x.filelist)
            for x in comp2.filegroups:
                x.filelist = filelist if x.rootpath == grp else sorted(x.filelist)

    groups = [Componentgroup(x.pathPP, component, experiment=x) for x in experiments]
    groups = [x.resolve_files() for x in groups]

    if common:
        compare_compgroups(groups[0], groups[1])

    file1 = request.args.getlist("file1")
    file2 = request.args.getlist("file2")

    if len(file1) == 0:
        return render_template(
            "diffmaps-selector.html",
            component=component,
            common=common,
            groups=groups,
            idnum=idnum,
        )

    return ""


# def jsonify_dirtree(dirpath, pptype="av"):
#     """Returns a post-processing directory tree
#
#     Parameters
#     ----------
#     dirpath : str, path-like
#         Path to top-level "pp" directory
#     pptype : str, optional
#         Type of post-processed files to return
#         either "av" or "ts", by default "av"
#
#     Returns
#     -------
#     dict
#         Dictionary of files and options to pass to file browser
#     """
#
#     filelist = []
#     if pptype == "av":
#         for component in os.scandir(dirpath):
#             if (
#                 component.name.startswith("ocean") or component.name.startswith("ice")
#             ) and component.is_dir():
#                 for pptype in os.scandir(component):
#                     if pptype.name.startswith("av"):
#                         for timechunk in os.scandir(pptype):
#                             if timechunk.is_dir():
#                                 for filename in os.scandir(timechunk):
#                                     filelist.append(
#                                         f"{component.name}/{pptype.name}/{timechunk.name}/{filename.name}"
#                                     )
#
#     elif pptype == "ts":
#         for component in os.scandir(dirpath):
#             if (
#                 component.name.startswith("ocean") or component.name.startswith("ice")
#             ) and component.is_dir():
#                 for pptype in os.scandir(component):
#                     if pptype.name.startswith("ts"):
#                         for freq in os.scandir(pptype):
#                             if freq.is_dir():
#                                 for timechunk in os.scandir(freq):
#                                     if timechunk.is_dir():
#                                         for filename in os.scandir(timechunk):
#                                             filelist.append(
#                                                 f"{component.name}/{pptype.name}/{freq.name}/{timechunk.name}/{filename.name}"
#                                             )
#
#     filelist = sorted(filelist)
#     filesplit = sorted([x.split("/") for x in filelist])
#     dirs = sorted(list(set([str("/").join(x[0:3]) for x in filesplit])))
#
#     filedict = {
#         "id": "",
#         "text": "pp",
#         "icon": "jstree-folder",
#         "state": {"opened": "true"},
#         "children": [
#             {
#                 "id": "",
#                 "text": directory,
#                 "icon": "jstree-folder",
#                 "children": [
#                     {
#                         "id": x,
#                         "text": x.replace(f"{directory}/", ""),
#                         "icon": "jstree-file",
#                     }
#                     for x in filelist
#                     if x.startswith(directory)
#                 ],
#             }
#             for directory in dirs
#         ],
#     }
#     return filedict
#
#
# def base64it(imgbuf):
#     """Converts in-memory PNG image to inlined ASCII format
#
#     Parameters
#     ----------
#     imgbuf : io.BytesIO
#         Binary memory buffer cotaining PNG image
#
#     Returns
#     -------
#     str
#         Base64 representation of the image
#     """
#     imgbuf.seek(0)
#     uri = "data:image/png;base64," + base64.b64encode(imgbuf.getvalue()).decode(
#         "utf-8"
#     ).replace("\n", "")
#     return uri
#
#
# @app.route("/analysis/om4labs", methods=["GET"])
# def om4labs_start():
#     """Flask route for calling OM4Labs
#
#     Returns
#     -------
#     Jinja template name and variables for rendering
#     """
#
#     # Get the experiment ID number from the URL or provide user with
#     # a form to enter a post-processing path directly
#     idnum = request.args.get("id")
#     if idnum is None:
#         return render_template("om4labs-splash.html")
#
#     # Fetch an Experiment object that houses all of the
#     # experiment metadata
#     experiment = Experiment(idnum)
#
#     # Get the requested analysis from the URL or provide user with
#     # a menu of available diagnostics in OM4Labs
#     analysis = request.args.getlist("analysis")
#     if analysis == []:
#         avail_diags = [x for x in dir(om4labs.diags) if not x.startswith("__")]
#         exclude = ["avail", "generic"]
#         avail_diags = [x for x in avail_diags if not any(diag in x for diag in exclude)]
#         avail_diags = [
#             (diag, eval(f"om4labs.diags.{diag}.__description__"))
#             for diag in avail_diags
#         ]
#         return render_template(
#             "om4labs-start.html",
#             avail_diags=avail_diags,
#             idnum=idnum,
#             experiment=experiment,
#         )
#
#     # get the start and end years for the analysis
#     # (rely on browser to make sure user enters values)
#     startyr = int(request.args.get("startyr"))
#     endyr = int(request.args.get("endyr"))
#
#     # default directories
#     default_dirs = {
#         "heat_transport": "ocean_monthly",
#         "moc": "ocean_annual_z",
#         "seaice": "ice_1x1deg",
#         "section_transports": None,
#         "so_yz_annual_bias_1x1deg": "ocean_annual_z_1x1deg",
#         "sss_annual_bias_1x1deg": "ocean_annual_z_1x1deg",
#         "sst_annual_bias_1x1deg": "ocean_annual_z_1x1deg",
#         "thetao_yz_annual_bias_1x1deg": "ocean_annual_z_1x1deg",
#     }
#
#     def daterange(fname):
#         fname = fname.split(".")[1]
#         return tuple([int(x) for x in fname.split("-")])
#
#     def in_daterange(fname, startyr, endyr):
#         try:
#             fname = daterange(os.path.basename(fname))
#             if (fname[1] < int(startyr)) or (fname[0] > int(endyr)):
#                 result = False
#             else:
#                 result = True
#         except:
#             result = False
#         return result
#
#     class Filegroup:
#         def __init__(self, rootpath, filelist):
#
#             assert isinstance(filelist, list), "A list must be provided"
#
#             # setup pp directory path and get number of files
#             self.rootpath = rootpath
#             self.filelist = filelist
#             self.nfiles = len(filelist)
#             self.paths = sorted([f"{rootpath}/{x}" for x in filelist])
#
#             # determine the range of years in the file group
#             ranges = [daterange(x) for x in self.filelist]
#             span = [list(range(x[0], x[1] + 1)) for x in ranges]
#             ranges = [x for sublist in ranges for x in sublist]
#             self.span = sorted([x for sublist in span for x in sublist])
#             self.range = (min(ranges), max(ranges))
#             gap_len = len(set(range(self.range[0], self.range[1])) - set(self.span))
#             self.monotonic = True if (gap_len == 0) else False
#
#         def compare(self, startyr, endyr):
#             local_set = set(range(self.range[0], self.range[1]))
#             expected_set = set(range(int(startyr), int(endyr)))
#             self.mismatched = max(
#                 len(local_set - expected_set), len(expected_set - local_set)
#             )
#
#             return self
#
#         def __len__(self):
#             return len(self.filelist)
#
#     def optimize_selection(ncfiles, startyr, endyr):
#         ncfiles = [tuple(os.path.split(x)) for x in ncfiles]
#         groups = {}
#         for x in ncfiles:
#             if x[0] not in groups.keys():
#                 groups[x[0]] = [x[1]]
#             else:
#                 groups[x[0]].append(x[1])
#
#         groups = [Filegroup(k, v) for k, v in groups.items()]
#         groups = [x.compare(startyr, endyr) for x in groups]
#         minval = min(groups, key=attrgetter("mismatched")).mismatched
#         groups = [x for x in groups if x.mismatched == minval]
#
#         if len(groups) >= 1:
#             groups = min(groups, key=attrgetter("nfiles"))
#             assert groups.monotonic, (
#                 "Non-monotonic file group encountered. "
#                 + "There are likely gaps in the post-processing that need to be fixed."
#             )
#         else:
#             raise ValueError("Unable to find suitable date range")
#
#         return groups.paths
#
#     class Diagnostic:
#         """Container class for an OM4labs diagnostic"""
#
#         def __init__(self, name, component, pptype="av"):
#             self.name = name
#             # Intialize and empty dictionary of options pertaining to the
#             # requested diagnostic
#             self.args = om4labs.diags.__dict__[name].parse(template=True)
#             # Tell OM4Labs where to find the observational data
#             self.args["platform"] = os.environ["OM4LABS_PLATFORM"]
#             # Tell OM4Labs we want streaming image buffers back
#             self.args["format"] = "stream"
#             # Remove any cases where a diagnostic defines a default model
#             # configuration and rely solely on the experiment's static file
#             self.args["config"] = None
#             # Assign component
#             self.component = component
#             # Assign pp type
#             self.pptype = pptype
#
#         def _find_files(self):
#             ppdir = self.args["ppdir"][0] + self.component
#             ppdir = f"{ppdir}/{self.pptype}"
#             ncfiles = glob.glob(f"{ppdir}/**/*.nc", recursive=True)
#             assert len(ncfiles) > 0, f"No files found in {ppdir}."
#             ncfiles = [x for x in ncfiles if in_daterange(x, self.startyr, self.endyr)]
#             ncfiles = optimize_selection(ncfiles, self.startyr, self.endyr)
#             return ncfiles
#
#         def update_component(self):
#             ppdir = self.args["ppdir"][0]
#             _component1 = self.component + "_d2"
#             _component2 = self.component.replace("_1x1deg", "_d2_1x1deg")
#             if os.path.exists(ppdir + _component1):
#                 self.component = _component1
#             elif os.path.exists(ppdir + _component2):
#                 self.component = _component2
#
#         def resolve_files(self, ppdir, label, startyr, endyr):
#
#             try:
#                 # set name and post-processing dir
#                 self.args["label"] = label
#                 self.args["ppdir"] = [ppdir]
#
#                 # determine input files
#                 exclude_list = ["section_transports"]
#                 if self.name not in exclude_list:
#                     # look for _d2 files
#                     self.update_component()
#                     # determine the input files
#                     self.startyr = startyr
#                     self.endyr = endyr
#                     self.args["infile"] = self._find_files()
#                     # get the static file
#                     self.args[
#                         "static"
#                     ] = f"{ppdir}/{self.component}/{self.component}.static.nc"
#                     self.args["topog"] = self.args["static"]
#                 else:
#                     self.args["infile"] = []
#
#                 self.success = True
#
#             except Exception as e:
#                 self.error = traceback.format_exc()
#                 self.files = []
#                 self.figures = []
#                 self.success = False
#
#             return self
#
#         def run(self):
#
#             try:
#                 # run the diagnostic
#                 results = om4labs.diags.__dict__[self.name].run(self.args)
#
#                 # some diagnostics may return images and a file, separate them here
#                 if isinstance(results, tuple):
#                     self.files = results[1]
#                     self.figures = results[0]
#                 else:
#                     self.files = []
#                     self.figures = results
#
#                 self.figures = [base64it(x) for x in self.figures]
#
#             except Exception as e:
#                 self.error = traceback.format_exc()
#                 self.files = []
#                 self.figures = []
#                 self.success = False
#
#             return self
#
#     diags = [Diagnostic(x, default_dirs[x]) for x in analysis]
#
#     diags = [
#         x.resolve_files(experiment.pathPP, experiment.expName, startyr, endyr)
#         for x in diags
#     ]
#     passed = [x for x in diags if x.success is True]
#     failed = [x for x in diags if x.success is False]
#
#     validated = request.args.get("validated")
#
#     if validated is None:
#         infiles = [x.args["infile"] for x in passed]
#         infiles = [x for sublist in infiles for x in sublist]
#         infiles = [x.replace(experiment.pathPP, "") for x in infiles]
#     elif validated == "True":
#         infiles = []
#
#         failed_resolve = failed
#
#         diags = [x.run() for x in diags if x.success is True]
#
#         passed = [x for x in diags if x.success is True]
#         failed = [x for x in diags if x.success is False]
#         failed = failed + failed_resolve
#
#     # Convert image buffers to in-lined images
#     download_flag = False
#     return render_template(
#         "om4labs-results.html",
#         args=request.args,
#         analysis=analysis,
#         infiles=infiles,
#         experiment=experiment,
#         download_flag=download_flag,
#         passed=passed,
#         failed=failed,
#     )
#
