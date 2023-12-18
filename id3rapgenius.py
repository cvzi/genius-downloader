#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Python 3.11
# https://github.com/cvzi/genius-downloader
# Download lyrics from genius.com and saves the lyrics in a mp3 or m4a file

import sys
import requests
import urllib.parse
import re
import time
import threading
import platform
import ctypes
import html.entities
import json
from mutagen import *
from mutagen.id3 import USLT
import mutagen.mp4

local = {
    'baseurl': "http://genius.com",  # without trailing slash
    'basesearchurl': "http://genius.com",  # same here
    'baseapiurl': "https://genius.com/api",  # same here
    'usage': """Downloads lyrics from genius.com and saves the lyrics in a mp3 or m4a file
You can select the correct lyrics from the first 20 search results.
Usage: python id3rapgenius.py filename artist songname
This was inteded as a Mp3Tag extension.
To add it to the Mp3Tag context menu, do the following steps in Mp3Tag:
  * Open Tools -> Options -> Tools
  * Click on the "New" icon
  * Enter the name that shall appear in the context menu
  * For path choose your python.exe
  * For parameter use: C:\\pathtofile\\id3rapgenius.py "%_path%" "$replace(%artist%,","")" "$replace(%title%,","")"
  * Accept the "for all selected files" option""",
    'colorInTerminal' : True
}


