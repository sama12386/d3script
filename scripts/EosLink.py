# EosLink.py
from time import sleep

from gui.inputmap import *
from d3 import *
import d3script
from scripts.pyosc.OSC import OSCServer, ThreadingOSCServer, ThreadingMixIn

def _setEosPersistentValues(user,cueList,oscDeviceName):
    d3script.setPersistentValue('EosLinkUser', user)
    d3script.setPersistentValue('EosLinkList', cueList)        
    d3script.setPersistentValue('EosOscDevice', oscDeviceName)


def _getEosPersistentValues():
    user = ''
    cueList = ''
    oscDeviceName = ''

    param = d3script.getPersistentValue('EosLinkUser')
    if param:
        user = param
        
    param = d3script.getPersistentValue('EosLinkList')
    if param:
        cueList = param

    param = d3script.getPersistentValue('EosOscDevice')
    if param:
        oscDeviceName = param

    return user, cueList, oscDeviceName


def _getTagAndNoteForSectionAtPlayhead():
    trk = state.track
    lastTagBeat = trk.findBeatOfLastTag(trk.timeToBeat(state.player.tCurrent))
    tag = trk.tagAtBeat(lastTagBeat)
    label = trk.noteAtBeat(lastTagBeat)

    tagParts = tag.split(' ')
    if (len(tagParts) != 2) or (tagParts[0] != 'CUE'):
        cue = ''
    else:
        cue = tagParts[1]

    return cue, label


def _getOscDeviceByName(name):
    oscDevices = resourceManager.allResources(OscDevice)
    oscDevices = filter(lambda d:d.description == name, oscDevices)

    if len(oscDevices) != 1:
        d3script.log('EosLink','Could not resolve OSC Device.  Not sending a message.')
        return None
    else:
        return oscDevices[0]


def _buildEosBaseWidget(title, buttonLabel, action, baseWidget, includeLabelFlag):

    baseWidget.titleButton = TitleButton("EosLink: " + title)
    baseWidget.add(baseWidget.titleButton)

    oscDeviceNames = map(lambda l: l.description, baseWidget.oscDevices)
    baseWidget.oscDeviceBox = ValueBox(baseWidget, 'oscDeviceIndex', oscDeviceNames)
    baseWidget.add(Field('OSC Device: ',baseWidget.oscDeviceBox))

    baseWidget.fieldWrapperWidget = CollapsableWidget('Cue Data','Cue Data')
    baseWidget.fieldWrapperWidget.arrangeVertical()
    baseWidget.add(baseWidget.fieldWrapperWidget)
    baseWidget.fieldSectionWidget = Widget()
    baseWidget.fieldSectionWidget.arrangeHorizontal()
    baseWidget.fieldWrapperWidget.add(baseWidget.fieldSectionWidget)
    baseWidget.labelWidget = Widget()
    baseWidget.valuesWidget = Widget()
    baseWidget.valuesWidget.minSize = Vec2(50,0)

    baseWidget.userEditBox = ValueBox(baseWidget,'user')
    baseWidget.valuesWidget.add(baseWidget.userEditBox)
    baseWidget.labelWidget.add(TextLabel('Eos User:').justify()) 

    baseWidget.listEditBox = ValueBox(baseWidget,'cuelist')
    baseWidget.valuesWidget.add(baseWidget.listEditBox)
    baseWidget.labelWidget.add(TextLabel('Eos List:').justify())

    baseWidget.cueEditBox = ValueBox(baseWidget,'cue')
    baseWidget.valuesWidget.add(baseWidget.cueEditBox)
    baseWidget.labelWidget.add(TextLabel('Cue Number:').justify()) 

    if (includeLabelFlag):
        baseWidget.labelEditBox = ValueBox(baseWidget,'label')
        baseWidget.valuesWidget.add(baseWidget.labelEditBox)
        baseWidget.labelWidget.add(TextLabel('Cue Label:').justify()) 

    baseWidget.labelWidget.arrangeVertical()
    baseWidget.valuesWidget.arrangeVertical()
        
    baseWidget.fieldSectionWidget.add(baseWidget.labelWidget)
    baseWidget.fieldSectionWidget.add(baseWidget.valuesWidget)
    baseWidget.computeAllMinSizes()
    baseWidget.arrangeVertical()

    doButton = Button(buttonLabel, action)
    doButton.border = Vec2(0,10)
    baseWidget.add(doButton)
    baseWidget.pos = (d3gui.root.size / 2) - (baseWidget.size/2)
        
    baseWidget.pos = Vec2(baseWidget.pos[0], baseWidget.pos[1]-100)

    return baseWidget


