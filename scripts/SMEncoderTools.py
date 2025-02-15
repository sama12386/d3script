# SMEncoderTools.py

from gui.inputmap import *
from d3 import *
import d3script
import colorsys

from scripts.util.ColorUtil import adjust_color_feel_hue_saturation_hsb, adjust_temperature_cct


def initCallback():
    d3script.log("EncoderTools","EncoderTools Loaded")



def performColorAdjustmentOfSelectedLayers(colorAndIncrement):
    split = colorAndIncrement.split(":")

    color = split[0]
    increment = float(split[1])
    # increment is 0-1

    # Get common properties from state
    currentTimeRender = state.player.tRender  # Current playhead track time in float seconds
    track = state.track
    selectedLayers = d3script.getSelectedLayers()

    sectStartTime, nextSectStartTime = getSectionTimes(track, currentTimeRender)


    for layer in selectedLayers:
        xColFieldSequence = [f for f in layer.fields if (f.name == "xCol")][0]
        yColFieldSequence = [f for f in layer.fields if (f.name == "yCol")][0]

        currentXCol = float(xColFieldSequence.sequence.evalString(currentTimeRender))
        currentYCol = float(yColFieldSequence.sequence.evalString(currentTimeRender))

        if(color == "cct"):
            newXCol, newYCol = adjust_temperature_cct(currentXCol, currentYCol, increment)

        else:
            newXCol, newYCol = adjust_color_feel_hue_saturation_hsb(currentXCol, currentYCol, color, increment)

        d3script.log("New Colors", str(newXCol) + " and " + str(newYCol))

        setKeyValues(currentTimeRender, sectStartTime, nextSectStartTime, xColFieldSequence, newXCol)
        setKeyValues(currentTimeRender, sectStartTime, nextSectStartTime, yColFieldSequence, newYCol)


def setXYColorOfSelectedLayers(color): #Format is x,y
    split = color.split(",")
    xCol = split[0]
    yCol = split[1]

    setPropertyOfSelectedLayers("xCol", 0, xCol)
    setPropertyOfSelectedLayers("yCol", 0, yCol)

def incrementPropertyOfSelectedLayers(propertyAndIncrement):
    split = propertyAndIncrement.split(":")

    property = split[0]
    increment = float(split[1])

    setPropertyOfSelectedLayers(property, increment)

def defaultPropertyOfSelectedLayers(propertyAndValue):
    split = propertyAndValue.split(":")

    property = split[0]
    value = float(split[1])

    setPropertyOfSelectedLayers(property, 0, value)


def multiplyPropertyOfSelectedLayers(propertyAndValue):

    split = propertyAndValue.split(":")

    property = split[0]
    value = float(split[1])

    d3script.log("Encoder Value Change", "Multiplying" + str(property) + " to " + str(value))
    setPropertyOfSelectedLayers(property, 0, None, value)