def unescape(text):
    """http://effbot.org/zone/re-sub.htm#unescape-html
Removes HTML or XML character references and entities from a text string.

@param text The HTML (or XML) source text.
@return The plain text, as a Unicode string, if necessary.
"""
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return chr(int(text[3:-1], 16))
                else:
                    return chr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = chr(html.entities.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text  # leave as is
    try:
        return re.sub(r"&#?\w+;", fixup, text)
    except BaseException:
        return text


# Show progess with dots . . .
class doingSth(threading.Thread):
    def __init__(self):
        super().__init__()
        self.i = 0
        self.exitFlag = 0

    def run(self):
        if not 'idlelib.run' in sys.modules:
            while 0 == self.exitFlag:
                time.sleep(0.3)
                print("\r", (".  " if self.i == 0 else (".. " if self.i == 1 else ("..." if self.i == 2 else "   "))), end=' ')
                self.i = (self.i + 1) % 4
            print("\r", end='')
        else:
            print('Downloading...')

    def exit(self):
        self.exitFlag = 1
        time.sleep(0.4)

def highlightMatch(a, b, flags=re.IGNORECASE):
    if not local['colorInTerminal']:
        return b
    BGGREEN = '\033[42m'
    ENDC = '\033[0m'
    splits = [fr"\b{re.escape(x)}\b" for x in re.split(r'(\W)', a)]
    def repl(m):
        if len(m[0]) < 2:
            return m[0]
        return f"{BGGREEN}{m[0]}{ENDC}"
    s = re.sub("|".join(splits), repl, b, flags=flags)
    s = re.sub(fr"{re.escape(ENDC)}(\W+){re.escape(BGGREEN)}", lambda m: m[1], s)
    return s

def getUrl(url, json=False):
    """Download from url with progress dots"""
    data = None
    url = url
    try:
        thread1 = doingSth()
        thread1.start()
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            if response.status_code != 200:
                raise requests.HTTPError(response.status_code)
            if json:
                data = response.json()
            else:
                data = response.text
        except KeyboardInterrupt as ki:
            thread1.exit()
            raise ki  # allow CTRL-C to interrupt
        finally:
            thread1.exit()

        return data
    except Exception as e:
        thread1.exit()
        raise e




def setLyrics(filepath, lyrics):
    """Set Lyrics of mp3 or m4a file"""

    # find correct encoding
    for enc in ('utf8', 'iso-8859-1', 'iso-8859-15',
                'cp1252', 'cp1251', 'latin1'):
        try:
            lyrics = lyrics.decode(enc)
            break
        except BaseException:
            pass

    # try to write to file
    audiofile = File(filepath)

    if isinstance(audiofile, mutagen.mp4.MP4):
        audiofile["\xa9lyr"] = lyrics
    elif isinstance(audiofile, mutagen.mp3.MP3):
        audiofile["USLT:desc:'eng'"] = USLT(
            encoding=3, lang='eng', desc='desc', text=lyrics)
    else:
        print("###unkown file type: ", type(audiofile))
        return False
    try:
        audiofile.save()
    except mutagen.MutagenError as e:
        print("Could not save file:")
        print(e)
        return False
    return True


def main(filename, artist, song):
    #print("%r\n%r\n%r" % (sys.argv[1], sys.argv[2], sys.argv[3]))

    foundsong = False

    exactName = artist.replace(" ", "-") + '-' + song.replace(" ", "-") + "-lyrics"
    url = local['baseurl'] + '/' + exactName


    print("Trying exact name: " + exactName)
    try:
        html = getUrl(url)
    except requests.HTTPError:
        html = "<h1>Looks like you came up short!<br>(Page not found)</h1>"

    if not "<h1>Looks like you came up short!<br>(Page not found)</h1>" in html:
        # Page exists:
        foundsong = True
        print("Found Lyrics!")
    else:
        # Remove a leading "The", featuring artists or brackets in general
        if artist[0:4] == "The " or artist[0:
                                           4] == "The " or "(" in artist or "feat" in artist or "Feat" in artist or "ft." in artist or "Ft." in artist:
            if artist[0:4] == "The " or artist[0:4] == "The ":
                tartist = artist[4:]
            else:
                tartist = artist
            tartist = tartist.split("(")[0].split("feat")[0].split(
                "Feat")[0].split("ft.")[0].split("Ft.")[0].strip()
            print(filename, tartist, song)
            url = local['baseurl'] + '/' + tartist.replace(" ", "-").replace(
                "&", "and") + '-' + song.replace(" ", "-").replace("&", "and") + "-lyrics"
            print("Trying exact name: " + tartist.replace(" ", "-").replace("&", "and") + '-' + song.replace(" ", "-").replace("&", "and"))
            try:
                html = getUrl(url)
            except requests.HTTPError:
                html = "<h1>Looks like you came up short!<br>(Page not found)</h1>"

            if not "<h1>Looks like you came up short!<br>(Page not found)</h1>" in html:
                # Page exists:
                foundsong = True
                print("Found Lyrics!")

        if not foundsong:
            # Try to search the song:
            print("No result for:")
            searchartist = artist.split("(")[0].split("feat")[0].split("Feat")[0].split(
                "ft.")[0].split("Ft.")[0].replace("The ", "").replace("the ", "").strip()
            searchsong = song.split("(")[0].split("feat")[0].split(
                "Feat")[0].split("ft.")[0].split("Ft.")[0].strip()
            print(artist + " - " + song)
            print("")
            print("Searching on website with:")
            print("Artist: " + searchartist)
            print("Song:   " + searchsong)
            searchurl = local['basesearchurl'] + "/search?hide_unexplained_songs=false&q=" + \
                urllib.parse.quote_plus(searchartist) + "%20" + urllib.parse.quote_plus(searchsong)

            obj = None
            try:
                obj = getUrl(local["baseapiurl"] +
                                        "/search/song?q=" +
                                        urllib.parse.quote_plus(searchartist) +
                                        "%20" +
                                        urllib.parse.quote_plus(searchsong), json=True)
            except requests.HTTPError as e:
                print("Could not open: " + searchurl)
                print(e)
                return 70

            results_length = 0

            assert obj["response"]["sections"][0]["type"] == "song", "Wrong type in json result"
            results_length = len(obj["response"]["sections"][0]["hits"])

            if 0 == results_length:
                print("0 songs found!")
            else:
                # List search results
                print("## -------------------------------------")
                results = []
                i = 1
                for hit in obj["response"]["sections"][0]["hits"]:
                    resulturl = hit["result"]["url"].encode(encoding="utf-8")

                    resultsongname = hit["result"]["title_with_featured"]
                    resultartist = hit["result"]["primary_artist"]["name"]

                    resultname = resultartist + " - " + resultsongname
                    resultname = resultname.replace("\u200b", "").replace("\xa0", " ").strip()

                    results.append([resultname, resulturl])
                    print("%2d: %s" % (i, highlightMatch(artist + " - " + song, resultname)))
                    i += 1
                print(" ---------------------------------------")
                while True:
                    print("Please choose song          (0 to exit)")
                    print("close to: " + artist + " - " + song)
                    inp = eval(input())
                    try:
                        val = int(inp)
                        if 0 == val:
                            sys.exit(0)
                        assert val > 0
                        assert val < i
                        break
                    except ValueError:
                        print("Sorry, wrong Number!")
                    except AssertionError:
                        print("Wtf?!")

                print("")
                print("Downloading lyrics #%d: %s" % (val, results[val - 1][0]))
                print("")
                url = results[val - 1][1]

                try:
                    html = getUrl(url)
                except requests.HTTPError as e:
                    print("Could not open: " + url)
                    print(e)
                    return 69

                if not "<h1>Looks like you came up short!<br>(Page not found)</h1>" in html:
                    # Page exists:
                    foundsong = True
                else:
                    print("URL wrong?! " + url)

    if foundsong:
        if "for this song have yet to be released" in html:
            print("Lyrics for this song have yet to be released. Please check back once the song has been released.")
            time.sleep(10)
            return 68

        if '<div class="lyrics">' in html:
            # Legacy page design (before March 2020)
            lyrics = html.split('<div class="lyrics">')[1].split("</div>")[0]
        else:
            # New design
            if '__PRELOADED_STATE__ = JSON.parse(' in html:
                # Example: https://genius.com/Friedberg-go-wild-lyrics?react=1
                json_str = html.split("__PRELOADED_STATE__ = JSON.parse('")[1].split("');\n")[0]
                json_str = re.sub(r'\\([^\\])', r'\1', json_str)
                json_str = re.sub(r'\\\\', r'\\', json_str)

                jdata = json.loads(json_str)

                def parseJdata(obj, arr):
                    if arr is None:
                        arr = []
                    if not 'children' in obj:
                        return arr
                    for child in obj['children']:
                        if type(child) is str:
                            arr.append(child)
                        else:
                            parseJdata(child, arr)
                            if child['tag'] == 'br':
                                arr.append('\n')
                    return arr

                lyrics_arr = parseJdata(jdata['songPage']['lyricsData']['body'], [])
                lyrics = "".join(lyrics_arr)
            else:
                print(f"Unkown page design for {url}")
                return 67


        # Remove <script>...</script>
        while "<script" in lyrics:
            before = lyrics.split("<script")[0]
            after = lyrics.split("</script>", 1)[1]
            lyrics = before + after

        # Replace accents, prime and apostrophe with 'closing single quotation
        # mark'
        primes = ["´", "`", "’", "′", "ʻ", "‘"]
        for symbol in primes:
            lyrics = lyrics.replace(symbol, "'")

        # Remove all html tags and add windows line breaks
        lyrics = re.sub(
            '<[^<]+?>',
            '',
            lyrics).strip().replace(
            "\r\n",
            "\n").replace(
            "\n",
            "\r\n")

        # Replace &XXX; html encoding line by line and remove encoding with
        # str()
        lines = lyrics.split("\n")
        lyrics = []
        for line in lines:
            esc = unescape(line)
            lyrics.append(str(esc))

        lyrics = "\n".join(lyrics)

        print("---------------------------")

        try:
            print(lyrics)
        except UnicodeEncodeError:
            try:
                print(lyrics.encode(sys.stdout.encoding, errors='ignore'))
            except BaseException:
                print("##Sorry, encoding problems with terminal##")
                pass
        print("---------------------------")
        if setLyrics(filename, lyrics):
            try:
                print("Saved lyrics to file " + filename)
            except BaseException:
                print("Saved lyrics to file.")
            time.sleep(3)
            return 0
        else:
            print("Could not save lyrics to file " + filename)
            time.sleep(60)
            return 66
    else:
        print("No song results for " + song + " by " + artist)
        time.sleep(10)
        return 0

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Error: Wrong argument number")
        print("\n" + local['usage'])
        sys.exit(64)


    if local['colorInTerminal'] and platform.system() == 'Windows':
        # Enable VT100 sequences (colored font/background in terminal)
        # https://docs.microsoft.com/en-us/windows/console/console-virtual-terminal-sequences#example-of-sgr-terminal-sequences
        kernel32 = ctypes.WinDLL('kernel32')
        stdOut = kernel32.GetStdHandle(-11)
        consoleMode = ctypes.c_ulong()
        kernel32.GetConsoleMode(stdOut, ctypes.byref(consoleMode))
        consoleMode.value |= 4
        kernel32.SetConsoleMode(stdOut, consoleMode)

    filename = sys.argv[1]
    artist = sys.argv[2].strip()
    song = sys.argv[3].strip()
    try:
        sys.exit(main(filename, artist, song))
    except KeyboardInterrupt:
        sys.exit(130)  # Exit program on Ctrl-C
    except Exception as e:
        print(e)
        time.sleep(10)
        sys.exit(71)
