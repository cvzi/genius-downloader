#!/usr/bin/env python
#Python 2.7
# -*- coding: utf-8 -*-

import sys
import urllib
import urllib2
import re
import threading
from mutagen import *
from mutagen.id3 import USLT

local = {
    'baseurl' : "http://rap.genius.com", # without trailing slash
    'basesearchurl' : "http://genius.com", # same here
    'usage' : """Downloads lyrics from rap.genius.com and saves the in a mp3 or m4a file
You can select the correct lyrics from the first 20 search results.
https://github.com/cvzi/Python/tree/master/Id3Rapgenius

Usage: python id3rapgenius.py filename artist songname

This was inteded as a Mp3Tag extension.
To add it to the Mp3Tag context menu, do the following steps in Mp3Tag:
  * Open Tools -> Options -> Tools 
  * Click on the "New" icon
  * Enter the name that shall appear in the context menu
  * For path choose your python.exe
  * For parameter use: C:\pathtofile\id3rapgenius.py "%_path%" "%artist%" "%title%"
  * Accept the "for all selected files" option"""
    }

# Show progess with dots . . .
class doingSth(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.i = 0
        self.exitFlag = 0
    def run(self):
      while 0 == self.exitFlag:
        threading._sleep(0.3)
        print "\r",(".  " if self.i==0 else (".. " if self.i==1 else ("..." if self.i==2 else "   "))),
        self.i = (self.i+1)%4
      print "\r",
    def exit(self):
      self.exitFlag = 1
      threading._sleep(0.4)

# Download from url with progress dots
def getUrl(url):
    thread1 = doingSth()
    thread1.start()
    try:
        req = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = urllib2.urlopen(req).read()      
    finally:
        thread1.exit()
    
    #data = unicode(data,'UTF8')
    #data = data.encode("utf-8")
    return data

# Set Lyrics of mp3 or m4a file
def setLyrics(filepath,lyrics):
  # find correct encoding
  for enc in ('utf8','iso-8859-1','iso-8859-15','cp1252','cp1251','latin1'):
    try:
      lyrics = lyrics.decode(enc)
      break
    except:
      pass

  # try to write to file
  audiofile = File(filepath)

  if type(audiofile) == mutagen.mp4.MP4:
    audiofile["\xa9lyr"] = lyrics
  elif type(audiofile) == mutagen.mp3.MP3:
    audiofile[u"USLT:desc:'eng'"] = USLT(encoding=3, lang=u'eng', desc=u'desc', text=lyrics)
  else:
    print "###unkown file type: ",type(audiofile)
    return False
  audiofile.save()
  return True

if __name__ == "__main__":
  
  if len(sys.argv) != 4:
    print "Error: Wrong argument number"
    print "\n"+local['usage']
    quit(1)

  filename = sys.argv[1]
  artist = sys.argv[2]
  song = sys.argv[3]

  print filename,artist,song

  foundsong = False
  
  url = local['baseurl']+'/'+artist.replace(" ","-")+'-'+song.replace(" ","-")+"-lyrics"
  print "Trying exact name: "+artist.replace(" ","-")+'-'+song.replace(" ","-")
  try:
    html = getUrl(url)
  except urllib2.HTTPError:
    html = "<h1>Looks like you came up short!<br>(Page not found)</h1>"
    
  if not "<h1>Looks like you came up short!<br>(Page not found)</h1>" in html:
    # Page exists:
    foundsong = True
    print "Found Lyrics!"
  else:
    # Remove a leading "The", featuring artists or brackets in general
    if artist[0:4] == "The " or artist[0:4] == "The " or "(" in artist or "feat" in artist or "Feat" in artist or "ft."  in artist or "Ft." in artist:
      if artist[0:4] == "The " or artist[0:4] == "The ":
        tartist = artist[4:]
      else:
        tartist = artist
      tartist = tartist.split("(")[0].split("feat")[0].split("Feat")[0].split("ft.")[0].split("Ft.")[0]
      print filename,tartist,song
      url = local['baseurl']+'/'+tartist.replace(" ","-")+'-'+song.replace(" ","-")+"-lyrics"
      print "Trying exact name: "+tartist.replace(" ","-")+'-'+song.replace(" ","-")
      try:
          html = getUrl(url)
      except urllib2.HTTPError:
          html = "<h1>Looks like you came up short!<br>(Page not found)</h1>"
      if not "<h1>Looks like you came up short!<br>(Page not found)</h1>" in html:
        # Page exists:
        foundsong = True
        print "Found Lyrics!"
  
    if not foundsong:
      # Try to search the song:
      print "No result for:"
      searchartist = artist.split("(")[0].split("feat")[0].split("Feat")[0].split("ft.")[0].split("Ft.")[0].replace("The ","").replace("the ","")
      searchsong = song.split("(")[0].split("feat")[0].split("Feat")[0].split("ft.")[0].split("Ft.")[0]
      print artist + " - " + song
      print ""
      print "Searching on website with:"
      print "Artist: "+searchartist
      print "Song:   "+searchsong
      searchurl = local['basesearchurl']+"/search?hide_unexplained_songs=false&q="+urllib.quote_plus(searchartist)+"%20"+urllib.quote_plus(searchsong)
      

      try:
          html = getUrl(searchurl)

      except urllib2.HTTPError as e:
          print "Could not open: "+searchurl
          print e
          exit()
    
      resultlist = html.split('<ul class="search_results song_list primary_list">')[1].split('</ul>')[0].strip()

      if "" == resultlist:
        print "0 songs found!"
      else:
        print "## -------------------------"
        results = []
        i = 1
        while "" != resultlist:
          txt,resultlist = resultlist.split("</li>",1)
          resultlist = resultlist.strip()
          
          resulturl = txt.split('<a href="')[1].split('"')[0].strip()
          
          resultsongname = txt.split("<span class='song_title'>")[1].split("</span>")[0]
          resultsongname = re.sub('<[^<]+?>', '', resultsongname ).strip()
          resultsongname = resultsongname .replace('\xe2\x80\x93','-')
          
          resultartist = txt.split("<span class='artist_name'>")[1].split("</span>")[0]
          resultartist = re.sub('<[^<]+?>', '', resultartist).strip()
          resultartist = resultartist.replace('\xe2\x80\x93','-').replace('&nbsp;',' ')

          resultname = resultartist + " - " + resultsongname 
          
          results.append([resultname,resulturl])
          print "%2d: %s" % (i,resultname)
          i += 1
        print "---------------------------"
        while True:
          print "Please choose song          (0 to exit)"
          print "close to: "+artist + " - " + song
          inp = input()
          try:
            val = int(inp)
            if 0 == val:
              exit()
            assert val > 0
            assert val < i
            break
          except ValueError:
            print "Sorry, wrong Number!"
          except AssertionError:
            print "Wtf?!"
        
        print ""
        print "Downloading lyrics #%d: %s" % (val,results[val-1][0])
        print ""
        #url = local['baseurl']+results[val-1][1]
        url = results[val-1][1] # in newer versions, the url seems to be complete already

        try:
            html = getUrl(url)
        except urllib2.HTTPError as e:
            print "Could not open: "+url
            print e
            exit()
        
        if not "<h1>Looks like you came up short!<br>(Page not found)</h1>" in html:
          # Page exists:
          foundsong = True
        else:
          print "URL wrong?! "+url



  if foundsong:
    lyrics = html.split('<div class="lyrics"')[1].split(">",1)[1].split("</div>")[0]
    
    lyrics = re.sub('<[^<]+?>', '', lyrics).strip()
    print "---------------------------"
    print lyrics
    print "---------------------------"
    if setLyrics(filename,lyrics):
      print "Saved lyrics to file "+filename
      threading._sleep(2)
    else:
      print "Could not save lyrics to file "+filename
      threading._sleep(10)
  else:
    print "No song results for "+song+" by "+artist
    threading._sleep(10)
