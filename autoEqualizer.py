#!/usr/bin/env python

import os
import sys
import threading
import signal

from time import sleep

from qt import *

try:
    from dcopext import DCOPClient, DCOPApp
except ImportError:
    sys.stderr.write("Err!!! I can't find the dcopext module.\n")
    os.popen( "kdialog --sorry 'PyKDE3 (KDE3 bindings for Python) is required for this script.'" )
    raise

#class Notification( QCustomEvent ):
class Notification( QCustomEvent ):
    __super_init = QCustomEvent.__init__
    def __init__( self, str ):
        self.__super_init(QCustomEvent.User + 1)
        self.string = str

class autoEqualizer( QApplication):
    """ The main application, also sets up the Qt event loop """

    def __init__( self, args ):
        QApplication.__init__( self, args )

	# create a new DCOP-Client
	self.client = DCOPClient()
	
	# connect the client to the local DCOP-Server
	if self.client.attach() is not True:
	    os.popen( "kdialog --sorry 'Could not connect to local DCOP server. Something weird happened.'" )
	    sys.exit(1)
	    
	# create a DCOP-Application-Object to talk to Amarok
	self.amarok = DCOPApp('amarok', self.client)

        debug( "Started." )

        # Start separate thread for reading data from stdin
        self.stdinReader = threading.Thread( target = self.readStdin )
        self.stdinReader.start()

        self.readSettings()

    def readSettings( self ):
        """ Reads settings from configuration file """

        try:
            foovar = config.get( "General", "foo" )

        except:
            debug( "No config file found, using defaults." )


############################################################################
# Stdin-Reader Thread
############################################################################

    def readStdin( self ):
        """ Reads incoming notifications from stdin """

        while True:
            # Read data from stdin. Will block until data arrives.
            line = sys.stdin.readline()
	    debug ("Line is %s.\n" % (line) )

            if line:
                qApp.postEvent( self, Notification(line) )
            else:
                break


############################################################################
# Notification Handling
############################################################################

    def customEvent( self, notification ):
        """ Handles notifications """

        string = QString(notification.string)
        debug( "Received notification: " + str( string ) )

        if string.contains( "configure" ):
            self.configure()

        if string.contains( "engineStateChange: play" ):
	    debug("Play even triggered.")
            self.engineStatePlay()

        if string.contains( "engineStateChange: idle" ):
            self.engineStateIdle()

        if string.contains( "engineStateChange: pause" ):
            self.engineStatePause()

        if string.contains( "engineStateChange: empty" ):
            self.engineStatePause()

        if string.contains( "trackChange" ):
	    debug("Track change event occured")
            self.trackChange()

# Notification callbacks. Implement these functions to react to specific notification
# events from Amarok:

    def configure( self ):
        debug( "configuration" )

        self.dia = ConfigDialog()
        self.dia.show()
        self.connect( self.dia, SIGNAL( "destroyed()" ), self.readSettings )

    def engineStatePlay( self ):
        """ Called when Engine state changes to Play """
	debug("Calling equalizer.\n")
	self.setEqualizer()

    def engineStateIdle( self ):
        """ Called when Engine state changes to Idle """
        pass

    def engineStatePause( self ):
        """ Called when Engine state changes to Pause """
        pass

    def engineStateEmpty( self ):
        """ Called when Engine state changes to Empty """
        pass

    def trackChange( self ):
        """ Called when a new track starts """
	debug ("Track Change event called.\n")
	self.setEqualizer()


    def getGenre(self):
	# get the Genre from the current song.
	retval, genre = self.amarok.player.genre()
	if retval is not True:
	    err()
	else:
	    return genre

    def setEqualizer(self):
	# set the equalizer accordingly
	# TODO: It would be good to have a list of preset equalizers
	# and match them

	self.genre = self.getGenre()
	retval, success = self.amarok.player.setEqualizerPreset(self.genre)
	if retval is not True:
	    err()
	else:
	    self.amarok.playlist.popupMessage("Activated equalizer preset -> %s" % (self.genre) )

    def equalizerState(self):
	# check if the equalizer is on or not
	# FIXME: Currently, it looks like dcopext has a bug
	# even though I try to set the equalizer to on, it doesn't
	# so for now we will check if the equalizer is on or not and
	# enable it using the dcop command
	retval, equalizerState = self.amarok.player.equalizerEnabled()
	if not equalizerState:
	    os.system( "dcop amarok player setEqualizerEnabled True" )



############################################################################

def debug( message ):
    """ Prints debug message to stdout """
    f = open("/tmp/amarok.foo", 'w')
    f.writelines(message)
    f.flush()
    f.close()

    #print debug_prefix + " " + message

def main( ):
    app = autoEqualizer ( sys.argv )

    app.exec_loop()

def onStop(signum, stackframe):
    """ Called when script is stopped by user """
    pass

if __name__ == "__main__":
    mainapp = threading.Thread(target=main)
    mainapp.start()
    signal.signal(15, onStop)
    # necessary for signal catching
    while 1: sleep(120)
