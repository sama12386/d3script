# Helper api for d3/disguise scripting
# Dan Scully, 2022
# No license yet
# Some code clearly copy/pasted from RGM

# TODO get bindings off of the gui root
# TODO check for scripting enabled flag
# TODO testing.  ugh

import importlib
from d3 import *
import os
import json
import sys
import math
import time
import struct
import socket
import win32com.client



SCRIPTSFOLDER = "./objects/Scripts"
D3MAJORVERSION = ReleaseVersion.versionName
D3MINORVERSION = ReleaseVersion.micro
SCRIPTMENUTITLE = 'Script Menu'
SCRIPTBUTTONTITLE = 'Scripts'
NOTESTORAGENAME = 'd3scriptstoragenote_donottouch'
scripts = []
scriptMods = []
debugmode = False

#utility functions - should these move somewhere else?
def log(sender, msg,debugOnly = False):
    """
    A wrapper for printing to the console.

    ``debugOnly`` is an optional flag for messages only printed when ``d3script.debugMode`` is True
    """
    if (not debugOnly) or (debugMode):
        print (sender + ": " + msg)

def callScript(module,func,param = None):
    """
    Calls a loaded script function directly.  Useful for firing scripts over the telnet console
    """    
    log('d3script','dispatching: ' + module + '.' + func)
    funcCall = getattr(sys.modules[module],func)
    if (param != None):
        funcCall(param)
    else:
        funcCall()

def sendOscMessage(device,msg,param = None):
    """
    Utility for sending OSC Messages.
    Currently only allows one parameter.  Uses the info from a d3 OSC Device, but does not use the builtin functions
    as messages are only supported on Directors and Actors.
    """

    log('d3script','Sending Eos msg: ' + msg + 'with param: ' + str(param))
    
    OSCAddrLength = math.ceil((len(msg)+1) / 4.0) * 4
    packedMsg = struct.pack(">%ds" % (OSCAddrLength), str(msg))

    if type(param) == str:
        OSCTypeLength = math.ceil((len(',s')+1) / 4.0) * 4
        packedType = struct.pack(">%ds" % (OSCTypeLength), str(',s'))
        OSCArgLength = math.ceil((len(param)+1) / 4.0) * 4
        packedParam = struct.pack(">%ds" % (OSCArgLength), str(param))

    elif type(param) == float:
        OSCTypeLength = math.ceil((len(',f')+1) / 4.0) * 4
        packedType = struct.pack(">%ds" % (OSCTypeLength), str(',f'))
        packedParam  = struct.pack(">f", float(param))

    elif type(param) == int:
        OSCTypeLength = math.ceil((len(',f')+1) / 4.0) * 4
        packedType = struct.pack(">%ds" % (OSCTypeLength), str(',i'))
        packedParam  = struct.pack(">i", int(param))

    else:
        packedType = ''
        packedParam = ''

    oscMsg = packedMsg + packedType + packedParam
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(oscMsg, (device.sendIPAddress, device.sendPort))
    time.sleep(0.1)

def getLayersOfTrackAtTime(trk,t):
    return filter(lambda l:(l.tStart <= t) and (t <= l.tEnd),trk.layers)

def findWidgetByName(name):
    """
    Find a gui widget by name.  
    Note that if you are looking at the widget title in the UI, that's often the name of the title button 
    and you need to get the parent object to get the widget you want.
    """

    return d3gui.root.findWidgetByName(name)

def getPersistentValue(key):
    """
    Gets a persistent value.  d3script stores values as JSON in a special note in d3's note system.
    """
    
    note = resourceManager.loadOrCreate('objects/note/'+NOTESTORAGENAME+'.apx',Note)
    if len(note.text) > 0:
        localDict = json.loads(note.text)
    else:
        return None

    if localDict.has_key(key):
        return localDict[key]
    else:
        return None


def setPersistentValue(key,value):
    """
    Sets a persistent value which will exist across restarts.  d3script stores values as JSON in a special note in d3's note system.
    """
    note = resourceManager.loadOrCreate('objects/note/'+NOTESTORAGENAME+'.apx',Note)
    if len(note.text) > 0:
        localDict = json.loads(note.text)
    else:
        localDict = {}
    
    localDict[key] = value

    note.text = json.dumps(localDict)


def createLayerOfTypeOnCurrentTrack(moduleType):
    """
    Creates a new on the current Track of the type specified (by module name in New Layer popup).
    Currently fakes UI interactions.
    Returns the layer.
    """

    tw = getTrackWidget()
    bw = tw.barWidget

    bw.newUnnamedLayer()

    cm = d3gui.root.findWidgetByName('Select type of layer')
    if (cm == None):
        log('d3script','Could not find Class Menu for create layer')
    
    #super fragile
    grps = cm.parent.children[2].children[0].children

    bts = []

    for grp in grps:
        for c in grp.children:
            bts.append(c)
    
    bts = filter(lambda bt: type(bt) == Button,bts)

    btn = filter(lambda bt: bt.name == moduleType,bts)
    
    if len(btn) != 1:
        log('d3script','create layer could not find module of type: ' + moduleType)
        return

    # 'Press' the button to make the layer
    btn[0].clickAction.doit()

    # I assume this is super fragile as well
    return state.track.layers[0]


