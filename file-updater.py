import http.server
import socketserver
import os
from requests import get
import requests
import hashlib
import threading
import PySimpleGUI as gui
import time

print('This is File Updater GUI v1.2')

gui.theme('Dark Grey 11')

windowlayout = [
    [gui.I(key='DirHost', enable_events=True, visible=False), gui.I(key='DirDownload', enable_events=True, visible=False)],
    [gui.B(key='HostB', button_text='Host', size=8), gui.FolderBrowse(target='DirHost', button_text='Folder to Host', size=15), gui.StatusBar(key='DirHostStatus', text='', size=17)],
    [gui.B(key='DownloadB', button_text='Download', size=8), gui.FolderBrowse(target='DirDownload', button_text='Download Folder', size=15), gui.StatusBar(key='DirDownloadStatus', text='', size=17)],
    [gui.T(text='IP', size=(4)), gui.I(key='IP', default_text='localhost', size=(15), tooltip='Host\'s IP')],
    [gui.T(text='PORT', size=(4)), gui.I(key='PORT', default_text='6969', size=(5), tooltip='Host\'s PORT')],
    [gui.Multiline(key='Console', disabled=True, autoscroll=True, size=(49,5))],
    [gui.ProgressBar(key='ChecksumProgress', max_value=100, size=(33,20))],
    [gui.ProgressBar(key='DownloadProgress', max_value=100, size=(33,20))]
]

window = gui.Window('File-Updater GUI v1.2', layout=windowlayout, icon=r'favicon.ico')

def checksumfiles(directory):
    dm5filelist = []
    filedirlist = []
    dirsubdirlist = [x[0] for x in os.walk(directory)]
    cutdirsubdirlist = []
    for uncutdir in dirsubdirlist:
        currentbyte = 0
        dirbytefound = 0
        for dirbyte in uncutdir:
            if dirbyte == '\\':
                dirbytefound = currentbyte
            currentbyte += 1
        if dirbytefound == 0:
            cutdirsubdirlist.append((uncutdir + ' ')[dirbytefound:-1])
        else:
            cutdirsubdirlist.append((uncutdir + ' ')[dirbytefound+1:-1])
    for subdir in dirsubdirlist:
        for file in os.listdir(subdir):
            if file not in cutdirsubdirlist:
                filedirlist.append(subdir+'\\'+file)
    for file in filedirlist:
        with open(file=file, encoding='iso-8859-1') as filecheck:
            window['Console'].print('Calculating Checksum... ' + str(len(dm5filelist) + 1) + '/' + str(len(filedirlist)))
            window['ChecksumProgress'].update((100/len(filedirlist))*(len(dm5filelist)+1))
            rddata = filecheck.read()
            md5output = hashlib.md5(str(rddata).encode('iso-8859-1')).hexdigest()
            dm5filelist.append((file+' ')[len(directory)+1:-1]+'|'+md5output)
    return dm5filelist

def removeemptyfolders(directory):
    delfolder = 'false'
    for folder in list(os.walk(directory))[1:]:
        if not folder[2]:
            try:
                os.rmdir(folder[0])
                window['Console'].print('Removing ' + folder[0]+'...')
                delfolder = 'true'
            except:
                continue
    if delfolder == 'true':
        removeemptyfolders(directory=directory)

def hostfiles(PORT, directory):
    if PORT != '':
        try:
            PORT = int(PORT)
        except:
            PORT = 6969
    else:
        PORT = 6969

    if not os.path.exists(directory) or directory == '':
        window['Console'].print('Error: Directory doesn\'t exist')
        window['HostB'].update(disabled=False)
        window['DownloadB'].update(disabled=False)
        window['DownloadProgress'].update(visible=True)
        window['IP'].update(disabled=False)
        window['PORT'].update(disabled=False)
        exit()

    else:
        window['Console'].print('')
        window['Console'].print('Creating Changelog...')
        hostchangelog = open(file=directory + '/' + 'FileChangeLog.txt', mode='w+', encoding='utf-8')
        for file in checksumfiles(directory=directory):
            hostchangelog.write(file + '\n')
        hostchangelog.close()
        window['Console'].print('Changelog Successfully Created!')

        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=directory, **kwargs)

        publicip = get('https://api.ipify.org').text
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            window['Console'].print()
            window['Console'].print('Server running at ' + publicip + ':' + str(PORT))
            httpd.serve_forever()