def EosSendKey(key):
    user, cuelist, oscDeviceName = _getEosPersistentValues()

    if (user == '') or (oscDeviceName == ''):
        d3script.log('EosLink','Missing osc Device or user number.  Not sending a message.')
        return

    oscDevice = _getOscDeviceByName(oscDeviceName)

    msg = '/eos/user/'+ user + '/key/' + key

    if (oscDevice != None):
        d3script.sendOscMessage(oscDevice, msg)


def EosFireMacro(macro):    
    user, cuelist, oscDeviceName = _getEosPersistentValues()

    if (user == '') or (oscDeviceName == ''):
        d3script.log('EosLink','Missing osc Device or user number.  Not sending a message.')
        return

    oscDevice = _getOscDeviceByName(oscDeviceName)

    msg = '/eos/user/'+ user + '/macro/fire'

    if (oscDevice != None):
        d3script.sendOscMessage(oscDevice, msg, macro)


class EosCueDelete(Widget):
    cue = ''
    user = ''
    cuelist = ''

    def __init__(self):
        
        self.user, self.cuelist, self.oscDeviceName = _getEosPersistentValues()
        
        self.oscDevices = resourceManager.allResources(OscDevice)
        self.oscDeviceIndex = 0
        for idx,item in enumerate(self.oscDevices):
            if item.description == self.oscDeviceName:
                self.oscDeviceIndex = idx
                break
        
        self.cue, label = _getTagAndNoteForSectionAtPlayhead()

        Widget.__init__(self) 

        _buildEosBaseWidget('Delete Cue', 'Delete Cue', self.doCueDeletion, self, False)  


    def doCueDeletion(self):

        d3script.log("CueDeletion", "running now")

        if (self.cuelist == '') or (self.cue == '') or (self.user == ''):
            d3script.log('EosLink','Missing list, cue, or user number.  Not sending a message.')
            self.close()
            return

        #Store Values for next time
        _setEosPersistentValues(self.user, self.cuelist, self.oscDevices[self.oscDeviceIndex].description)

        oscDev = self.oscDevices[self.oscDeviceIndex]

        prefix = '/eos/user/'+self.user

        #clear the cmd line
        msg = prefix + '/key/clear_cmdline'
        d3script.sendOscMessage(oscDev, msg)

        #go into blind
        msg = prefix + '/key/delete'
        d3script.sendOscMessage(oscDev, msg)

        #create the cue
        msg = prefix + '/set/cue/'+self.cuelist+'/'+self.cue
        d3script.sendOscMessage(oscDev, msg)
        
        #We send enter twice to confirm new cue creation.  If cue exists it has no effect.
        msg = prefix + '/key/enter'
        d3script.sendOscMessage(oscDev, msg)
        d3script.sendOscMessage(oscDev, msg) 

        msg = prefix + '/key/clear_cmdline'
        d3script.sendOscMessage(oscDev, msg)

        self.close()


class EosCueRetrigger(Widget):
    cue = ''
    user = ''
    cuelist = ''
    label = ''

    def __init__(self):
        
        self.user, self.cuelist, self.oscDeviceName = _getEosPersistentValues()
        
        self.oscDevices = resourceManager.allResources(OscDevice)
        self.oscDeviceIndex = 0
        for idx,item in enumerate(self.oscDevices):
            if item.description == self.oscDeviceName:
                self.oscDeviceIndex = idx
                break

        Widget.__init__(self) 

        _buildEosBaseWidget('Retrigger Cue', 'Retrigger Cue', self.doRetriggerCue, self, False) 


    def doRetriggerCue(self):

        if (self.cuelist == '') or (self.user == ''):
            d3script.log('EosLink','Missing list or user number.  Not sending a message.')
            self.close()
            return

        #Store Values for next time
        _setEosPersistentValues(self.user, self.cuelist, self.oscDevices[self.oscDeviceIndex].description)

        oscDev = self.oscDevices[self.oscDeviceIndex]

        prefix = '/eos/user/'+self.user

        #clear the cmd line
        msg = prefix + '/key/clear_cmdline'
        d3script.sendOscMessage(oscDev, msg)

        #go into blind
        msg = prefix + '/key/go_to_cue'
        d3script.sendOscMessage(oscDev, msg)
        
        #We send enter twice to confirm new cue creation.  If cue exists it has no effect.
        msg = prefix + '/key/enter'
        d3script.sendOscMessage(oscDev, msg)

        msg = prefix + '/key/clear_cmdline'
        d3script.sendOscMessage(oscDev, msg)

        self.close()