####
# def setPropertyOfSelectedLayers(property, increment, overrideValue = None, multiplierValue = None):
#
#     if property == "blendMode":
#         increment = int(increment)
#         if overrideValue != None:
#             overrideValue = int(overrideValue)
#     # split = propertyAndIncrement.split(":")
#     #
#     # property = split[0]
#     # increment = float(split[1])
#
#     currentTimeRender = state.player.tRender #Current playhead track time in float seconds
#     track = state.track
#
#     modifyFields = []
#     selectedLayers = d3script.getSelectedLayers()
#
#     for layer in selectedLayers: #Iterate over selected layer and add each FieldSequence to be modified
#         modifyFields += [f for f in layer.fields if (f.name == property) and (f.type == float or f.name == "blendMode")]
#
#     for fieldSequence in modifyFields:
#         # d3script.log("PresetManager3", fieldSequence.)
#         floatSeq = fieldSequence.sequence
#         sectStartTime = track.sections.getT(track.beatToSection(track.timeToBeat(currentTimeRender)))
#         nextSectIndex = track.beatToSection(track.timeToBeat(currentTimeRender)) + 1
#         if nextSectIndex < track.nSections:
#             nextSectStartTime = track.sections.getT(nextSectIndex)
#         else:
#             nextSectStartTime = sectStartTime + 30
#         curValue = float(floatSeq.evalString(currentTimeRender))
#
#         if(overrideValue == None):
#             newValue = curValue + increment
#
#         else:
#             newValue = overrideValue
#
#
#         if(multiplierValue != None): #Hack to insert multiplier
#             newValue = curValue * multiplierValue
#
#
#         # Add check to see if exceeds min or max
#
#         d3script.log("Encoder Value Change", "Name: " + fieldSequence.name + " value: " + str(newValue))
#
#         prevKeyTime = floatSeq.findCurrentKeyTime(currentTimeRender)
#         nextKeyTime = floatSeq.findNextKeyTime(currentTimeRender)
#         prevKeyValue = float(floatSeq.evalString(prevKeyTime))
#         nextKeyValue = float(floatSeq.evalString(nextKeyTime))
#         sectValue = float(floatSeq.evalString(sectStartTime))
#         nextSectValue = float(floatSeq.evalString(nextSectStartTime))
#
#
#         # Break
#
#         keyValue = newValue
#         # keyTime = parseKeyTime(key[1])
#         keyTime = None
#
#         # if (fieldSequence.noSequence == True) and (keyTime != None):
#         #     fieldSequence.disableSequencing = False
#         #     if (floatSeq.nKeys() > 0):
#         #         floatSeq.remove(0, floatSeq.nKeys())
#         #     floatSeq.setFloat(keyTime, float(keyValue))
#         #     floatSeq.key(floatSeq.find(keyTime)).interpolation = key[2]
#
#         if (fieldSequence.noSequence == True) and (keyTime == None):
#             if (floatSeq.nKeys > 0):
#                 floatSeq.remove(0, floatSeq.nKeys())
#             floatSeq.setFloat(fieldSequence.layer.tStart, float(keyValue))
#
#         elif (fieldSequence.noSequence == False) and (keyTime == None):
#             floatSeq.setFloat(currentTimeRender, float(keyValue))
#             floatSeq.key(floatSeq.find(currentTimeRender)).interpolation = key[2]
#             # TODO does interpolation need to be set?
#
#         # elif (fieldSequence.noSequence == False) and (keyTime != None):
#         #     seq.setFloat(keyTime, float(keyValue))
#         #     seq.key(seq.find(keyTime)).interpolation = key[2]

#####

def setPropertyOfSelectedLayers(property, increment, overrideValue=None, multiplierValue=None):
    # Step 1: Handle the property and increment logic
    property, increment, overrideValue = handlePropertyLogic(property, increment, overrideValue)

    # Get common properties from state
    currentTimeRender = state.player.tRender  # Current playhead track time in float seconds
    track = state.track
    selectedLayers = d3script.getSelectedLayers()

    # Step 2: Get the fields that need to be modified
    modifyFields = getFieldsToModify(selectedLayers, property)

    # Step 3: Modify the field sequences
    for fieldSequence in modifyFields:
        modifyFieldSequence(fieldSequence, track, currentTimeRender, increment, overrideValue, multiplierValue)


def handlePropertyLogic(property, increment, overrideValue):
    """Handles logic specific to the property and increments."""
    if property == "blendMode":
        increment = int(increment)
        if overrideValue is not None:
            overrideValue = int(overrideValue)
    return property, increment, overrideValue


def getFieldsToModify(selectedLayers, property):
    """Gathers fields from selected layers based on the given property."""
    modifyFields = []
    for layer in selectedLayers:
        modifyFields += [f for f in layer.fields if (f.name == property) and (f.type == float or f.name == "blendMode")]
    return modifyFields


def modifyFieldSequence(fieldSequence, track, currentTimeRender, increment, overrideValue, multiplierValue):
    """Modifies a given field sequence based on the current and new values."""
    floatSeq = fieldSequence.sequence
    sectStartTime, nextSectStartTime = getSectionTimes(track, currentTimeRender)
    curValue = float(floatSeq.evalString(currentTimeRender))

    # Step 4: Calculate the new value
    newValue = calculateNewValue(curValue, increment, overrideValue, multiplierValue)

    # Step 5: Log the value change
    logValueChange(fieldSequence, newValue)

    # Step 6: Set the new key values in the sequence
    setKeyValues(currentTimeRender, sectStartTime, nextSectStartTime, fieldSequence, newValue)


def getSectionTimes(track, currentTimeRender):
    """Determines section start and next section times."""
    sectStartTime = track.sections.getT(track.beatToSection(track.timeToBeat(currentTimeRender)))
    nextSectIndex = track.beatToSection(track.timeToBeat(currentTimeRender)) + 1
    if nextSectIndex < track.nSections:
        nextSectStartTime = track.sections.getT(nextSectIndex)
    else:
        nextSectStartTime = sectStartTime + 30
    return sectStartTime, nextSectStartTime


def calculateNewValue(curValue, increment, overrideValue, multiplierValue):
    """Calculates the new value based on the current value, increment, and any overrides."""
    if overrideValue is None:
        newValue = curValue + increment
    else:
        newValue = overrideValue

    if multiplierValue is not None:
        newValue = curValue * multiplierValue

    return newValue


