* Install driver from Blackmagic: “ATEM Switchers” (currently 3.4)
* Reboot
* Open Atem Setup Utlility, update device firmware if applicable



Installation atemclient OS-X (10.8.2)
==========================
Homebrew
--------------
Make sure you have [homebrew](http://mxcl.github.com/homebrew/) installed since the rest of this document is written assuming you have it.

    brew install git

Command Line Utilities for Xcode
-------------------------------------------
Go to http://connect.apple.com download and install the Command Line Utilities for Xcode. You will need a free Apple Developer Account for the download. The package contains everything required to compile/link applications for use on the commandline. If you already have Xcode installed this step is not required. It’s also a requirement for homebrew so you might already have installed it.

Atemclient
--------------
Install required packages using brew
    brew install git
    brew install ffmpeg

Checkout the latest version of atemclient from github. Change your working directory to a desired installation path.
    cd ~
    git clone https://github.com/kyrios/atemclient.git

Configuration
==========
There is no seperate configuration file for atemclient yet. All configuration is done in the script itself. (Meh..)

Open atemclient.py in your favorite editor and search for the “CONFIGURATION” part at the bottom of the file. Pay attention to the ffmpeg encoder settings. The example given assumes that your connection to the knive backend is reachable with at least 1Mbit/s. This means that if you stream from your home to a dedicated server somewhere you need for example 16/1Mbit DSL.

Running atemClient
==============
make sure the AtemTV Studio is connected to your computer and turned on.
Start atemclient with some ‘secret’ and the endpoint location.
    ./atemClient.py knivebackend.example.com:3333 thisIsMySecr3t



