# SMTransitionTools.py

from d3 import *
import d3script


def initCallback():
    d3script.log("EncoderTools","EncoderTools Loaded")



def setCurrentSectionCrossfade(time):
    time = float(time)
    track = state.track

    sectionTransitions = track.sectionTransitions

    currentSectionNumber = track.beatToSection(track.timeToBeat(state.player.tRender))

    currentTransition = sectionTransitions[currentSectionNumber]

    # Transition modes: 0=Undefined, 1=Fade, 2=TrackSection

    if time == 0:
        currentTransition.mode = 0
        currentTransition.fadeDurationBeats = 0
    else:
        currentTransition.mode = 1
        currentTransition.fadeDurationBeats = time

    track.onChangedAction.doit()


SCRIPT_OPTIONS = {
    "minimum_version" : 23, # Min. compatible version
    "init_callback" : initCallback, # Init callback if version check passes
    "scripts" : [
        {
            "name" : "Set Current Section Crossfade", # Display name of script
            "group" : "Encoder Tools", # Group to organize scripts menu.  Scripts menu is sorted a separated by group
            "help_text" : "Sets current fade time", #text for help system
            "callback" : setCurrentSectionCrossfade, # function to call for the script
        }
    ]
}
