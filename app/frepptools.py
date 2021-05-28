""" Collection of tools for working with frepp-generated output """

import glob
import os
from operator import attrgetter


def daterange(fname):
    """Extracts a tuple of start and endy years from a frepp-
    generated post-processing file

    Parameters
    ----------
    fname : str
        File name string

    Returns
    -------
    tuple
        start year, end year
    """
    fname = fname.split(".")[1]
    return tuple([int(x) for x in fname.split("-")])


def in_daterange(fname, startyr, endyr):
    """Logical test if file is in specified date range

    Parameters
    ----------
    fname : str
        File name string
    startyr : int
        Start year
    endyr : int
        End year

    Returns
    -------
    bool
        True if in range
    """
    try:
        fname = daterange(os.path.basename(fname))
        if (fname[1] < int(startyr)) or (fname[0] > int(endyr)):
            result = False
        else:
            result = True
    except:
        result = False
    return result


def jsonify_dirtree(dirpath, pptype="av"):
    """Returns a post-processing directory tree

    Parameters
    ----------
    dirpath : str, path-like
        Path to top-level "pp" directory
    pptype : str, optional
        Type of post-processed files to return
        either "av" or "ts", by default "av"

    Returns
    -------
    dict
        Dictionary of files and options to pass to file browser
    """

    filelist = []
    if pptype == "av":
        for component in os.scandir(dirpath):
            if (
                component.name.startswith("ocean") or component.name.startswith("ice")
            ) and component.is_dir():
                for pptype in os.scandir(component):
                    if pptype.name.startswith("av"):
                        for timechunk in os.scandir(pptype):
                            if timechunk.is_dir():
                                for filename in os.scandir(timechunk):
                                    filelist.append(
                                        f"{component.name}/{pptype.name}/{timechunk.name}/{filename.name}"
                                    )

    elif pptype == "ts":
        for component in os.scandir(dirpath):
            if (
                component.name.startswith("ocean") or component.name.startswith("ice")
            ) and component.is_dir():
                for pptype in os.scandir(component):
                    if pptype.name.startswith("ts"):
                        for freq in os.scandir(pptype):
                            if freq.is_dir():
                                for timechunk in os.scandir(freq):
                                    if timechunk.is_dir():
                                        for filename in os.scandir(timechunk):
                                            filelist.append(
                                                f"{component.name}/{pptype.name}/{freq.name}/{timechunk.name}/{filename.name}"
                                            )

    filelist = sorted(filelist)
    filesplit = sorted([x.split("/") for x in filelist])
    dirs = sorted(list(set([str("/").join(x[0:3]) for x in filesplit])))

    filedict = {
        "id": "",
        "text": "pp",
        "icon": "jstree-folder",
        "state": {"opened": "true"},
        "children": [
            {
                "id": "",
                "text": directory,
                "icon": "jstree-folder",
                "children": [
                    {
                        "id": x,
                        "text": x.replace(f"{directory}/", ""),
                        "icon": "jstree-file",
                    }
                    for x in filelist
                    if x.startswith(directory)
                ],
            }
            for directory in dirs
        ],
    }
    return filedict


def list_components(ppdir, exclude=None):
    """Generates a list of components in a top-level /pp directory

    Parameters
    ----------
    ppdir : str, path-like
        Full path to a post-processing directory
    exclude : str or list, optional
        Additional directories to ignore, by default None

    Yields
    -------
    generator
        List of directories
    """
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


def optimize_filegroup_selection(ncfiles, startyr, endyr):
    """Determines which set of filegroups archieves the best overlap
    of the date range with the fewest number of files

    Parameters
    ----------
    ncfiles : list
        List of NetCDF files
    startyr : int
        Starting year
    endyr : end
        Ending year

    Returns
    -------
    list
        List of optimized files
    """
    ncfiles = [tuple(os.path.split(x)) for x in ncfiles]
    groups = {}
    for x in ncfiles:
        if x[0] not in groups.keys():
            groups[x[0]] = [x[1]]
        else:
            groups[x[0]].append(x[1])

    groups = [Filegroup(k, v) for k, v in groups.items()]
    groups = [x.compare(startyr, endyr) for x in groups]
    minval = min(groups, key=attrgetter("mismatched")).mismatched
    groups = [x for x in groups if x.mismatched == minval]

    if len(groups) >= 1:
        groups = min(groups, key=attrgetter("nfiles"))
        assert groups.monotonic, (
            "Non-monotonic file group encountered. "
            + "There are likely gaps in the post-processing that need to be fixed."
        )
    else:
        raise ValueError("Unable to find suitable date range")

    return groups.paths()


