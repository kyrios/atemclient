#!/usr/bin/env python
#
# atemClient.py
# Copyright (c) 2012 Thorsten Philipp <kyrios@kyri0s.de>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in the 
# Software without restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, 
# and to permit persons to whom the Software is furnished to do so, subject to the
# following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION 
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import sys, os
# try:
#     scriptdir = os.path.dirname(os.path.realpath(__file__))
#     knivedir = scriptdir + os.path.sep + 'knive'
#     sys.path.insert(0,knivedir)

print sys.path

from knive import foundation
from knive import files
from knive import ffmpeg
from knive import tcpts
from zope.interface import implements
from twisted.application import service, internet
from twisted.internet.protocol import ReconnectingClientFactory, Protocol
from twisted.protocols.basic import LineReceiver
from twisted.python import log, usage, procutils
from twisted.internet import reactor
from twisted.internet.defer import Deferred


import types
import ConfigParser
import logging


class BMDSSDataProtocol(Protocol):
    """docstring for BMDSSDataProtocol"""
    bytes = 0
    iterations = 0
    lastBytes = 0
    service = None

    def startReceiving(self):
        """docstring for start"""
        log.msg("Starting stream receiver")
        self.transport.write('receive -id %s -transport tcp\n' % self.factory.signalingFactory.channel)
        self.progress()

    def dataReceived(self,data):
        """docstring for dataReceived"""
        self.bytes += len(data)
        self.factory.service.sendDataToAllOutlets(data)

    def progress(self):
        """docstring for progress"""
        self.iterations += 1
        deltabytes = self.bytes - self.lastBytes
        self.lastBytes = self.bytes
        log.msg("Received %s bytes (%s kbps) from BM Atem TV Studio" % (deltabytes,deltabytes / 5 * 8 / 1024))
        reactor.callLater(5,self.progress)

