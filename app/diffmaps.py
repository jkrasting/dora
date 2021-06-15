from flask.globals import g
from app.project_util import list_projects
import base64
import xcompare
import glob
import io
import cartopy.crs as ccrs

from operator import itemgetter
from operator import attrgetter
import os
import traceback
import xarray as xr

import om4labs
from flask import render_template
from flask import request
from flask import send_file

from app import app
from .Experiment import Experiment

from .frepptools import list_components, Componentgroup, compare_compgroups

import matplotlib.pyplot as plt


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


def get_vertical_coord(dset):
    varlist = list(dset.variables)

    # get coord-names
    varcoords = [list(dset[x].coords) for x in varlist]
    varcoords = [x for sublist in varcoords for x in sublist]
    varcoords = list(set(varcoords))
    varcoords = varcoords

    # known vertical coordinates
    known_vert_coords = [
        "z_l",
        "z_i",
        "depth",
        "pfull",
        "phalf",
        "level",
        "plev",
        "lev",
    ]
    varcoords = [x for x in varcoords if x in known_vert_coords]

    # sort the coords in the file in order of preference and
    # and take the first one
    if len(varcoords) > 0:
        varcoords = sorted(varcoords, key=known_vert_coords.index)
        zdim = varcoords[0]
        zdim = (varcoords[0], [str(x) for x in dset[zdim].values])
    else:
        zdim = None

    return zdim


