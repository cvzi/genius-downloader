#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Python 2.7
# https://github.com/cvzi/genius-downloader
# Download lyrics from rap.genius.com and saves the lyrics in a mp3 or m4a file

import sys
import urllib
import urllib2
import re
import threading
import htmlentitydefs
import json
from mutagen import *
from mutagen.id3 import USLT
import mutagen.mp4

local = {
    'baseurl' : "http://rap.genius.com", # without trailing slash
    'basesearchurl' : "http://genius.com", # same here
    'baseapiurl' : "https://genius.com/api", # same here
    'usage' : """Downloads lyrics from rap.genius.com and saves the lyrics in a mp3 or m4a file
You can select the correct lyrics from the first 20 search results.
Usage: python id3rapgenius.py filename artist songname
This was inteded as a Mp3Tag extension.
To add it to the Mp3Tag context menu, do the following steps in Mp3Tag:
  * Open Tools -> Options -> Tools
  * Click on the "New" icon
  * Enter the name that shall appear in the context menu
  * For path choose your python.exe
  * For parameter use: C:\pathtofile\id3rapgenius.py "%_path%" "$replace(%artist%,","")" "$replace(%title%,","")"
  * Accept the "for all selected files" option"""
    }


# http://effbot.org/zone/re-sub.htm#unescape-html

##
# Removes HTML or XML character references and entities from a text string.
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.

def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    try:
        return re.sub("&#?\w+;", fixup, text)
    except:
        return text



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
def getUrl(url, getEncoding=False):
    try:
        thread1 = doingSth()
        thread1.start()
        fs = None
        try:
            req = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            fs = urllib2.urlopen(req)
            data = fs.read()
        except KeyboardInterrupt as ki:
            thread1.exit()
            raise ki # allow CTRL-C to interrupt
        finally:
            if fs is not None:
                fs.close()
            thread1.exit()

        #data = unicode(data,'UTF8')
        #data = data.encode("utf-8")
        
        if getEncoding:
            try:
                enc = fs.headers.get("Content-Type").split("charset=")[1]
            except:
                enc = "utf-8"
            return data, enc
        
        return data
    except Exception as e:
        thread1.exit()
        raise e

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
  artist = sys.argv[2].decode(encoding="windows-1252").encode('utf-8').strip()
  song = sys.argv[3].decode(encoding="windows-1252").encode('utf-8').strip()

  print filename,artist,song

  foundsong = False

  url = local['baseurl']+'/'+artist.replace(" ","-")+'-'+song.replace(" ","-")+"-lyrics"
  print "Trying exact name: "+artist.replace(" ","-")+'-'+song.replace(" ","-")
  try:
    html = getUrl(url)
  except urllib2.HTTPError:
    html = "<h1>Looks like you came up short!<br>(Page not found)</h1>"
  except KeyboardInterrupt:
    sys.exit() # Exit program on Ctrl-C

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
      tartist = tartist.split("(")[0].split("feat")[0].split("Feat")[0].split("ft.")[0].split("Ft.")[0].strip()
      print filename,tartist,song
      url = local['baseurl']+'/'+tartist.replace(" ","-")+'-'+song.replace(" ","-")+"-lyrics"
      print "Trying exact name: "+tartist.replace(" ","-")+'-'+song.replace(" ","-")
      try:
          html = getUrl(url)
      except urllib2.HTTPError:
          html = "<h1>Looks like you came up short!<br>(Page not found)</h1>"
      except KeyboardInterrupt:
          sys.exit() # Exit program on Ctrl-C
    
      if not "<h1>Looks like you came up short!<br>(Page not found)</h1>" in html:
        # Page exists:
        foundsong = True
        print "Found Lyrics!"

    if not foundsong:
      # Try to search the song:
      print "No result for:"
      searchartist = artist.split("(")[0].split("feat")[0].split("Feat")[0].split("ft.")[0].split("Ft.")[0].replace("The ","").replace("the ","").strip()
      searchsong = song.split("(")[0].split("feat")[0].split("Feat")[0].split("ft.")[0].split("Ft.")[0].strip()
      print artist + " - " + song
      print ""
      print "Searching on website with:"
      print "Artist: "+searchartist
      print "Song:   "+searchsong
      searchurl = local['basesearchurl']+"/search?hide_unexplained_songs=false&q="+urllib.quote_plus(searchartist)+"%20"+urllib.quote_plus(searchsong)
          
      try:
        text, encoding = getUrl(local["baseapiurl"] + "/search/song?q=" + urllib.quote_plus(searchartist)+"%20"+urllib.quote_plus(searchsong), getEncoding=True)
      except urllib2.HTTPError as e:
        print "Could not open: "+searchurl
        print e
        exit()
      except KeyboardInterrupt:
        sys.exit() # Exit program on Ctrl-C
          
      obj = json.loads(text, encoding=encoding)
      results_length = 0

      assert obj["response"]["sections"][0]["type"] == "song", "Wrong type in json result"
      results_length = len(obj["response"]["sections"][0]["hits"])
      
      if 0 == results_length:
        print "0 songs found!"
      else:
        print "## -------------------------"
        results = []
        i = 1
        for hit in obj["response"]["sections"][0]["hits"]:
          resulturl = hit["result"]["url"].encode(encoding="utf-8")

          resultsongname = hit["result"]["title_with_featured"]
          resultartist = hit["result"]["primary_artist"]["name"]

          resultname = resultartist + " - " + resultsongname
          resultname = resultname.replace(u"\u200b", u"").replace(u"\xa0", u" ").strip().encode('ascii', 'ignore')

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
        except KeyboardInterrupt:
            sys.exit() # Exit program on Ctrl-C
          
        if not "<h1>Looks like you came up short!<br>(Page not found)</h1>" in html:
          # Page exists:
          foundsong = True
        else:
          print "URL wrong?! "+url



  if foundsong:
    
    lyrics = html.split('<div class="lyrics">')[1].split("</div>")[0]

    # Remove <script>...</script>
    while "<script" in lyrics:
        before = lyrics.split("<script")[0]
        after = lyrics.split("</script>",1)[1]
        lyrics = before + after

    # Replace accents, prime and apostrophe with 'closing single quotation mark'
    primes = ["´","`","’","′","ʻ","‘"]
    for symbol in primes:
        lyrics = lyrics.replace(symbol, "'")
    
    # Remove all html tags and add windows line breaks
    lyrics = re.sub('<[^<]+?>', '', lyrics).strip().replace("\r\n", "\n").replace("\n","\r\n")
    
    # Replace &XXX; html encoding line by line and remove encoding with str()
    lines = lyrics.split("\n")
    lyrics = []
    for line in lines:
        esc = unescape(line)
        lyrics.append(str(esc))
    
    lyrics = "\n".join(lyrics)
    
    
    print "---------------------------"
    
    try:
        print lyrics
    except UnicodeEncodeError:
        try:
            print lyrics.encode(sys.stdout.encoding, errors='replace')
        except:
            print "##Sorry, encoding problems with terminal##"
            pass
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