class BMDSSLineProtocol(LineReceiver):
    lastCommand = None
    lastCommandType = None
    commandQueue = []
    initializing = True
    lineFree = False
    Set = False
    stopEncodingDeferred = None
    encodingSet = False
    gotResponse = True

    def connectionMade(self):
        log.msg("Connection established")
        self.delimiter = '\n'
        self.sendCommand('notify', force=True)
        self.sendCommand('get', 'device')
        self.sendCommand('get', 'encoding')
        self.sendCommand('validate', 'encoding', '-fps 50p -srcx 0 -srcy 0 -srcw 1280 -srch 720 -dstw 1280 -dsth 720 -vkbps 5500 -profile high -level 40 -cabac 1 -bframes 1 -arate 48000 -achannels 2 -abits 16 -akbps 256 -preset 1')
        self.sendCommand('set', 'encoding', '-fps 50p -srcx 0 -srcy 0 -srcw 1280 -srch 720 -dstw 1280 -dsth 720 -vkbps 5500 -profile high -level 40 -cabac 1 -bframes 1 -arate 48000 -achannels 2 -abits 16 -akbps 256 -preset 1')
        #reactor.callLater(10,self.stopEncoding)

    def workFromQueue(self):
        """docstring for workFromQueue"""
        if len(self.commandQueue) > 0:
            item = self.commandQueue.pop(0)
            if type(item) == types.MethodType:
                item()
            else:
                arguments = None
                command = None
                try:
                    commandtype, command, arguments = item.split(':::')
                except ValueError:
                    try:
                        commandtype, command = item.split(':::')
                    except ValueError:
                        commandtype = item
                
            
                self.sendCommand(commandtype,command,arguments)
        reactor.callLater(1,self.workFromQueue)
            
    def refreshDeviceStatus(self):
        if self.lineFree:
            self.sendCommand('get','device')
        else:
            self.commandQueue.append(self.refreshDeviceStatus)
          
    def startEncoding(self):
        """docstring for startEncoding"""
        log.msg('Starting encoding')
        if self.lineFree:
            if not self.encodingSet:
                raise(Exception('Encoding parameters not valid. Can\'t start'))
            if self.factory.deviceStatus == 'booting':
                log.msg('Device is booting. Waiting')
                reactor.callLater(5,self.startEncoding)
            elif self.factory.deviceStatus != 'idle':
                log.msg('Device not idle. Restarting (%s)' % self.factory.deviceStatus)
                self.commandQueue.append(self.stopEncoding)
                reactor.callLater(2,self.refreshDeviceStatus)
                reactor.callLater(3,self.startEncoding)
            else:
                self.sendCommand('start')
        else:
            self.commandQueue.append(self.startEncoding)
        
    def stopEncoding(self):
        self.stopEncodingDeferred = Deferred()
        if self.lineFree:
            if self.factory.deviceStatus != 'encoding':
                log.msg('Device not encoding. Can not stop')
                return
            else:
                self.sendCommand('stop')
        else:
            self.commandQueue.append(self.stopEncoding)
        return self.stopEncodingDeferred
            
    def stopEncodingFinal(self):
        """docstring for stopEncodingFast"""
        self.transport.write('stop -id %s\n' % (self.factory.channel))
        self.transport.loseConnection()
        log.msg("Sent stop")
        
    def sendCommand(self,commandtype,command=None,arguments=None,force=False):
        """docstring for sendCommand"""
        if (self.lineFree or force):
            self.lineFree = False
            self.lastCommand = command
            self.lastCommandType = commandtype
            if arguments:
                log.msg('\t\t> > > %s -id %s -%s %s' % (commandtype,self.factory.channel,command,arguments))
                self.transport.write('%s -id %s -%s %s\n' % (commandtype,self.factory.channel,command,arguments))
            elif command:
                log.msg('\t\t> > > %s -id %s -%s' % (commandtype,self.factory.channel,command))
                self.transport.write('%s -id %s -%s\n' % (commandtype,self.factory.channel,command))
            else:
                if commandtype == 'notify':
                    log.msg('\t\t> > > %s' % (commandtype))
                    self.transport.write('%s\n' % (commandtype))
                else:
                    log.msg('\t\t> > > %s -id %s' % (commandtype,self.factory.channel))
                    self.transport.write('%s -id %s\n' % (commandtype,self.factory.channel))
        else:
            if arguments:
                self.commandQueue.append(':::'.join([commandtype,command,arguments]))
            elif command:
                self.commandQueue.append(':::'.join([commandtype,command]))
            else:
                self.commandQueue.append(':::'.join([commandtype]))
                
                
    def printDeviceStatus(self):
        """docstring for printDeviceStatus"""
        log.msg("%s >>>>>> %s" % (self.factory.deviceIdentifier,self.factory.deviceStatus.upper()))
            
    def lineReceived(self,line):
        """docstring for lineReceived"""
        log.msg("\t\t< < < " +line)

        if self.initializing:
            if line.startswith('arrived'):
                paras = line.split(' ')
                self.factory.deviceIdentifier = " ".join(paras[2:])
            if line.startswith('input'):
                self.initializing = False
                self.lineFree = True
                paras = line.split(' ')
                self.factory.channel = paras[1]
                log.msg("Connected to: %s Channel: %s" % (self.factory.deviceIdentifier,self.factory.channel))
                self.workFromQueue()
        else:
            
            if(line.startswith('OK')):
                 #log.msg("Last Command: %s" % self.lastCommand)
                 if self.lastCommand == 'device':
                     #log.msg('-----')
                     #log.msg(line)
                     self.factory.deviceStatus = line.split(' ').pop()
                     self.printDeviceStatus()
                     if self.factory.deviceStatus == 'idle':
                         try:
                             self.stopEncodingDeferred.callback(None)
                         except:
                             pass
                     #log.msg('-----')
                 elif self.lastCommandType == 'get' and self.lastCommand == 'encoding':
                      pass
                 elif self.lastCommandType == 'validate' and self.lastCommand == 'encoding':
                     log.msg('<- Encoding settings will be okay')
                 elif self.lastCommandType == 'set' and self.lastCommand == 'encoding':
                     log.msg('<- Encoding settings are okay')
                     self.encodingSet = True
                     self.factory.setupComplete = True
                 elif self.lastCommandType == 'stop':
                     log.msg('<- Encoder stoping')
                 elif self.lastCommandType == 'start':
                     log.msg('<- Encoder starting')
            elif(line == 'device: %s encoding' % self.factory.channel):
                self.factory.deviceStatus = 'encoding'
                self.printDeviceStatus()
            elif(line == 'device: %s stopping' % self.factory.channel):
                self.factory.deviceStatus = 'stopping'
                self.printDeviceStatus()
            elif(line == 'device: %s idle' % self.factory.channel):
                self.factory.deviceStatus = 'idle'
                self.printDeviceStatus()
                try:
                    self.stopEncodingDeferred.callback(None)
                except:
                    pass
            elif(line.startswith('Error')):
                log.err('Problem communicating with device. : %s' % line)
            elif(line == 'device: %s booting' % self.factory.channel):
                self.factory.deviceStatus = 'booting'
                self.printDeviceStatus()
            else:
                log.err('Received unexpected data: %s' % line)
            self.lineFree = True
            self.workFromQueue()
        

class BMDSSLineFactory(ReconnectingClientFactory):
    channel = None
    deviceIdentifier = None
    deviceStatus = None
    setupComplete = False

    def buildProtocol(self, addr):
         self.protocol = BMDSSLineProtocol()
         self.protocol.factory = self
         return self.protocol

    def clientConnectionFailed(self, connector, reason):
        log.msg('connection failed: %s %s' % (connector,reason))
        if self.continueTrying:
            self.connector = connector
            self.retry()
    
    def clientConnectionLost(self, connector, reason):
        log.err('connection lost: %s' % reason)
        if self.continueTrying:
            self.connector = connector
            self.retry() 
    # def clientConnectionLost(self, connector, reason):
    #     print 'Lost connection.  Reason:', reason

    # def clientConnectionFailed(self, connector, reason):
    #     print 'Connection failed. Reason:', reason

    def stopEncoding(self):
        """docstring for stopEncoding"""
        return(self.protocol.stopEncoding())
        
    def startEncoding(self):
        """docstring for startEncoding"""
        self.protocol.startEncoding()

