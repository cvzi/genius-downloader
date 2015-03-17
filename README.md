genius downloader
=================

Downloads lyrics from rapgenius.com and saves the lyrics in a mp3 or m4a file.
You can select the correct lyrics from the first 20 search results. 
Written in Python using the mutagen module.

Required:
 * Python 2.7
 * [Mutagen](https://bitbucket.org/lazka/mutagen) python module


**Usage**: python id3rapgenius.py filename artist songname

This was originally inteded as a [Mp3Tag](http://www.mp3tag.de) extension.
To add it to the Mp3Tag context menu, do the following steps in Mp3Tag:
 * Open Tools -> Options -> Tools 
 * Click on the "New" icon
 * Enter the name that shall appear in the context menu
 * For path choose your python.exe
 * For parameter use: C:\pathtofile\id3rapgenius.py "%_path%" "%artist%" "%title%"
 * Accept the "for all selected files" option
 
![Mp3Tag instructions](https://raw.githubusercontent.com/cvzi/Python/master/Id3Rapgenius/id3rapgenius.jpg)