class EosCueCreator(Widget):
    cue = ''
    user = ''
    cuelist = ''
    label = ''

    def __init__(self):
        
        self.user, self.cuelist, self.oscDeviceName = _getEosPersistentValues()
        
        self.oscDevices = resourceManager.allResources(OscDevice)
        self.oscDeviceIndex = 0
        for idx,item in enumerate(self.oscDevices):
            if item.description == self.oscDeviceName:
                self.oscDeviceIndex = idx
                break
        
        self.cue, self.label = _getTagAndNoteForSectionAtPlayhead()

        Widget.__init__(self)   

        _buildEosBaseWidget('Create Cue', 'Create Cue', self.doCueCreation, self, True) 


    def doCueCreation(self):

        if (self.cuelist == '') or (self.cue == '') or (self.user == ''):
            d3script.log('EosLink','Missing list, cue, or user number.  Not sending a message.')
            self.close()
            return

        oscDev = self.oscDevices[self.oscDeviceIndex]

        #Store Values for next time
        _setEosPersistentValues(self.user, self.cuelist, self.oscDevices[self.oscDeviceIndex].description)

        prefix = '/eos/user/'+self.user

        #clear the cmd line
        msg = prefix + '/key/clear_cmdline'
        d3script.sendOscMessage(oscDev, msg)

        #go into blind
        msg = prefix + '/key/blind'
        d3script.sendOscMessage(oscDev, msg)

        #create the cue
        msg = prefix + '/set/cue/'+self.cuelist+'/'+self.cue
        d3script.sendOscMessage(oscDev, msg)
        
        #We send enter twice to confirm new cue creation.  If cue exists it has no effect.
        msg = prefix + '/key/enter'
        d3script.sendOscMessage(oscDev, msg)
        d3script.sendOscMessage(oscDev, msg) 

        msg = '/eos/set/cue/'+self.cuelist+'/'+self.cue+'/label'   
        d3script.sendOscMessage(oscDev, msg, self.label)

        #go live
        msg = prefix + '/key/live'
        d3script.sendOscMessage(oscDev, msg)

        self.close()


