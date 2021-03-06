#
# © 2016. Ben Fleming.
# Python Auto Torrent Placer
#
# Import required moduals
import os
import sys
import json
import time
import random
import smtplib
from pytvdbapi import api
from pytvdbapi.error import ConnectionError, BadData, TVDBIndexError
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Global Variables
can_acces = False
max_loop = 10
debug = 'True'
email = 'False'
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

# Check for Config.json file
if os.path.isfile('config.json'):

    # Open Config.json file
    with open('config.json') as data_file:

        # Load json
        jsonData = json.load(data_file)
        debug = jsonData['debug']
        email = jsonData['email']
        baseDir = jsonData['basedir']
        moveDir = jsonData['movedir']
        dirFormat = jsonData['dirformat']
        fileExtentions = jsonData['fileextentions']
        name_formats = jsonData['nameformats']
        shows = jsonData['shows']

# if no config.json is found run error
else:
    error("No config.json file found")

# List of shows (strings) to watch the direcotry for
watchArray = []

# Handle watchdog events
class HandleFileEvents(PatternMatchingEventHandler):

    # Set patterns as the watchArray
    patterns = watchArray

    # process event
    def process(self, event):

        # Check that event type == 'created'
        if event.event_type == 'created':

            # If debug is 'True' print new file
            if debug == 'True':
                print("File Added: "+event.src_path)

            # Get name with self.get_name()
            name = self.get_name(event)

            # Get season with self.get_substring()
            season = self.get_substring(event, [1,4])
            # Format season with self.format_season()
            season = self.format_season(event, season)

            # Get episode with self.get_substring()
            episode = self.get_substring(event, [4,7])
            # Format episode with self.format_season()
            episode = self.format_season(event, episode)

            # Get file extention with self.get_substring()
            extention = self.get_substring(event, [-4,'null'])

            # Build tempMoveDir string with show info
            tempMoveDir = moveDir+name['dir'].replace(" ",dirFormat).replace("__space__", " ")+'/Season_'+season[1]+'/'

            # If debug is 'True' print show info
            if debug == 'True':
                print("Name: "+name['name'])
                print("Season: "+season[0])
                print("Episode: "+episode[0])
                print("Extention: "+extention)
                print("Moved To: "+tempMoveDir)

            # Check that the file is openable
            for i in range(0, max_loop):

                # Try open the file
                try:
                    with open(event.src_path, 'rb') as _:
                        can_access = True
                        break

                # On KeyboardInterrupt break loop
                except KeyboardInterrupt:
                    break

                # If file is not openable sleep for 3 seconds
                except IOError:
                    time.sleep(3)

            # If the program can access the continue
            if can_access:

                # Build file_name string
                file_name = name['name'].replace(" ", ".")+"."+season[0]+episode[0]+extention

                # Rename file and move it to new direcotry
                if os.path.isdir(tempMoveDir) is not True: os.makedirs(tempMoveDir)
                os.rename(event.src_path, tempMoveDir+file_name)

                # If email['send'] == 'True' send email
                if email['send'] == 'True':

                    # Connect to TVDB and grab show info
                    db = api.TVDB('36139F469F704416', ignore_case=True, banners=True)

                    db_worked = True

                    imdb_id = ""
                    rating = ""
                    banner = None
                    fanart = None
                    ep_name = ""

                    email_body = None

                    # Try grab show info
                    try:
                        result = db.search(name['name'], 'en')
                        show = result[0]
                        show.update()

                    # The search did not generate any hits
                    except TVDBIndexError:
                        db_worked = False

                    # Handle the fact that the server is not responding
                    except ConnectionError:
                        db_worked = False

                    # The server responded but did not provide valid XML data
                    except BadData:
                        db_worked = False

                    else:
                        # Get episo from show
                        ep = show[int(season[1])][int(episode[1])]

                        # Get IMDB ID
                        imdb_id = show.IMDB_ID

                        # Get Rating
                        rating = show.Rating

                        # Get Banner Objects
                        banner = show.banner_objects[0]

                        # Extract fanart from banner objects
                        fanart = [b for b in show.banner_objects if b.BannerType == "fanart"]
                        fanart = fanart[random.randint(0,len(fanart)-1)].banner_url

                        # Get EpisodeName
                        ep_name = ep.EpisodeName

                        # Load show vars into object
                        template_vars = {
                            'name': name['name'],
                            'season': season[0],
                            'episode': episode[0],
                            'episodename': ep_name,
                            'rating': rating,
                            'IMDBID': imdb_id,
                            'backgroundurl': fanart
                        }

                        # Try open email tempalte and adding vars
                        try:
                            with open('email/email_01_tvdb.txt') as email_template:
                                email_body = email_template.read().format(**template_vars)

                        # On except pass
                        except:
                            pass

                    # If email failed to load, Load backup
                    if db_worked is False:

                        # Load show vars into object
                        template_vars = {
                            'name': name['name'],
                            'season': season[0],
                            'episode': episode[0]
                        }

                        # Try open email tempalte and adding vars
                        try:
                            with open('email/email_01_no_tvdb.txt') as email_template:
                                email_body = email_template.read().format(**template_vars)

                        # On except pass
                        except:
                            pass

                    # Make sure an email has been built
                    if email_body is not None:
                        # Build the subect string
                        subject = "New '"+name['name']+"' Episode | "+season[0]+episode[0]

                        # Send email
                        send_email(email["sender"], email["password"], email["recipient"], subject, email_body)

                # If the program can not access the file
                else:

                    # Print no access error
                    print("Error: The file can not be accessed by the program")

            # Print Done
            print("Done\n")

    # When file created process
    def on_created(self, event):
        self.process(event)

    # Format Season into [Lond, Short]
    def format_season(self, event, string):
        if string[1] == '0':
            return [string, string[2:]]
        else:
            return [string, string[1:]]

    # Format name
    def get_name(self, event):

        # Get path
        string = event.src_path

        # Trim off baseDir
        string = string.replace(baseDir, "")

        # Loop through shows
        for show in shows:

            # Loop through name_formats
            for nameformat in name_formats:

                # Format name with nameformat
                showName = show['name'].replace(" ", nameformat)

                # Try find showName in string
                try:
                    if string.index(showName) > -1:
                        return show

                # On ValueError pass
                except ValueError:
                    pass

    # Get substring (detail) of name
    def get_substring(self, event, substring):

        # Get path and trim off baseDir
        path = event.src_path.replace(baseDir, "")

        # Get name
        baseName = self.get_name(event)['name']

        # Loop through name_formats
        for nameformat in name_formats:

            # Format name with nameformat
            showName = baseName.replace(" ", nameformat)

            # Try find showName in path
            try:
                if path.index(showName) > -1:

                    # Trim off showName in path
                    path = path.replace(showName, "")
                    if substring[1] != 'null':
                        return path[substring[0]:substring[1]]
                    else:
                        return path[substring[0]:]

            # On ValueError pass
            except ValueError:
                pass

