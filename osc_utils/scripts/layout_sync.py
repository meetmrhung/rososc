#!/usr/bin/env python

# -*- coding: utf-8 -*-
# layout_sync.py
#
# Copyright (c) 2011, Michael Carroll
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
# * Neither the name of the copyright holders nor the names of any
#   contributors may be used to endorse or promote products derived
#   from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""

Python script and helper class for loading layouts to TouchOSC.

layout_sync.py provides a command line tool for programmatically loading TouchOSC
layout files to the TouchOSC iPhone/iPad application without the need for the 
TouchOSC editor program.  

This was reverse-engineered from Wireshark logs of the actual TouchOSC layout 
editor.  The editor regsiters a bonjour service of type _touchosc._tcp and then 

"""

__author__ = "Michael Carroll <carroll.michael@gmail.com>"

import roslib; roslib.load_manifest('osc_utils')
import bonjour

import sys
import socket
import zipfile
import os
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

def defaultError(msg,*args):
    """
    Default handler for error messages.  Can be overridden with the logging facility
    of your choice

    @type msg: str
    @param msg: Message to be displayed as an error message.
    @param args: format-string arguments, if necessary
    """
    sys.stderr.write("Layout Server Error: %s\n"%(msg%args))

def defaultInfo(msg,*args):
    """
    Default handler for messages.  Can be overridden with the logging facility of
    your choice.

    @type msg: str
    @param msg: Message to be displayed as a message.
    @param args: format-string arguments, if necessary
    """
    sys.stdout.write("Layout Server Info: %s\n"%(msg%args))

def make_layoutHandler_class(layoutFile):
    """
    Function to generate a class that extends BaseHTTPRequest Handler.

    @type layoutFile: str
    @param layoutFile: Path to the layout file to be loaded to the TouchOSC app.
    """
    #TODO: Do HTTPRequestHandler the proper "Python way".
    # This is sort of a hack.  The way that this should probably be done:
    # 1. Extend the HTTPServer class to take "layoutFile" as part of the constructor.
    # 2. In my overridden do_GET function in the LayoutHTTPRequestHandler, I should
    # then take advantage of the instance variable "server" which points to the 
    # overrideen HTTPServer class.  I should be able to get to all of the instance
    # variables of the HTTPServer class through that "server" variable.
    #
    # That is what I tried, but couldn't get working.  Because this is not a really
    # mission-critical application, this will work for now.
    class LayoutHTTPRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            f = zipfile.ZipFile(layoutFile,"r")
            print(f.read("index.xml"))
            try:
                self.send_response(200)
                self.send_header('Content-type','application/touchosc')
                self.send_header('Content-Disposition',
                                 'attachment; filename="%s"'%(
                                     os.path.basename(layoutFile)))
                self.end_headers()
                self.wfile.write(f.read("index.xml"))
            except Exception:
                import traceback
                traceback.print_exc(f=sys.stdout)
            return
    return LayoutHTTPRequestHandler

class LayoutServer():
    """docstring for LayoutServer"""
    def __init__(self, arg):
        super(LayoutServer, self).__init__()
        self.arg = arg
        

def main(argv, stdout):
    usage = "usage: %prog [options] /path/to/layout.touchosc"
    parser = OptionParser(usage=usage)
    parser.add_option("-p","--port",action="store",type="int",dest="port",
            default=9658,
            help="Port that the layout server will host on.")
    parser.add_option("-n","--name",action="store",type="string",dest="name",
            default="OSC Layout Server on %s"%socket.gethostname(),
            help="Name that will appear in TouchOSC's Server List")

    (options,args) = parser.parse_args(argv)
    if len(args) < 2:
        parser.error("Please specify a layout file.")
        sys.exit(1)
    
    layoutFilePath=args[1];

    if not os.path.lexists(layoutFilePath):
        parser.error("Layout file not found: %s"%(layoutFilePath))
        sys.exit(1)


    b = bonjour.bonjour(options.name,options.port,'_touchosceditor._tcp')
    b.run_register()
    server = HTTPServer(('',options.port),make_layoutHandler_class(args[1]))

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.socket.close()
        b.stop_register()



if __name__ == '__main__':
    from optparse import OptionParser

    main(sys.argv, sys.stdout)