def getFieldFromLayerByName(lay, fieldName):
    """Get the field by name from a layer"""
    flds = filter(lambda x: x.name.lower() == fieldName.lower(),lay.fields)
    if len(flds) == 1:
        return flds[0]
    else:
        log('d3script','Could not find field: ' + fieldName + ' for layer: ' + lay.name)


def setKeyForLayerAtTime(lay, fieldName, val, timeStart):
    """creates a keyframe for value at time.  If key exists, delete key"""
    """passing a string to a resource field will attempt to find the resource by name"""

    def _findResourceByNameAndType(name,rt):
        if type(name) == str:
            vcs = resourceManager.allResources(rt)
            vcs = filter(lambda v: v.description.lower() == name.lower(),r)

            if len(vcs) == 1:
                return vcs[0]
            else:
                return None
                

    timeStart = float(timeStart)

    seq = getFieldFromLayerByName(lay,fieldName).sequence

    # Find out what type of sequence we are dealing with
    if isinstance(seq, ResourceSequence):
        
    # delineate between videos, mappings, and audio mappings
    # and create full path to resource.

        theRes = None
        if fieldName == 'video':
            resType = VideoClip

        elif fieldName == 'mapping':
            resType = Projection

        elif fieldName == 'Output':
            resType = LogicalAudioOutDevice

        else:
            log('d3script','Only resource sequences of "video", "mapping", or "Output" are supported as of now')
            return


        if type(val) == str:
            theRes = _findResourceByNameAndType(val,resType)

        elif isinstance(val,resType):
            theRes = val

        if (theRes) == None:
            log('d3script','Could not find resource of right type with name ' + val)
            return

    # Remove key if it exists already
        for key in range(seq.nKeys()):
            if seq.keys[key].localT == timeStart:
                seq.remove(key, timeStart)

        seq.setResource(timeStart, theRes)

    elif isinstance(seq, FloatSequence):
        seq.setFloat(timeStart, float(val))

    elif isinstance(seq, StringSequence):
        seq.setStringAtT(timeStart, str(val))



def expressionSafeString(text):
    """
    Convert string to be expression safe.
    Replaces all punctuation with underscores
    """

    return text.replace('{','_').replace('}','_').replace('(','_').replace(')','_').replace(' ','_').replace('[','_').replace(']','_').replace('-','_')


def setExpression(layer,fieldName,expression):
    """
    Sets an expression on the layer for the fieldName specified.  
    Checks to make sure field is or type int or float to avoid issues with trying to set expressions on resource-backed fields.
    """
    fs = filter(lambda f:f.name == fieldName,layer.fields)

    if len(fs) == 0:
        log('d3script','Could not find field: '+ fieldName + ' for layer: ' + layer.name)
        return
    else:
        fs = fs[0]

    if (fs.type != int) and (fs.type != float):
        log('d3script','Field is not int or float type.  Cannot set expression.')
        return

    fs.setExpression(expression)



def simulateKeypress(key):
    """
    Simulates key presses by the user
    # For SHIFT prefix with +
    # For CTRL  prefix with ^
    # For ALT   prefix with %
    # ~	{~}	Send a tilde (~)
	# {!}	Send an exclamation point (!)
	# {^}	Send a caret (^)
	# {+}	Send a plus sign (+)
    # Backspace	{BACKSPACE} or {BKSP} or {BS}	Send a Backspace keystroke
    # Break	{BREAK}	Send a Break keystroke
    # Caps Lock	{CAPSLOCK}	Press the Caps Lock Key (toggle on or off)
    # Clear	{CLEAR}	Clear the field
    # Delete	{DELETE} or {DEL}	Send a Delete keystroke
    # Insert	{INSERT} or {INS}	Send an Insert keystroke
    # Cursor control arrows	{LEFT} / {RIGHT} / {UP} / {DOWN}	Send a Left/Right/Up/Down Arrow
    # End	{END}	Send an End keystroke
    # Enter	{ENTER} or ~	Send an Enter keystroke
    # Escape	{ESCAPE}	Send an Esc keystroke
    # F1 through F16	{F1} through {F16}	Send a Function keystroke
    # Help	{HELP}	Send a Help keystroke
    # Home	{HOME}	Send a Home keystroke
    # Numlock	{NUMLOCK}	Send a Num Lock keystroke
    # Page Down {PGDN}
    # Page Up	{PGUP}	Send a Page Down or Page Up keystroke
    # Print Screen	{PRTSC}	Send a Print Screen keystroke
    # Scroll lock	{SCROLLLOCK}	Press the Scroll lock Key (toggle on or off)
    # TAB	{TAB}	Send a TAB keystroke
    """
    shell = win32com.client.Dispatch('WScript.Shell')
    shell.SendKeys(key)

