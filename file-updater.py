import http.server
import socketserver
import os
from requests import get
import requests
import hashlib
import PySimpleGUI as gui

print('This is File Updater GUI v1.1')

gui.theme('Dark Grey 11')

windowlayout = [
    [gui.I(key='DirHost', enable_events=True, visible=False), gui.I(key='DirDownload', enable_events=True, visible=False)],
    [gui.B(key='HostB', button_text='Host', size=8), gui.FolderBrowse(target='DirHost', button_text='Folder to Host', size=15), gui.StatusBar(key='DirHostStatus', text='', size=17)],
    [gui.B(key='DownloadB', button_text='Download', size=8), gui.FolderBrowse(target='DirDownload', button_text='Download Folder', size=15), gui.StatusBar(key='DirDownloadStatus', text='', size=17)],
    [gui.T(text='IP', size=(4)), gui.I(key='IP', default_text='localhost', size=(15), tooltip='Host\'s IP')],
    [gui.T(text='PORT', size=(4)), gui.I(key='PORT', default_text='6969', size=(5), tooltip='Host\'s PORT')],
    [gui.Multiline(key='ErrorLog', disabled=True, autoscroll=True, size=(40,2)), gui.B(key='StopB', button_text='Stop', size=(5,3))],
    [gui.ProgressBar(key='ChecksumProgress', max_value=100, size=(33,20))],
    [gui.ProgressBar(key='DownloadProgress', max_value=100, size=(33,20))],
]

window = gui.Window('File-Updater GUI v1.1', layout=windowlayout, icon=r'favicon.ico')
errorcount = 0

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
            print('Calculating Checksum... ' + str(len(dm5filelist) + 1) + '/' + str(len(filedirlist)))
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
                print('Removing ' + folder[0]+'...')
                delfolder = 'true'
            except:
                continue
    if delfolder == 'true':
        removeemptyfolders(directory=directory)

def hostfiles(PORT, directory, errorcount):
    error = 0
    if PORT != '':
        try:
            PORT = int(PORT)
        except:
            PORT = 6969
    else:
        PORT = 6969

    if not os.path.exists(directory) or directory == '':
        error += 1
        print(str(errorcount+1)+' Error: Directory doesn\'t exist')
        window['ErrorLog'].print(str(errorcount+1)+' Error: Directory doesn\'t exist')
        window['HostB'].update(disabled=False)
        window['DownloadB'].update(disabled=False)
        return error
    else:
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=directory, **kwargs)

        print('Creating Changelog...')
        hostchangelog = open(file=directory + '/' + 'FileChangeLog.txt', mode='w+', encoding='utf-8')
        for file in checksumfiles(directory=directory):
            hostchangelog.write(file + '\n')
        hostchangelog.close()
        print('Changelog Successfully Created!')

        publicip = get('https://api.ipify.org').text
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print()
            print('Server running at ' + publicip + ':' + str(PORT))
            window.close()
            httpd.serve_forever()
    return error

def downloadfiles(IP, PORT, directory, errorcount):
    error = 0
    print()
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
        error += 1
        print(str(errorcount+1)+' Error: Directory doesn\'t exist')
        window['ErrorLog'].print(str(errorcount+1)+' Error: Directory doesn\'t exist')
        return error

    print()
    print('Trying to connect to host...')
    ConnectionCheck = ''
    try:
        ConnectionCheck = str(requests.get(url=URL))
        if ConnectionCheck == '<Response [200]>':
            print('Connection Established!')
            print()
        elif ConnectionCheck != '':
            error += 1
            print(str(errorcount + 1) + ' Unknown Error code: ' + ConnectionCheck)
            window['ErrorLog'].print(str(errorcount + 1) + ' Unknown Error code: ' + ConnectionCheck)
            return error
    except:
        error += 1
        print(str(errorcount + 1) + 'Error: Unable to establish connection')
        window['ErrorLog'].print(str(errorcount + 1) + ' Error: Unable to establish connection')
        return error


    if ConnectionCheck == '<Response [200]>':
        print()
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
        print()
        print('Checking and Removing Old Files...')
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
                print('Removing ' + cutsinglefile + '...')
                os.remove(directory + '/' + cutsinglefile)
        print('Removal of Old Files Completed!')
        print()

        print('Removing Empty Folders...')
        removeemptyfolders(directory=directory)
        print('Removal of Empty Folders Completed!')
        print()

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

        print('Creating new folders...')
        for singleneededfile in neededfiles:
            anchorbyte = 0
            for byte in singleneededfile:
                if byte == '\\':
                    folderpath = singleneededfile[0:anchorbyte]
                    if not os.path.exists(directory + '\\' + folderpath):
                        print('Creating new folder ' + folderpath + '...')
                        os.mkdir(directory + '\\' + folderpath)
                anchorbyte += 1
        print('Creating new folders Completed!')
        print()

        print('Downloading New Files...')
        dwcurrentfile = 1
        for singleneededfile in neededfiles:
            print('Downloading file ' + singleneededfile + ' ' + str(dwcurrentfile) + '/' + str(len(neededfiles)))
            window['DownloadProgress'].update((100/len(neededfiles))*dwcurrentfile)
            urlsingleneededfile = singleneededfile.replace('\\', '/')
            downloadfile = requests.get(url=URL + urlsingleneededfile)
            open(directory + '\\' + singleneededfile, 'wb').write((downloadfile.content))
            dwcurrentfile += 1
        window['DownloadProgress'].update(100)
        print('All New Files Successfully Downloaded!')
        print()
        print('You are Up-To Date!')
        print()
        return error

while True:
    event, values = window.read()
    if event == gui.WINDOW_CLOSED:
        exit()
    DirHostStatusByteFinder = 0
    DirHostStatusByte = 0
    for x in values['DirHost']:
        if x == '/':
            DirHostStatusByte = DirHostStatusByteFinder
        DirHostStatusByteFinder += 1
    cutDirHost = (values['DirHost'] + ' ')[DirHostStatusByte + 1:-1]
    DirDownloadStatusByteFinder = 0
    DirDownloadStatusByte = 0
    for x in values['DirDownload']:
        if x == '/':
            DirDownloadStatusByte = DirDownloadStatusByteFinder
        DirDownloadStatusByteFinder += 1
    cutDirDownload = (values['DirDownload'] + ' ')[DirDownloadStatusByte + 1:-1]
    window['DirHostStatus'].update(cutDirHost)
    window['DirDownloadStatus'].update(cutDirDownload)
    if event == 'HostB':
        window['ChecksumProgress'].update(0)
        window['DownloadProgress'].update(0)
        window['HostB'].update(disabled=True)
        window['DownloadB'].update(disabled=True)
        window['DownloadProgress'].update(visible=False)
        errorcount += hostfiles(PORT=values['PORT'], directory=values['DirHost'], errorcount=errorcount)
        window['HostB'].update(disabled=False)
        window['DownloadB'].update(disabled=False)
        window['DownloadProgress'].update(visible=True)
    if event == 'DownloadB':
        window['ChecksumProgress'].update(0)
        window['DownloadProgress'].update(0)
        window['HostB'].update(disabled=True)
        window['DownloadB'].update(disabled=True)
        errorcount += downloadfiles(IP=values['IP'], PORT=values['PORT'], directory=values['DirDownload'], errorcount=errorcount)
        window['HostB'].update(disabled=False)
        window['DownloadB'].update(disabled=False)
    if event == 'StopB':
        window['HostB'].update(disabled=False)
        window['DownloadB'].update(disabled=False)
        window['DownloadProgress'].update(visible=True)
window.close()