def logValueChange(fieldSequence, newValue):
    """Logs the value change."""
    d3script.log("Encoder Value Change", "Name: " + fieldSequence.name + " value: " + str(newValue))


def setKeyValues(currentTimeRender, sectStartTime, nextSectStartTime, fieldSequence, newValue):

    floatSeq = fieldSequence.sequence

    """Sets key values for the field sequence."""
    prevKeyTime = floatSeq.findCurrentKeyTime(currentTimeRender)
    nextKeyTime = floatSeq.findNextKeyTime(currentTimeRender)
    prevKeyValue = float(floatSeq.evalString(prevKeyTime))
    nextKeyValue = float(floatSeq.evalString(nextKeyTime))
    sectValue = float(floatSeq.evalString(sectStartTime))
    nextSectValue = float(floatSeq.evalString(nextSectStartTime))

    keyValue = newValue
    keyTime = None

    if (fieldSequence.noSequence == True) and (keyTime == None):
        if (floatSeq.nKeys > 0):
            floatSeq.remove(0, floatSeq.nKeys())
        floatSeq.setFloat(fieldSequence.layer.tStart, float(keyValue))

    elif (fieldSequence.noSequence == False) and (keyTime == None):
        floatSeq.setFloat(currentTimeRender, float(keyValue))
        floatSeq.key(floatSeq.find(currentTimeRender)).interpolation = key[2]

    # if fieldSequence.noSequence and keyTime is None:
    #     if floatSeq.nKeys() > 0:
    #         floatSeq.remove(0, floatSeq.nKeys())
    #     floatSeq.setFloat(fieldSequence.layer.tStart, float(keyValue))
    # elif not fieldSequence.noSequence and keyTime is None:
    #     floatSeq.setFloat(currentTimeRender, float(keyValue))
    #     floatSeq.key(floatSeq.find(currentTimeRender)).interpolation = None  # You may need to handle interpolation





#####

# def getCurrentValue(fieldSequence, currentTimeRender):
#     floatSeq = fieldSequence.sequence
#     sectStartTime = track.sections.getT(track.beatToSection(track.timeToBeat(currentTimeRender)))
#     nextSectIndex = track.beatToSection(track.timeToBeat(currentTimeRender)) + 1
#     if nextSectIndex < track.nSections:
#         nextSectStartTime = track.sections.getT(nextSectIndex)
#     else:
#         nextSectStartTime = sectStartTime + 30
#     curValue = float(floatSeq.evalString(currentTimeRender))
#     return curValue


def scrollFocusedSmall(scale):
    scaleNumber = int(scale)
    fw = d3gui.root.focusedWidget()
    if hasattr(fw,'mouseScrollSmall'):
        fw.mouseScrollSmall(scaleNumber)



SCRIPT_OPTIONS = {
    "minimum_version" : 23, # Min. compatible version
    "init_callback" : initCallback, # Init callback if version check passes
    "scripts" : [
        {
            "name" : "Modify Layer Propeerty", # Display name of script
            "group" : "Encoder Tools", # Group to organize scripts menu.  Scripts menu is sorted a separated by group
            "help_text" : "move value by 'small' amount.  'scale' is the direction as an int ", #text for help system
            "callback" : incrementPropertyOfSelectedLayers, # function to call for the script
        },
        {
            "name" : "Set Layer Propeerty", # Display name of script
            "group" : "Encoder Tools", # Group to organize scripts menu.  Scripts menu is sorted a separated by group
            "help_text" : "move value by 'small' amount.  'scale' is the direction as an int ", #text for help system
            "callback" : defaultPropertyOfSelectedLayers, # function to call for the script
        },
        {
            "name" : "Set Layer XY Color", # Display name of script
            "group" : "Encoder Tools", # Group to organize scripts menu.  Scripts menu is sorted a separated by group
            "help_text" : "format is x,y", #text for help system
            "callback" : setXYColorOfSelectedLayers, # function to call for the script
        },
        {
            "name" : "Multiply Layer Property", # Display name of script
            "group" : "Encoder Tools", # Group to organize scripts menu.  Scripts menu is sorted a separated by group
            "help_text" : "format is x,y", #text for help system
            "callback" : multiplyPropertyOfSelectedLayers, # function to call for the script
        },
{
            "name" : "Adjust indirect color", # Display name of script
            "group" : "Encoder Tools", # Group to organize scripts menu.  Scripts menu is sorted a separated by group
            "help_text" : "color, increment", #text for help system
            "callback" : performColorAdjustmentOfSelectedLayers, # function to call for the script
        }
    ]
}