def getTrackWidget():
    """
    Return the track widget
    """
    return findWidgetByName('trackwidget')

def getSelectedLayers():
    """
    Get selected layers (if any) in the active track.
    """
    tw = getTrackWidget()
    if tw:
        return  tw.layerView.getSelectedLayers()


def blendModeToString(mode):
    modes = {
        0.0 : 'Over',
        1.0 : 'Alpha',
        2.0 : 'Add',
        3.0 : 'Mult',
        4.0 : 'Mask',
        5.0 : 'MultF',
        6.0 : 'MultA',
        7.0 : 'PreMultA',
        8.0 : 'Scrn',
        9.0 : 'Ovrly',
        10.0 : 'Hard',
        11.0 : 'Soft',
        12.0 : 'Burn',
        13.0 : 'Dark',
        14.0 : 'Light',
        15.0 : 'Diff',
        16.0 : 'Excl',
        17.0 : 'Dodge',
        18.0 : 'HMix' }

    return modes[mode]


def guiSpacer(x,y):
    """
    create and return a spacer widget with the given sizes
    """
    spacer = Widget()
    spacer.minSize = Vec2(x * d3gui.dpiScale.x, y * d3gui.dpiScale.y)
    return spacer

def recursive_dir(obj, path):
    #if ((obj!=None) and (not isinstance(obj, (str,float,int,list,dict,set)))):
    if (obj!=None):
        for attr, val in obj.__dict__.iteritems():
            temp_path = path[:]
            temp_path.append(attr)
            recursive_dir(getattr(obj, attr), temp_path)
    else:
        print (path, "--->", obj)
        print("")

def load_scripts():
    """
    If the ``enableScripting`` option is enabled, the Objects/PythonFile folder will be scanned,
    and will attempt to load any modules/.py files found.  Errors while loading will be
    reported to the console.
    """
    # Should check for a flag, but that flag doesn't exist yet.

    global scripts
    global scriptMods

    #Stop d3/python from making pyc files while we load modules
    pycFlag = sys.dont_write_bytecode
    sys.dont_write_bytecode = True

    # if we are reloading scripts, we need to do some work to clean up the old versions

    # We need to remove the keybindings to previous callback functions.  This seems... bad.
    d3gui.root.inputMap.clearMappings()
    
    openScriptMenu = findWidgetByName(SCRIPTMENUTITLE)
    if openScriptMenu:
        openScriptMenu.parent.close()

    scripts = []

    while len(scriptMods) > 0:
        mod = scriptMods.pop()
        try:
            if mod.SCRIPT_OPTIONS.has_key('del_callback'):
                mod.SCRIPT_OPTIONS['del_callback']()

            reload(mod)
            log('d3script','Reloaded module: ' + mod.__name__ + '.')

        except:
            log('d3script','Error while reloading ' + mod.__name__ + '. Error thrown during deletion/reload.')

    scriptMods = []

    # Make sure scripts path exists
    if not os.path.exists(SCRIPTSFOLDER):
        os.mkdir(SCRIPTSFOLDER)

    # Add objects/pythonFile to the path
    if SCRIPTSFOLDER not in sys.path:
        sys.path.append(SCRIPTSFOLDER)

    possiblescripts = os.listdir(SCRIPTSFOLDER)
    
    for script in possiblescripts:
        scriptname = os.path.splitext(script)[0]
        try:
            scriptMods.append(importlib.import_module(scriptname))
        except:
            log('d3script','Error while loading ' + scriptname + '. Skipping script.')


    for mod in scriptMods:
        register_script(mod)

    existingButton = findWidgetByName(SCRIPTBUTTONTITLE)
    if (existingButton):
        existingButton.parent.close()

    findWidgetByName('d3').add(ScriptButton())

    #reset this pyc flag when we are done in case something relies on it
    sys.dont_write_bytecode = pycFlag



def open_scripts_menu():
    """
    opens a script menu if not already open
    """

    script_gui_menu = findWidgetByName(SCRIPTMENUTITLE)
    if not script_gui_menu:
        ScriptMenu()
    else:
        script_gui_menu.parent.moveToFront()