class Filegroup:
    """Group of frepp-generated postprocessing files"""

    def __init__(self, rootpath, filelist):
        """Initialized a Filegroup object

        Parameters
        ----------
        rootpath : str
            Path to directory containing frepp files
        filelist : list
            List of files in the directory
        """

        assert isinstance(filelist, list), "A list must be provided"

        # setup pp directory path and get number of files
        self.rootpath = rootpath
        self.filelist = filelist
        self.nfiles = len(filelist)

        # determine the range of years in the file group
        ranges = [daterange(x) for x in self.filelist]
        span = [list(range(x[0], x[1] + 1)) for x in ranges]
        ranges = [x for sublist in ranges for x in sublist]
        self.span = sorted([x for sublist in span for x in sublist])
        self.range = (min(ranges), max(ranges))
        gap_len = len(set(range(self.range[0], self.range[1])) - set(self.span))
        self.monotonic = True if (gap_len == 0) else False

    def compare(self, startyr, endyr):
        """Compares Filegroup against a specified range of years

        Parameters
        ----------
        startyr : int
            Start year
        endyr : int
            End year

        Returns
        -------
        Filegroup
            Updated Filegroup with the number of mismatched files
        """
        local_set = set(range(self.range[0], self.range[1]))
        expected_set = set(range(int(startyr), int(endyr)))
        self.mismatched = max(
            len(local_set - expected_set), len(expected_set - local_set)
        )

        return self

    def paths(self):
        """Returns a list of resolved paths"""
        return sorted([f"{self.rootpath}/{x}" for x in self.filelist])


class Componentgroup:
    """ Object describing a frepp-generated post-processing component directory """

    def __init__(self, ppdir, component, experiment=None, pptype="av"):
        """Intialized a Component group object

        Parameters
        ----------
        ppdir : str, path-like
            Top-level post-processing directory
        component : str
            Name of component
        experiment : Experiment, optional
            Experiment object, by default None
        pptype : str, optional
            Either "av" or "ts" (not supported - yet), by default "av"
        """
        self.ppdir = ppdir
        self.component = component
        self.pptype = pptype
        self.experiment = experiment

    def reconstitute_files(self):
        result = []
        for grp in self.filegroups:
            _ = grp.paths()
            result = result + _ if _ is not None else result
        result = [f"{self.ppdir}{x}" for x in result]
        return result

    def resolve_files(self):
        """Updates the Componentgroup object with Filegroup objects

        Returns
        -------
        Componentgroup
            Updated object with filegroups attribute
        """
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

    def exclude_files(self, filelist):
        for grp in self.filegroups:
            grp.filelist = [x for x in grp.filelist if x in filelist]
        return self


def compare_compgroups(comp1, comp2):
    """Updates the Componentgroup objects with the union of both objects

    Parameters
    ----------
    comp1 : Componentgroup
        First group
    comp2 : Componentgroup
        Second group
    """
    filegroups1 = set([x.rootpath for x in comp1.filegroups])
    filegroups2 = set([x.rootpath for x in comp2.filegroups])
    filegroups = list(filegroups1.intersection(filegroups2))
    comp1.filegroups = [x for x in comp1.filegroups if x.rootpath in filegroups]
    comp2.filegroups = [x for x in comp2.filegroups if x.rootpath in filegroups]

    for grp in [filegroups[0]]:
        filelist1 = set([x.filelist for x in comp1.filegroups if x.rootpath == grp][0])
        filelist2 = set([x.filelist for x in comp2.filegroups if x.rootpath == grp][0])
        filelist = sorted(list(filelist1.intersection(filelist2)))

        for x in comp1.filegroups:
            x.filelist = filelist if x.rootpath == grp else sorted(x.filelist)
        for x in comp2.filegroups:
            x.filelist = filelist if x.rootpath == grp else sorted(x.filelist)
