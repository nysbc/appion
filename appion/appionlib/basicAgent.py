from appionlib import slurmHost 
from appionlib import apConfig
import sys

class BasicAgent(object): 
    '''
    Base Class of apAgent that does not need database connection, just .appion.cfg
    style configuration file.
    '''
    def __init__(self, configFile=None):
        if configFile:
            self.configFile = configFile
        self.processingHost = None

    def createProcessingHost(self, command, jobType):
        if not self.configFile:
            raise ValueError ("Could not create processing host object, configuration file is not defined") 
        
        configDict = apConfig.parseConfigFile(self.configFile)

        try:
            processingHostType = configDict['ProcessingHostType'].upper()
            if 'SLURM' == processingHostType.upper():
                processingHost = slurmHost.SlurmHost(command, jobType, configDict)
            else:
                sys.stderr.write("Unknown processing host type, using default\n")
                processingHost = slurmHost.SlurmHost(command, jobType, configDict)
            
        except (KeyError, AttributeError):
            sys.stderr.write("Could not determine processing host type, using default\n")
            processingHost = slurmHost.SlurmHost(command, jobType, configDict)
 
        return processingHost

##
    #
    
    def Main(self,command):
        '''
        Execute one shell command on processingHost
        '''
        self.processingHost = self.createProcessingHost()
        self.processingHost.executeCommand(command)
