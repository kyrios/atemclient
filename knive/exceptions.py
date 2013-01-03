#
# exceptions.py
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
"""Collection of Exceptions knive will eventually throw.

.. moduleauthor:: Thorsten Philipp <kyrios@kyri0s.de>

"""
class ServiceRunningWithoutInlet(Exception):
    """Raised when an IKNOutlet is started without a valid inlet. This IKNOutlet will not receive any data"""
    def something(self):
        pass

class CanNotStartError(Exception):
    """A service could not start successfully."""
    def something(self):
        pass

class ServiceRunningWithoutOutlets(Exception):
    """Raised when an IKNInlet is started without valid IKNOutlets to send data to."""
    def something(self):
        pass

class AlreadyRecording(Exception):
    """Raised when an already running recording is tried to start again."""
    def something():
        pass

class NoRecording(Exception):
    """Raised when trying to stop a not running episode."""
    def something():
        pass
        
        
        
        