class GetCuesFromCurrentTrack(Widget):
    cue = ''
    user = ''
    cuelist = ''
    label = ''
    eosCuesFetchInProgress = False
    eosCueListLength = 0
    eosCueNumbers = []
    eosCueDataReceivedCount = 0

    oscServer = None

    def __init__(self):

        self.user, self.cuelist, self.oscDeviceName = _getEosPersistentValues()

        self.oscDevices = resourceManager.allResources(OscDevice)
        self.oscDeviceIndex = 0
        for idx, item in enumerate(self.oscDevices):
            if item.description == self.oscDeviceName:
                self.oscDeviceIndex = idx
                break

        self.cue, self.label = _getTagAndNoteForSectionAtPlayhead()

        Widget.__init__(self)

        d3script.log('Eoslink', "test")

        builtWidget = _buildEosBaseWidget('Scan44', 'Scan223', self.compareEosCuesWithCurrentTrack, self, True)

        d3gui.root.add(builtWidget)

    def compareEosCuesWithCurrentTrack(self):

        self.getD3Cues()
        self.eosGetAllCuesForList()

    def getD3Cues(self):
        d3script.log('Eoslink', "Getting Cues")

        numberOfCues = state.track.tags.n()
        d3script.log('wow', str(numberOfCues))

        cueList = []

        # Iterate through tag list and check if tag is a cue
        for i in range(numberOfCues):
            tagName = state.track.tags.getV(i)
            if tagName.startswith("CUE"):
                d3script.log("Found Cue", tagName)

                cueNumber = tagName.split(' ')[1]

                cueList.append(cueNumber)

        return cueList

    def inititateOscServer(self, oscDev):
        d3script.log('Eoslink', "Initiating OSC Server")
        d3script.log('IP', oscDev.sendIPAddress)
        d3script.log('Port', str(oscDev.sendPort))

        # socketServ = SocketServer.ThreadingMixIn

        receiveIPAddress = "127.0.0.1"
        d3script.log("receiveip", receiveIPAddress)

        # oscServer = OSCServer((receiveIPAddress, oscDev.receivePort))

        self.oscServer = ThreadingOSCServer((receiveIPAddress,8002))
        d3script.log('Eoslink', "Finished Initiating OSC server")

    def eosGetAllCuesForList(self):

        d3script.log('Eoslink', "Starting to get eos cues")

        if (self.cuelist == '') or (self.user == ''):
            d3script.log('EosLink', 'Missing list, cue, or user number.  Not sending a message.')
            self.close()
            return

        # Store Values for next time
        _setEosPersistentValues(self.user, self.cuelist, self.oscDevices[self.oscDeviceIndex].description)

        oscDev = self.oscDevices[self.oscDeviceIndex]

        self.inititateOscServer(oscDev)

        receiveCueCountAddress = "/eos/out/get/cue/" + self.cuelist + "/count"

        self.oscServer.addMsgHandler(receiveCueCountAddress, self.processEosCueListLength)
        self.oscServer.addMsgHandler("/eos/out/get/cuelist/", self.processEosCueData)
        self.oscServer.addMsgHandler("/samtest", self.samtest)


        # self.oscServer.serve_forever()

        d3script.log("server", "osc server serving")


        self.eosCuesFetchInProgress = True

        # prefix = '/eos/user/' + self.user

        msg = '/eos/get/cue/' + self.cuelist + '/count'
        d3script.sendOscMessage(oscDev, msg)

        # while self.eosCuesFetchInProgress:
        #     d3script.log("EosFetch", "Fetch Still in progress")
        #     sleep(0.01)

        # Iterate through eos cuelist

        d3script.log("Cue List Found Length", str(self.eosCueListLength))

        for i in range(self.eosCueListLength):
            msg = '/eos/get/cue/' + self.cuelist + '/index/' + i
            d3script.sendOscMessage(oscDev, msg)


        # while(self.eosCueListLength != self.eosCueDataReceivedCount):
        #     d3script.log("eos", "Not matching. " + self.eosCueListLength + " expected and " + self.eosCueDataReceivedCount + " received.")
        #     sleep(1.0)

        d3script.log("Eos", "FINISHEDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD")

        # d3script.log("Eoslink", firstCue)

        # d3script.log("number of cues", str(len(cueList)))


    def processEosCueListLength(self, length):
        d3script.log("AAAAAAAAcue list length", str(length))
        self.eosCueListLength = length
        self.eosCuesFetchInProgress = False

    def processEosCueData(self, data):

        d3script.log("cue data: ", str(data))
        # self.eosCueNumbers.appeand
        self.eosCueDataReceivedCount += 1

    def samtest(self):
        d3script.log("samtest", "samtttttttttttttttttttttttttttttest")

    
def createCueForCurrentSection():
    EosCueCreator()

def deleteCueForCurrentSection():
    EosCueDelete()

def retriggerCuePopup():
    EosCueRetrigger()

def getAllCuesFromCurrentTrack():
    GetCuesFromCurrentTrack()

def initCallback():
    d3script.log('EosLink','Initialized')

SCRIPT_OPTIONS = {
    "minimum_version" : 21, # Min. compatible version
    "init_callback" : initCallback, # Init callback if version check passes
    "scripts" : [
        {
            "name" : "Create Cue for Current Section", # Display name of script
            "group" : "EosLink", # Group to organize scripts menu.  Scripts menu is sorted a separated by group
            "bind_globally" : True, # binding should be global
            "help_text" : "Creates a cue for the current section Tag", #text for help system
            "callback" : createCueForCurrentSection, # function to call for the script
        },
        {
            "name" : "Delete Cue", # Display name of script
            "group" : "EosLink", # Group to organize scripts menu.  Scripts menu is sorted a separated by group
            "bind_globally" : True, # binding should be global
            "help_text" : "Delete's an Eos cue - assumes current section Tag", #text for help system
            "callback" : deleteCueForCurrentSection, # function to call for the script
        },
        {
            "name" : "Retrigger Cue", # Display name of script
            "group" : "EosLink", # Group to organize scripts menu.  Scripts menu is sorted a separated by group
            "bind_globally" : True, # binding should be global
            "help_text" : "Sends 'GO TO CUE ENTER' to retrigger eos and snap d3 in line", #text for help system
            "callback" : retriggerCuePopup, # function to call for the script
        },
        {
            "name": "Get all d3 Cues",  # Display name of script
            "group": "EosLink",  # Group to organize scripts menu.  Scripts menu is sorted a separated by group
            "bind_globally": True,  # binding should be global
            "help_text": "Gets all d3 cues from current track",  # text for help system
            "callback": getAllCuesFromCurrentTrack,  # function to call for the script
        }
        ]

    }