def io_save(fig):
    imgbuf = io.BytesIO()
    fig.savefig(imgbuf, format="png", bbox_inches="tight")
    return imgbuf


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

    # Get an Experiment object for each idnumber
    experiments = [Experiment(x) for x in idnum]

    # Get the requested component and send user to the file selector
    # if it is not defined
    component = request.args.get("component")
    if component is None:
        # list components
        ppdirs = [x.pathPP for x in experiments]
        components = [set(list_components(x)) for x in ppdirs]
        components = list(components[0].intersection(components[1]))
        components = sorted(components)
        # filter out passage flow components
        single_comps = [x for x in components if not "_" in x]
        components = list(set(components) - set(single_comps))
        components = [x for x in components if not x.split("_")[1][0].isupper()]
        components = sorted(components + single_comps)
        return render_template(
            "diffmaps-selector.html",
            component=component,
            components=components,
            idnum=idnum,
            infiles=None,
            file1=None,
            file2=None,
            varlist=None,
        )

    # Determine if overlapping files is requested
    common = (
        True
        if (request.args.get("common") == "1" or request.args.get("common") == "True")
        else False
    )

    # create a component group object for each experiment and resolve the files
    groups = [Componentgroup(x.pathPP, component, experiment=x) for x in experiments]
    groups = [x.resolve_files() for x in groups]

    # if common times are requested, find overlap between two experiments
    if common:
        compare_compgroups(groups[0], groups[1])

    # get list of files from the command line
    file1 = request.args.getlist("file1")
    file2 = request.args.getlist("file2")

    # if no files are selected, send user to the file seclector
    if len(file1) == 0:
        return render_template(
            "diffmaps-selector.html",
            component=component,
            common=common,
            groups=groups,
            idnum=idnum,
            infiles=None,
            file1=None,
            file2=None,
            varlist=None,
        )

    # if common times requested, use the same filelist for both
    if common:
        file2 = file1

    # weed out files that are not requested
    groups[0] = groups[0].exclude_files(file1)
    groups[1] = groups[1].exclude_files(file2)

    # resolve paths
    infiles = [x.reconstitute_files() for x in groups]
    infiles = [x for sublist in infiles for x in sublist]

    # infer static files
    _ = [infiles.append(x.static) for x in groups]

    # See if the user acknowleged the need to pre-dmget the files
    validated = request.args.get("validated")

    # If the user has *not* validated the files, display a list
    # of files that the user should dmget on their own
    if validated is None:
        return render_template(
            "diffmaps-selector.html",
            component=component,
            common=common,
            groups=groups,
            idnum=idnum,
            file1=file1,
            file2=file2,
            infiles=infiles,
            varlist=None,
        )

    # get a list of variables to plot
    variable = request.args.getlist("variable")

    if len(variable) == 0:
        ds1 = xr.open_dataset(groups[0].reconstitute_files()[0])
        try:
            ds2 = xr.open_dataset(groups[1].reconstitute_files()[0])
        except Exception as e:
            print("flist", groups[1].reconstitute_files(debug=True))
            print(e)
        stdname = lambda x: ds1[x].long_name if "long_name" in ds1[x].attrs else ""
        varlist = set(ds1.variables).intersection(set(ds2.variables))
        varlist = list(varlist - set(ds1.coords))
        # remove bounds
        varlist = [x for x in varlist if not x.endswith("_bnds")]
        # remove frepp time avaerage vars
        varlist = [x for x in varlist if not x.startswith("average_")]
        # identify the vertical coordinate
        zdim = get_vertical_coord(ds1)
        # add in variable long names
        varlist = [(x, stdname(x)) for x in sorted(varlist)]
        # get a list of cartopy projections
        proj = ccrs.__dict__.keys()
        proj = [x for x in proj if x[0].isupper() and x[1].islower()]
        exclude_list = ["Globe", "Projection"]
        proj = sorted([x for x in proj if x not in exclude_list])
        # get a list of colormaps
        cmaps = plt.colormaps()

        return render_template(
            "diffmaps-selector.html",
            component=component,
            common=common,
            groups=groups,
            idnum=idnum,
            file1=file1,
            file2=file2,
            infiles=infiles,
            varlist=varlist,
            zdim=zdim,
            proj=proj,
            cmaps=cmaps,
        )

    # open datasets
    ds1 = xr.open_mfdataset(
        [groups[0].reconstitute_files()] + [groups[0].static],
        use_cftime=True,
        join="override",
    )
    ds2 = xr.open_mfdataset(
        [groups[1].reconstitute_files()] + [groups[1].static],
        use_cftime=True,
        join="override",
    )

    zlev = float(request.args.get("zlev"))
    ds1 = ds1.sel({get_vertical_coord(ds1)[0]: zlev}, method="nearest")
    ds2 = ds2.sel({get_vertical_coord(ds2)[0]: zlev}, method="nearest")

    results = xcompare.compare_datasets(ds1, ds2, varlist=variable, timeavg=True)

    # get requested projection
    projection = request.args.get("projection")
    projection = ccrs.__dict__[projection]()

    # get geographic bounds
    lon_range = (request.args.get("lon0"), request.args.get("lon1"))
    lat_range = (request.args.get("lat0"), request.args.get("lat1"))

    lon_range = tuple(
        None if ((x == "") or (x is None)) else float(x) for x in lon_range
    )
    lat_range = tuple(
        None if ((x == "") or (x is None)) else float(x) for x in lat_range
    )

    lat_range = (
        None if None in lat_range else (float(lat_range[0]), float(lat_range[1]))
    )
    lon_range = (
        None if None in lon_range else (float(lon_range[0]), float(lon_range[1]))
    )

    coastlines = True if request.args.get("coastlines") == "1" else False
    print(coastlines)

    cmap = request.args.get("cmap")

    sigma = 1.5 if request.args.get("sigma") == "" else float(request.args.get("sigma"))
    vmin = None if request.args.get("vmin") == "" else float(request.args.get("vmin"))
    vmax = None if request.args.get("vmax") == "" else float(request.args.get("vmax"))
    diffvmin = (
        None
        if request.args.get("diffvmin") == ""
        else float(request.args.get("diffvmin"))
    )
    diffvmax = (
        None
        if request.args.get("diffvmax") == ""
        else float(request.args.get("diffvmax"))
    )

    figs = [
        (
            x,
            xcompare.plot_three_panel(
                results,
                x,
                projection=projection,
                labels=[experiments[0].expName, experiments[1].expName],
                cmap=cmap,
                vmin=vmin,
                vmax=vmax,
                diffvmin=diffvmin,
                diffvmax=diffvmax,
                lat_range=lat_range,
                lon_range=lon_range,
                coastlines=coastlines,
                sigma=sigma,
            ),
        )
        for x in variable
    ]
    figs = [(x[0], io_save(x[1])) for x in figs]
    figs = [(x[0], base64it(x[1])) for x in figs]

    xr.set_options(display_style="html")
    html_text = results["diff"]._repr_html_()

    return render_template(
        "diffmaps-results.html", ds1=ds1, html_text=html_text, figs=figs
    )
