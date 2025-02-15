# SMPresetStorage.py
from gui.inputmap import *
from d3 import *
from gui.columnlistview import *
import d3script
import json


def initCallback():
    d3script.log("PresetManager3","PresetManager3 Loaded")
    PMPreset.loadPresets()


def applyPreset(preset):
    PMPreset.applyByName(preset)  




        
def sendActiveColorInfo():
    """Open a popup menu with rename options"""

    selectedLayers = d3script.getSelectedLayers()

    if(selectedLayers.len() < 0):
        d3script.log("PresetStorage", "PresetManager3 Loaded")
        return


SCRIPT_OPTIONS = {
    "minimum_version" : 23, # Min. compatible version
    "init_callback" : initCallback, # Init callback if version check passes
    "scripts" : [
        {
            "name" : "Preset Manager", # Display name of script
            "group" : "Preset Manager", # Group to organize scripts menu.  Scripts menu is sorted a separated by group
            "help_text" : "Manage Number(float) values as recallable values", #text for help system
            "callback" : sendActiveColorInfo, # function to call for the script
        },

        ]

    }