def register_script(mod):
    """
    This function has two responsiblities:
    - Check for version compatibility.  If that check clears, call the scripts entrypoint
    - If the script wants it, add the script to the Scripts menu

    Each script should define a dict called ``SCRIPT_OPTIONS`` which defines the following:
    ``SCRIPT_OPTIONS = {
        "minimum_version" : 17, # Min. compatible version
        "minimum_minor_version" : 1.3, # Min. minor version (when combined with major version)
        "maximum_version" : 20, # Max. compatible version - or None
        "maximum_minor_version" : 9.9, # Max. minor version  (when combined with major version) - or None
        "init_callback" : callbackfunc, # Init callback if version check passes
        "del_callback"  : delcallbackfunc, # Destructor in case we reload module
        "scripts" : [array of script entry points (see below)]
    }

    script = {
        "name" : "My Script #1", # Display name of script
        "group" : "Dan's Scripts", # Group to organize scripts menu.  Scripts menu is sorted a separated by group
        "binding" : "CTRL+SHIFT+P", # Keyboard shortcut
        "bind_globally" : True, # binding should be global
        "help_text" : "Tool Tip Text", #text for help system
        "callback" : callbackfunc, # function to call for the script
    }
    """
    
    global scripts

    #First check versioning
    try:
        script_options = mod.SCRIPT_OPTIONS

        if script_options['minimum_version'] > D3MAJORVERSION:
            log('d3script','Error while registering ' + mod.__name__ + '. Minimum version is newer than current.')
            return
        elif (script_options['minimum_version'] == D3MAJORVERSION) and (script_options['minimum_minor_version'] > D3MINORVERSION):
            log('d3script','Error while registering ' + mod.__name__ + '. Minimum minor version is newer than current.')
            return
        elif (script_options.has_key('maximum_version')) and (not script_options.has_key('maximum_minor_version')) and (script_options['maximum_version'] < D3MAJORVERSION):
            log('d3script','Error while registering ' + mod.__name__ + '. Maximum version is less than current.')
            return       
        elif (script_options.has_key('maximum_version')) and (script_options.has_key('maximum_minor_version')) and (script_options['maximum_version'] == D3MAJORVERSION) and (script_options['maximum_minor_version'] < D3MINORVERSION):
            log('d3script','Error while registering ' + mod.__name__ + '. Maximum minor version is less than current.')
            return        
    except:
            log('d3script','Error while registering ' + mod.__name__ + '. Uknown error during version check.')
            return    

    log('d3script', mod.__name__ + ' passed version check.')

    #Version checks out - call the init script
    try:
        if script_options.has_key('init_callback'):
            script_options['init_callback']()
    except:
        log('d3script','Error while registering ' + mod.__name__ + '. Error thrown during initialization.')
        return  

    log('d3script', mod.__name__ + ' passed initialization.')

    #process script callbacks
    for script in script_options['scripts']:
        if (not script.has_key('name')) or (not script.has_key('group')) or (not script.has_key('callback')):
            log('d3script','Error while registering ' + mod.__name__ + '. script missing parameter.')
            continue 


        if script.has_key('binding'):
            globalScope = script.get('bind_globally', False)
            helptext = script.get('help_text', script['name'])
            try:
                #ignoring global scope for now. FIX FIX FIX - This is ugly
                d3gui.root.inputMap.add(script['callback'], script['binding'], helptext)
            except:
                log('d3script','Error while registering ' + mod.__name__ + '. Could not make script binding.')
            
        if script not in scripts:
            log('d3script','Adding script ' + script['name'] + ' to scripts list.')
            scripts.append(script)
    
    def script_sort(val):
        val['group'] + '.' + val['name']
    
    scripts.sort(key=script_sort)


class ScriptButton(Widget):

    def __init__(self):
        global scripts

        Widget.__init__(self) 
        bt = TitleButton(SCRIPTBUTTONTITLE)
        bt.clickAction.add(open_scripts_menu)
        self.arrangeHorizontal()
        bt.canClose = False
        bt.border = Vec2(6,6)
        self.border = Vec2(6,6)
        self.add(bt)


class ScriptMenu(Widget):
    isStickyable = True

    def __init__(self):
        global scripts
        
        Widget.__init__(self)   
        self.titleButton = TitleButton(SCRIPTMENUTITLE)
        self.add(self.titleButton)
        bt = Button('Reload Scripts',load_scripts)
        bt.border = Vec2(0,10)
        #self.updateAction.add(self.update)

        self.add(bt)
        self.pos = d3gui.cursorPos + Vec2(64,-8)
        self.arrangeVertical()
        self.minSize = Vec2(1000,800)

        currentGroup = None
        groupWidget = None

        # Add scripts to menu
        for index, script in enumerate(scripts):
            if (currentGroup != script['group']):
                groupWidget = CollapsableWidget(script['group'],script['group'])
                currentGroup = script['group']
                self.add(groupWidget)

            bt = Button(script['name'],script['callback'])
            bt.border = Vec2(0,12)

            #self.buttons.append(bt)
            groupWidget.add(bt)

        d3gui.root.add(self)


load_scripts()