class BMDSSDataFactory(ReconnectingClientFactory):
    """docstring for BMDSSDataFactory"""
    signalingFactory = None
    
    def buildProtocol(self, addr):
         self.protocol = BMDSSDataProtocol()
         self.protocol.factory = self
         return self.protocol

    def clientConnectionFailed(self, connector, reason):
        log.err('connection failed: %s' % reason)
        if self.continueTrying:
            self.connector = connector
            self.retry()
    
    def clientConnectionLost(self, connector, reason):
        log.err('connection lost: %s' % reason)
        if self.continueTrying:
            self.connector = connector
            self.retry()
         
    # def clientConnectionLost(self, connector, reason):
    #     print 'Lost connection.  Reason:', reason

    # def clientConnectionFailed(self, connector, reason):
    #     print 'Connection failed. Reason:', reason

    def setSignaling(self,signalingFactory):
        """docstring for setSignaling"""
        self.signalingFactory = signalingFactory

    def startReceiver(self):
        """docstring for startReceiver"""
        print "STARTING RECEIVER"
        if self.signalingFactory.setupComplete and self.protocol:
            #start Receiver
            self.protocol.startReceiving()
            self.signalingFactory.startEncoding()
        else:
            print "Not ready yet"
            #print self.signalingFactory
            #print self.signalingFactory.deviceStatus
            reactor.callLater(2,self.startReceiver)


        
class AtemStudioClient(foundation.KNInlet, service.MultiService):    
    """Connects to a Blackmagic Atem TV Studio and receives the captured video"""
    implements(service.IServiceCollection)

    def __init__(self,host='localhost',port=13823):
        super(AtemStudioClient,self).__init__(name='AtemStudioClient')
        self.log = logging.getLogger('Atem %s:%s' % (host,port))
        self.host = host
        self.port = port
        self.services = []
        self.namedServices = {}
        self.parent = None
        
        self.atemSignallingFactory = BMDSSLineFactory()
        self.atemDataFactory = BMDSSDataFactory()
        self.atemDataFactory.service = self
            

        
        self.log.debug('Setup complete')

        # atemSignalling.setName('Atem Signalling Connection')
        # atemSignalling.setServiceParent(self)
        # atemData.setName('Atem Data Connection')
        # atemData.setServiceParent(self)


    def _willStart(self):
        """Preparations"""
        self.atemDataFactory.setSignaling(self.atemSignallingFactory)

        
    def _start(self):
        log.msg("Starting %s" % self)
        atemSignalling = internet.TCPClient(self.host, self.port, self.atemSignallingFactory)
        atemData = internet.TCPClient(self.host, self.port, self.atemDataFactory)
        atemSignalling.startService()
        atemData.startService()

        self.atemDataFactory.startReceiver()



logging.basicConfig(level=logging.DEBUG)
observer = log.PythonLoggingObserver()
observer.start()

config = ConfigParser.SafeConfigParser()
config.add_section('Paths')
# config.set('Paths','ffmpeg','/home/kyrios/tpffmpeg/build/bin/ffmpeg')


config.add_section('General')

def usage(exitPar=1):
    """docstring for usage"""
    print "Usage: %s [options] <hostname>" % scriptname
    if exitPar:
        sys.exit(1)

startupargs = sys.argv
scriptname = startupargs.pop(0)
try:
    kniveServerHostname = startupargs.pop()
except IndexError:
    usage()
print "Hostname %s" % kniveServerHostname




atemClient = AtemStudioClient()


#-vcodec libx264 -vpre veryfast -vpre main -b 500k -crf 22 -threads 0 -level 30 -r 25 -g 25 -async 2 -
#masterEncoder = ffmpeg.FFMpeg(ffmpegbin=config.get('Paths','ffmpeg'),encoderArguments=dict(vcodec="libx264",vpre=("fast","main"),crf="22",b='800k',maxrate='1100k',bufsize='1100k',threads=0,level="30",r=25,g=25,acodec='copy',f="mpegts"))
try:
    ffmpegbinpath = config.get('Paths','ffmpeg')
except Exception, e:
    ffmpegbinpath = procutils.which('ffmpeg')[0]
    print 'Using ffmpeg: "%s"' % ffmpegbinpath
else:
    pass
masterEncoder = ffmpeg.FFMpeg(ffmpegbin=ffmpegbinpath,encoderArguments=dict(vcodec="libx264",vpre=("normal","main"),crf="27",b='300k',maxrate='350k',bufsize='350k',threads=0,level="30",r=25,g=25,async=2,acodec='libfaac',ab='128k',f="mpegts"))
masterEncoder.addOutlet(files.FileWriter('../',filename='atem_encoded',suffix='.ts'))
masterEncoder.addOutlet(tcpts.TCPTSClient(kniveServerHostname,3333,secret='123123asd'))
masterEncoder.setInlet(atemClient)



atemClient.start()
reactor.run()