def downloadfiles(IP, PORT, directory):
    if IP == '':
        IP = 'localhost'
    if PORT != '':
        try:
            PORT = int(PORT)
        except:
            PORT = 6969
    else:
        PORT = 6969
    URL = 'http://' + IP + ':' + str(PORT) + '/'

    if not os.path.exists(directory) or directory == '':
        window['Console'].print('Error: Directory doesn\'t exist')
        window['IP'].update(disabled=False)
        window['PORT'].update(disabled=False)
        window['HostB'].update(disabled=False)
        window['DownloadB'].update(disabled=False)
        exit()

    window['Console'].print()
    window['Console'].print('Trying to connect to host...')
    ConnectionCheck = ''
    try:
        ConnectionCheck = str(requests.get(url=URL))
        if ConnectionCheck == '<Response [200]>':
            window['Console'].print('Connection Established!')
            window['Console'].print()
        elif ConnectionCheck != '':
            window['Console'].print('Unknown Error code: ' + ConnectionCheck)
            window['IP'].update(disabled=False)
            window['PORT'].update(disabled=False)
            window['HostB'].update(disabled=False)
            window['DownloadB'].update(disabled=False)
            exit()
    except:
        window['Console'].print('Error: Unable to establish connection')
        window['IP'].update(disabled=False)
        window['PORT'].update(disabled=False)
        window['HostB'].update(disabled=False)
        window['DownloadB'].update(disabled=False)
        exit()


    if ConnectionCheck == '<Response [200]>':
        downloadchangelog = checksumfiles(directory=directory)
        dhostchangelog = (requests.get(url=URL + 'FileChangeLog.txt')).text
        listdhostchangelog = []
        dhclastbyte = -1
        dhccurrentbyte = 0
        for x in dhostchangelog:
            if dhostchangelog[dhccurrentbyte:dhccurrentbyte + 1] == '\n':
                listdhostchangelog.append(dhostchangelog[dhclastbyte + 1:dhccurrentbyte - 1])
                dhclastbyte -= dhclastbyte
                dhclastbyte += dhccurrentbyte
            dhccurrentbyte += 1

        unneededfiles = []
        window['Console'].print()
        window['Console'].print('Checking and Removing Old Files...')
        for singlefile in downloadchangelog:
            rmfileornot = 'true'
            anchorbyte = 0
            for x in singlefile:
                if x == '|':
                    cutsinglefile = singlefile[0:anchorbyte]
                anchorbyte += 1
            for singlecheckfile in listdhostchangelog:
                if singlefile == singlecheckfile:
                    unneededfiles.append(cutsinglefile)
                    rmfileornot = 'false'
            if rmfileornot == 'true':
                window['Console'].print('Removing ' + cutsinglefile + '...')
                os.remove(directory + '/' + cutsinglefile)
        window['Console'].print('Removal of Old Files Completed!')
        window['Console'].print()

        window['Console'].print('Removing Empty Folders...')
        removeemptyfolders(directory=directory)
        window['Console'].print('Removal of Empty Folders Completed!')
        window['Console'].print()

        neededfiles = []
        for neededsinglefile in listdhostchangelog:
            fileexist = 'false'
            anchorbyte = 0
            for x in neededsinglefile:
                if x == '|':
                    cutneededsinglefile = neededsinglefile[0:anchorbyte]
                anchorbyte += 1
            for unneededsinglefile in unneededfiles:
                if cutneededsinglefile == unneededsinglefile:
                    fileexist = 'true'
            if fileexist == 'false' and cutneededsinglefile != 'FileChangeLog.txt':
                neededfiles.append(cutneededsinglefile)

        window['Console'].print('Creating new folders...')
        for singleneededfile in neededfiles:
            anchorbyte = 0
            for byte in singleneededfile:
                if byte == '\\':
                    folderpath = singleneededfile[0:anchorbyte]
                    if not os.path.exists(directory + '\\' + folderpath):
                        window['Console'].print('Creating new folder ' + folderpath + '...')
                        os.mkdir(directory + '\\' + folderpath)
                anchorbyte += 1
        window['Console'].print('Creating new folders Completed!')
        window['Console'].print()

        window['Console'].print('Downloading New Files...')
        dwcurrentfile = 1
        for singleneededfile in neededfiles:
            window['Console'].print('Downloading file ' + singleneededfile + ' ' + str(dwcurrentfile) + '/' + str(len(neededfiles)))
            window['DownloadProgress'].update((100/len(neededfiles))*dwcurrentfile)
            urlsingleneededfile = singleneededfile.replace('\\', '/')
            downloadfile = requests.get(url=URL + urlsingleneededfile)
            open(directory + '\\' + singleneededfile, 'wb').write((downloadfile.content))
            dwcurrentfile += 1
        window['DownloadProgress'].update(100)
        window['Console'].print('All New Files Successfully Downloaded!')
        window['Console'].print()
        window['Console'].print('You are Up-To Date!')
        window['IP'].update(disabled=False)
        window['PORT'].update(disabled=False)
        window['HostB'].update(disabled=False)
        window['DownloadB'].update(disabled=False)

def cutdir(directory):
    DirByteFinder = 0
    DirByte = 0
    for x in directory:
        if x == '/':
            DirByte = DirByteFinder
        DirByteFinder += 1
    return(directory+' ')[DirByte + 1:-1]

def guiwindow():
    while True:
        event, values = window.read()
        if event == gui.WINDOW_CLOSED:
            exit()
        window['DirHostStatus'].update(cutdir(values['DirHost']))
        window['DirDownloadStatus'].update(cutdir(values['DirDownload']))
        if event == 'HostB':
            window['ChecksumProgress'].update(0)
            window['DownloadProgress'].update(0)
            window['HostB'].update(disabled=True)
            window['DownloadB'].update(disabled=True)
            window['DownloadProgress'].update(visible=False)
            window['IP'].update(disabled=True)
            window['PORT'].update(disabled=True)
            HostFilesThread = threading.Thread(daemon=True, target=hostfiles, args=[values['PORT'], values['DirHost']])
            HostFilesThread.start()
        if event == 'DownloadB':
            window['ChecksumProgress'].update(0)
            window['DownloadProgress'].update(0)
            window['HostB'].update(disabled=True)
            window['DownloadB'].update(disabled=True)
            window['IP'].update(disabled=True)
            window['PORT'].update(disabled=True)
            DownloadFilesThread = threading.Thread(daemon=True, target=downloadfiles, args=[values['IP'], values['PORT'], values['DirDownload']])
            DownloadFilesThread.start()
    window.close()

GuiWindowThread = threading.Thread(daemon=True, target=guiwindow)
GuiWindowThread.start()

while True:
    if GuiWindowThread.is_alive() == False:
        exit()
    else:
        time.sleep(3)