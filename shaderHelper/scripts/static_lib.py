from contextlib import contextmanager
from maya import cmds
from maya.api import OpenMaya as api2
from PySide2 import QtCore
from functools import partial


# --------------------- Build Mapping Information --------------------- #
# --------------------------------------------------------------------- #


mappingLambert = {
    "diffuse": "base",
    "color": "baseColor",
    "normalCamera": "normalCamera",
    "incandescence": "emissionColor",
    "translucence": "subsurface",
    "transparency": "opacity"
}

mappingBlinn = {
    "diffuse": "base",
    "color": "baseColor",
    "specularRollOff": "specular",
    "specularColor": "specularColor",
    "reflectivity": "coat",
    "reflectedColor": "coatColor",
    "eccentricity": "specularRoughness",
    "normalCamera": "normalCamera",
    "incandescence": "emissionColor",
    "transparency": "opacity",
    "translucence": "subsurface"
}

mappingPhong = {
    "diffuse": "base",
    "color": "baseColor",
    "reflectedColor": "coatColor",
    "specularColor": "specularColor",
    "reflectivity": "coat",
    "normalCamera": "normalCamera",
    "incandescence": "emissionColor",
    "translucence": "subsurface"
}
# -Not tested
mappingMia = {
    "diffuse_weight": "base",
    "diffuse": "baseColor",
    "diffuse_roughness": "diffuseRoughness",
    "refl_color": "specularColor",
    "reflectivity": "specular",
    "refr_ior": "coat_IOR",
    "refr_color": "coatColor",
    "transparency": "transmission",
    "anisotropy_rotation": "anisotropyRotation",
    "cutout_opacity": "opacity"
}
# -Not tested
mappingDielectric = {
    "ior": "IOR",
    "col": "transmittance"
}


def _populate_childAttrs(m):
    """
    Populate map with child attributes like colorR, colorB, colorG.

    Args:
        m ([Dict]): Map which should be populated.

    Returns:
        [Dict]: Changed map.
    """
    for k in m.keys():
        if "color" in k.lower() or k.lower() in _RGB:
            for c in "RGB":
                m["%s%s" % (k, c)] = m[k]+c

        elif k.lower() in _XYZ:
            for c in "XYZ":
                m["%s%s" % (k, c)] = m[k]+c
    return m


# -attributes in these maps will get child attributes with there corrosponding aliases
_RGB = ("transparency", "incandescence")
_XYZ = ("normalcamera")
# -temp map list
_MAPS = (mappingLambert, mappingBlinn, mappingPhong,
         mappingMia, mappingDielectric)


MAPS = tuple(_populate_childAttrs(m) for m in _MAPS)
LEGALTYPES = ("lambert", "blinn", "phong", "mia_material_x_passes",
              "mia_material_x", "dielectric_material")
LEGALTYPES_MAPS = {typ: maps for typ, maps in zip(LEGALTYPES, MAPS)}


# --------------------- Build QT Interface Information ---------------- #
# --------------------------------------------------------------------- #

CONVERT_TO = {"aiStandardSurface": "ai"}

COLORSPACES = partial(cmds.colorManagementPrefs, q=True, inputSpaceNames=True)


# --------------------- Helper Variables ------------------------------ #
# --------------------------------------------------------------------- #

FROM_TOOL = True

AIDEFAULT = "aiStandardSurface"

NON_DELETEABLES = ("lambert1", "particleCloud1",
                   "shaderGlow1", "standardSurface1")

APIENUM_strToNum = vars(api2.MFn)
APIENUM_numToStr = {v: k for k, v in APIENUM_strToNum.items()}