# Send email via smpt.gmail.com
def send_email(user, pwd, recipient, subject, body):

    # Build message
    msg = MIMEMultipart('alternative')
    # Set Subject
    msg['Subject'] = subject
    # Set From
    msg['From'] = user
    # Set To
    msg['To'] = recipient

    # Attach email to message
    msg.attach(MIMEText(body, 'html'))

    # Try to send email
    try:
        # Connect to smpt.gmail.com on port 587
        server = smtplib.SMTP("smtp.gmail.com", 587)
        # Send EHLO command
        server.ehlo()
        # Start TTLS command
        server.starttls()
        # Send EHLO command
        server.ehlo()
        # Login to Gmail
        server.login(user, pwd)
        # Send message
        server.sendmail(user, recipient, msg.as_string())
        # Close connection to server
        server.close()

        # If debug == 'True' print notifaction
        if debug == 'True':
            print('Email Sent')

    # If email failed print error
    except:
        print('Error: Email failed to send')

# Format the name ready for watchdog
def formatName(string, videoformat):
    return baseDir+'*'+string+'*'+videoformat

# Grab all shows in config and format them for PatternMatchingEventHandler
for show in shows:
    show_name = show['name']

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

# If in debug print new line
if debug == 'True':
    print("\n")

# Print error and exit
def error(err):
    sys.exit("Error: "+err)

# If in main file start watching direcotry
if __name__ == '__main__':
    observer = Observer()

    # Set watcher options
    observer.schedule(HandleFileEvents(), baseDir, recursive=True)

    # Start watching
    observer.start()

    # Try to sleep for 1 second
    try:
        while True:
            time.sleep(1)

    # On KeyboardInterrupt stop watching
    except KeyboardInterrupt:
        observer.stop()

    # Clean up the watch
    observer.join()
