import web, urllib2, time, os
from threading import Timer
#from MusicLibraryFunctions import *
from XMLLibraryParser import *

# ------------------------------ Here be variables you need to set --------------------------------------

# Base server address where the "iTunes Music" folder is shared
musicBaseUrl = "http://jarman.homedns.org:82/"

# the name of the client server as displayed in the selection menu
# currently this name cannot contain spaces, and possibly non-alphanumeric characters
clientName = "Jarman"

# The current servers DNS name, or the empty string if it does not exist. Do not preface with http://
# examples: "testdomain.com", "" 
clientAddress = ""

# The email address (gmail account) which is allowed to use the account. Empty string to allow everyone. 
# examples: "joe@gmail.com", "" 
allowedUser = "jarman@gmail.com"

# Location of the XML file for iTunes
libraryLocation = "\users\jarman\Music\MacBook iTunes\iTunes Library.xml"
#libraryLocation = "/Users/Jarman/Music/iTunes/iTunes Library.xml"

# The address of the main server
# This should remain the same
serverUrl = 'http://www.jarmanrogers.com/'

urls = (
    '/songs(.*)', 'songs',
    '/artists(.*)', 'artists',
    '/albums(.*)', 'albums',
    '/playlists(.*)', 'playlists',
    '/load', 'load'
)

render = web.template.render('templates/')

app = web.application(urls, globals())

# load the library and set the initial 
lib = XMLLibraryParser(libraryLocation)
libLastModified = os.path.getmtime(libraryLocation)

def getPlaylistContents(plid):    
    songs = [];
    for id in lib.playlists[plid]['songs']:
        if (lib.songs[id]['Kind'] != 'Apple Lossless audio file'):
            localLoc = lib.songs[id]['Location']
            localFolder = localLoc[localLoc.find('iTunes%20Music/')+15:]
            networkLoc = musicBaseUrl + localFolder
            songs.append([networkLoc,lib.songs[id]])
    return songs, lib.playlists[plid]['Name']

def getArtistSongs(artist):    
    songs = [];
    
    for id in lib.artists[artist]['songs']:
        localLoc = lib.songs[id]['Location']
        localFolder = localLoc[localLoc.find('iTunes%20Music/')+15:]
        networkLoc = musicBaseUrl + localFolder
        songs.append([networkLoc,lib.songs[id]])
    
    return songs

def getAlbumSongs(album):    
    songs = [];
    for id in lib.albums[album]:
        localLoc = lib.songs[id]['Location']
        localFolder = localLoc[localLoc.find('iTunes%20Music/')+15:]
        networkLoc = musicBaseUrl + localFolder
        songs.append([networkLoc,lib.songs[id]])
       
    return songs

def findSongs(s):
    cats = ['Name', 'Artist', 'Album']
    songs = [[], [], []]
    s = s.encode('latin-1').lower();


    for song,attributes in lib.songs.iteritems():
        for i in range(len(cats)):
            if attributes.get(cats[i]) and attributes.get(cats[i]).lower().find(s) > -1:
                localLoc = attributes.get('Location')
                localFolder = localLoc[localLoc.find('iTunes%20Music/')+15:]
                networkLoc = "http://jarman.homedns.org:82/" + localFolder
                songs[i].append([networkLoc, attributes])
    return songs, cats

#------------------------------------------------------------------------------------------------

class songs:    
    def GET(self, name):
        web.header('Content-Type', 'text/xml')
        if web.input(Playlist='null').Playlist != 'null':
            songs, plName = getPlaylistContents(web.input().Playlist)
            if name == '.xml':
                return render.songsxml(songs, plName)
            else:
                return render.songs(songs, plName);
        if web.input(Artists='null').Artists != 'null':
            artist = web.input().Artists
            songs = getArtistSongs(artist)
            return render.songs(songs, artist);
        if web.input(Albums='null').Albums != 'null':
            album = web.input().Albums
            songs = getAlbumSongs(album)
            return render.songs(songs, album);
        if len(web.input(search='null').search) > 1:
            songs, titles = findSongs(web.input().search)
            return render.search(web.input().search, songs, titles);
        else:
            return('invalid');

class artists:    
    def GET(self, name):
        return render.albums('Artists', lib.artistNames);

class albums:    
    def GET(self, name):
        return render.albums('Albums', lib.albumNames);

class playlists:
    def GET(self, name):
		if (name == '.xml'):
			return render.playlistsXML(lib.folders, lib.sortedPlaylists, render);
		else:
			return render.playlists(lib.folders, lib.sortedPlaylists, render);

class load:
    def GET(self):
        loadLibrary()
        return('finished!');

def loadLibrary():
    global lib, libLastModified, app, urls, globals
    newTime = os.path.getmtime(libraryLocation)
    if (newTime != libLastModified):
        print("reloading Library");
        libLastModified = newTime
        lib = XMLLibraryParser(libraryLocation)
        app = web.application(urls, globals());
        print("loaded library")

def pingServer():
    fullUrl = serverUrl + "register?name=" + clientName

    # append the client address and username, if they are not the empty string
    if (clientAddress != "" and clientAddress != None):
        fullUrl += "&url=" + clientAddress
    if (allowedUser != "" and allowedUser != None):
        fullUrl += "&user=" + allowedUser
    try:
        urllib2.urlopen(fullUrl);
    except urllib2.URLError, e:
        print "The server was unavailable";

def update():
    loadLibrary()
    pingServer()
    Timer(900, update, ()).start()

# function to run the server
if __name__ == "__main__":
    pingServer();
    #check to see if the library needs to be reloaded in 15 mins
    Timer(900, update, ()).start()
    app.run()
