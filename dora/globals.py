from dora import dora
from .projects import list_projects

model_types = sorted(
    [
        "AM5c96",
        "AM5c384",
        "CM4",
        "OM4",
        "AM4",
        "CM4p5",
        "ESM4p5",
        "ESM4",
        "ESM2G",
        "OM4p5",
        "CM3",
        "LM3",
        "SPEAR",
        "SM4",
        "CMIP6-CM4",
        "LM4",
        "OM4p125",
        "CMIP6-ESM4",
        "C4MIP-ESM4",
    ]
)

cmip6_mips = sorted(
    [
        "AerChemMIP",
        "CDRMIP",
        "C4MIP",
        "CFMIP",
        "DECK",
        "DAMIP",
        "FAFMIP",
        "GMMIP",
        "LUMIP",
        "OMIP",
        "RFMIP",
        "SIMIP",
        "ScenarioMIP",
    ]
)


@dora.context_processor
def get_global_vars():
    return {
        "model_types": model_types,
        "cmip6_mips": cmip6_mips,
        "projects": list_projects(),
        "project_list": [project[1] for project in list_projects()],
    }
