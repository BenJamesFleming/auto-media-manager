#
# © 2016. Ben Fleming.
# Python Auto Torrent Placer
#
# Import required moduals
import os
import sys
import json
import time
import glob
import random
import smtplib
from pytvdbapi import api
from pytvdbapi.error import ConnectionError, BadData, TVDBIndexError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime

# Global Variables
config_file = 'config_local.json'
can_acces = False
max_loop = 10
debug = 'True'
email = 'False'
uTorrentConfig = ''
baseDir = ''
moveDir = ''
dirFormat = '_'
fileExtentions = [
    '.mp4',
    '.mkv'
]
name_formats = [
    ' ',
    '_',
    '.',
    ''
]

# Get Variables Parsed From uTorrent
torrentHash = sys.argv(1)
torrentName = sys.argv(2)

# SetUp Date
now = datetime.datetime.now()

# Check for Config.json file
if os.path.isfile(config_file):

    # Open Config.json file
    with open(config_file) as data_file:

        # Load json
        jsonData = json.load(data_file)
        email = jsonData['email']
        uTorrentConfig = jsonData['uTorrent']
        moveDir = jsonData['movedir']
        dirFormat = jsonData['dirformat']
        fileExtentions = jsonData['fileextentions']
        name_formats = jsonData['nameformats']
        for show in jsonData['shows'].split('|'):
            show = show.split(';');
            shows.append([show[0], (len(show) == 2 ? show[1] : None)])

# if no config.json is found run error
else:
    error("No "+config_file+" file found")

# List of shows (strings) to watch the direcotry for
watchArray = []

# Connect To uTorrent
con = Connection(uTorrentConfig["host"], uTorrentConfig["username"], uTorrentConfig["password"])
utorrent = Falcon(con, con.utorrent())

# Format the name ready for watchdog
def formatName(string, videoformat):
    return '*'+string+'*'+videoformat

# Build the watchArray
for show in shows:
    show_name = show[0]

    # Check show name for " "
    try:
        if show_name.index(" ") > -1:

            # Loop through each nameforamt
            for nameformat in name_formats:

                # Loop through each extention
                for extention in fileExtentions:
                    string = show_name.replace(" ", nameformat)
                    string = formatName(string, extention)

                    # Append fotmatted show name to watch array
                    watchArray.append(string)

                    # If in debug mode print the show name
                    if debug == 'True':
                        print(string)

    # If ValueError skip nameformats
    except ValueError:

        # Loop through eaxh extention
        for extention in fileExtentions:
            string = formatName(show_name, extention)

            # Append fotmatted show name to watch array
            watchArray.append(string)

            # If in debug mode print the show name
            if debug == 'True':
                print(string)


def addToLog(msg):

    global now

    preMsg="["+now.strftime("%Y-%m-%d %H:%M")+"] "
    fileName=now.day+"_log.txt"

    # Create Dir If Needed
    if not os.path.exists(path):
        open(path, 'a').close()

    # Write To File
    with open(path, 'a') as f:
        f.write(preMsg+msg+"\n")

def moveTorrent():

    global con
    global utorrent
    global torrentHash

    try:
        torrent = [t for h, t in sorted( utorrent.torrent_list( ).items( ), key = lambda x: getattr( x[1], "name" ), reverse = False ) if t.return_attr()["hash_code"] == torrentHash][0]
        torrent_attr = torrent.return_attr()
        torrent_name = torrent_attr["name"]
        torrent_attr["attr"] = torrentparser.parse(torrent_name)

        if torrent_attr["progress"] != "100":
            addToLog("ERROR: Torrent Not Finished, Skipping File Movement")
            return

        # Remove From uTorrent & Server
        torrent.remove()

        # Sleep To give uTorrent Time
        time.sleep(2)

        # Create Dir If Needed
        if not os.path.exists(path):
            os.makedirs(path)

        # Move File
        os.rename(config["localDownloadFolder"]+"/"+torrent_name, path+"/"+torrent_name)

        # Add To Log
        addToLog("INFO: Torrent '"+torrent_name+"' Moved From '"+config["localDownloadFolder"]+"' to '"+path+"'")

    except Exception as e:
        addToLog("ERROR: Error While Attemping To Move Torrent!, "+str(e))

    return

# Check If Torrent Is In Config
if any(show in torrentName for show in watchArray):
    moveTorrent()
