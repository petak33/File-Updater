import http.server
import socketserver
import socket
import os
import requests
import hashlib
import threading
import PySimpleGUI as gui
import time
import zipfile
import random
import glob
import shutil

ProgramName = 'File Updater GUI v1.4.1'
print('This is '+ProgramName)

gui.theme('Dark Grey 11')

windowlayout = [
    [gui.I(key='DirHost', enable_events=True, visible=False), gui.I(key='DirDownload', enable_events=True, visible=False)],
    [gui.B(key='HostB', button_text='Host', size=8), gui.FolderBrowse(target='DirHost', button_text='Folder to Host', size=15), gui.StatusBar(key='DirHostStatus', text='', size=17)],
    [gui.B(key='DownloadB', button_text='Download', size=8), gui.FolderBrowse(target='DirDownload', button_text='Download Folder', size=15), gui.StatusBar(key='DirDownloadStatus', text='', size=17)],
    [gui.T(text='IP', size=(4)), gui.I(key='IP', default_text='localhost', size=(15), tooltip='Host\'s IP'), gui.T(size=16), gui.Combo(key='CompressionType', values=['ZIP', 'BZIP2', 'LZMA'], tooltip='Compression Type', default_value='ZIP', size=5)],
    [gui.T(text='PORT', size=(4)), gui.I(key='PORT', default_text='6969', size=(5), tooltip='Host\'s PORT'), gui.T(size=16), gui.Checkbox(key='CompressionOpt', default=False, text='File Compression', tooltip='Requires more storage during hosting/downloading (Must be enabled on server and client to work)')],
    [gui.Multiline(key='Console', disabled=True, autoscroll=True, size=(49,5))],
    [gui.ProgressBar(key='ChecksumProgress', max_value=100, size=(33,20))],
    [gui.ProgressBar(key='DownloadProgress', max_value=100, size=(33,20))]
]

window = gui.Window(ProgramName, layout=windowlayout, icon=r'favicon.ico')

def ButtonInputUpdate(state):
    window['IP'].update(disabled=state)
    window['PORT'].update(disabled=state)
    window['HostB'].update(disabled=state)
    window['DownloadB'].update(disabled=state)
    window['CompressionOpt'].update(disabled=state)
    window['CompressionType'].update(disabled=state)

def createpath(path):
    currentdir = 0
    cpath = ''
    singledirlist = (path.replace('\\', '/')).split('/')
    for directory in singledirlist:
        cpath += directory+'/'
        if currentdir + 1 == len(singledirlist):
            break
        if ':' not in directory:
            if not os.path.exists(cpath):
               os.mkdir(cpath)
        currentdir += 1

def listtostr(list):
    string = ''
    for x in list:
        string += x+'\n'
    return string

def strtolist(str):
    list = []
    bytea = -1
    byteb = 0
    for x in str:
        if x == '\n':
            list.append(str[bytea+1:byteb])
            bytea -= bytea
            bytea += byteb
        byteb += 1
    return list

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
            try:
                rddata = filecheck.read()
                md5output = hashlib.md5(str(rddata).encode('iso-8859-1')).hexdigest()
                dm5filelist.append((file + ' ')[len(directory) + 1:-1] + '|' + md5output)
            except:
                filesize = os.path.getsize(file)
                chunksize = 1024000000
                window['Console'].print('Calculating Large File, This Might Take a While... (File Size: '+str(filesize//1000000000)+'GB)')
                rddata = ''
                largefileprogress = 0
                window['Console'].print('Large File Checksum: 0%')
                while True:
                    rdchunk = filecheck.read(int(chunksize))
                    rddata += hashlib.md5(str(rdchunk).encode('iso-8859-1')).hexdigest()
                    if not rdchunk:
                        window['Console'].print('Large File Checksum: 100%')
                        md5output = hashlib.md5(str(rddata).encode('utf-8')).hexdigest()
                        print(md5output)
                        dm5filelist.append((file + ' ')[len(directory) + 1:-1] + '|' + md5output)
                        break
                    largefileprogress += 1
                    if int(((100 / (filesize / chunksize)) * largefileprogress) // 1) < 100:
                        window['Console'].print('Large File Checksum: ' + str(int(((100 / (filesize / chunksize)) * largefileprogress) // 1)) + '%')
    window['ChecksumProgress'].update(100)
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

def hostserver(PORT, directory):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

def hostfiles(PORT, directory, compression, compressiontype):
    if PORT != '':
        try:
            PORT = int(PORT)
        except:
            PORT = 6969
    else:
        PORT = 6969

    if not os.path.exists(directory) or directory == '':
        window['Console'].print('Error: Directory doesn\'t exist')
        window['DownloadProgress'].update(visible=True)
        ButtonInputUpdate(state=False)
        exit()

    else:
        if os.path.exists(directory + '\\file-updater-cache'):
            for file in glob.glob(directory + '\\file-updater-cache' + '\\*'):
                os.remove(file)
            os.rmdir(directory+'\\file-updater-cache')

        window['Console'].print('')
        window['Console'].print('Creating Changelog...')
        hostchangelog = open(file=directory + '/' + 'FileChangeLog.txt', mode='w+', encoding='utf-8')
        for file in checksumfiles(directory=directory):
            hostchangelog.write(file + '\n')
        hostchangelog.close()
        window['Console'].print('Changelog Successfully Created!')

        publicip = requests.get('https://api.ipify.org').text
        window['Console'].print()
        window['Console'].print('Server running at ' + publicip + ':' + str(PORT))

        HostServerThread = threading.Thread(daemon=True, target=hostserver, args=[PORT, directory])
        HostServerThread.start()

        if compression == True:
            if compressiontype == 'ZIP':
                CompressionType = zipfile.ZIP_DEFLATED
            if compressiontype == 'BZIP2':
                CompressionType = zipfile.ZIP_BZIP2
            if compressiontype == 'LZMA':
                CompressionType = zipfile.ZIP_LZMA
            if not os.path.exists(directory + '\\file-updater-cache'):
                os.mkdir(directory+'\\file-updater-cache')
            HOST = socket.gethostbyname(socket.gethostname())
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.bind((HOST, PORT))
            while True:
                data, addr = s.recvfrom(1024000)
                rdata = data.decode('utf-8')
                listdata = strtolist(rdata)
                if listdata[0] == '--requestfiles--':
                    randomcode = str(random.random())[2:-1]
                    print('Compressing...')
                    with zipfile.ZipFile(directory+'\\file-updater-cache\\'+randomcode+'.zip', mode='w', compression=CompressionType) as wzip:
                        for file in listdata:
                            if file != '--requestfiles--':
                                print(file)
                                wzip.write(directory+'\\'+file, file)
                    print('Sending randomcode to ' + str(addr) + '...')
                    s.sendto(randomcode.encode('utf-8'), addr)
                if listdata[0] == '--removezip--':
                    os.remove(directory+'\\file-updater-cache\\'+listdata[1]+'.zip')

def downloadfiles(IP, PORT, directory, compression):
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
        ButtonInputUpdate(state=False)
        exit()

    window['Console'].print()
    window['Console'].print('Trying to connect to host...')
    ConnectionCheck = ''
    try:
        ConnectionCheck = str(requests.get(url=URL))
        if ConnectionCheck == '<Response [200]>':
            window['Console'].print('Connection Established!')
        elif ConnectionCheck != '':
            window['Console'].print('Unknown Error code: ' + ConnectionCheck)
            ButtonInputUpdate(state=False)
            exit()
    except:
        window['Console'].print('Error: Unable to establish connection')
        ButtonInputUpdate(state=False)
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
        movedfiles = []
        window['Console'].print()
        window['Console'].print('Checking and Removing/Moving Old Files...')
        for singlefile in downloadchangelog:
            rmfileornot = True
            movefile = False
            anchorbyte = 0
            for x in singlefile:
                if x == '|':
                    cutsinglefile = singlefile[0:anchorbyte]
                anchorbyte += 1
            for singlecheckfile in listdhostchangelog:
                singlefilemovef = (singlefile.split('\\'))
                singlecheckfilemovef = (singlecheckfile.split('\\'))
                if singlefile == singlecheckfile:
                    unneededfiles.append(cutsinglefile)
                    rmfileornot = False
                elif singlefilemovef[len(singlefilemovef)-1] == singlecheckfilemovef[len(singlecheckfilemovef)-1] and singlefile not in listdhostchangelog:
                    movedfiles.append(singlecheckfile)
                    filetomove = singlefile.split('|')[0]+'|'+singlecheckfile.split('|')[0]
                    movefile = True
                    rmfileornot = False
            if rmfileornot == True:
                window['Console'].print('Removing ' + cutsinglefile + '...')
                os.remove(directory + '/' + cutsinglefile)
            elif movefile == True:
                window['Console'].print('Moving '+cutsinglefile+'...')
                createpath(path=directory+'\\'+filetomove.split('|')[1])
                shutil.move(directory+'\\'+filetomove.split('|')[0], directory+'\\'+filetomove.split('|')[1])
        window['Console'].print('Removal/Moving of Old Files Completed!')
        window['Console'].print()

        window['Console'].print('Removing Empty Folders...')
        removeemptyfolders(directory=directory)
        window['Console'].print('Removal of Empty Folders Completed!')
        window['Console'].print()

        neededfiles = []
        for neededsinglefile in listdhostchangelog:
            fileexist = False
            anchorbyte = 0
            for x in neededsinglefile:
                if x == '|':
                    cutneededsinglefile = neededsinglefile[0:anchorbyte]
                anchorbyte += 1
            for unneededsinglefile in unneededfiles:
                if cutneededsinglefile == unneededsinglefile or neededsinglefile in movedfiles:
                    fileexist = True
            if fileexist == False and cutneededsinglefile != 'FileChangeLog.txt':
                neededfiles.append(cutneededsinglefile)

        if neededfiles == []:
            window['DownloadProgress'].update(100)
            window['Console'].print('You are Up-To Date!')
            ButtonInputUpdate(state=False)
            exit()

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

        if compression == True:
            cIP = socket.gethostbyname(socket.gethostname())
            cPORT = PORT
            sIP = IP
            sPORT = PORT
            server = (sIP, sPORT)
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.bind((cIP, cPORT))

            window['Console'].print('Requesting files...')
            s.sendto(('--requestfiles--\n'+listtostr(neededfiles)).encode('utf-8'), server)
            window['Console'].print('Waiting for File...')
            data, addr = s.recvfrom(1024000)
            filecode = data.decode('utf-8')
            window['Console'].print('File received!')
            window['Console'].print()
            compressedURL = URL+'file-updater-cache/'+filecode+'.zip'

            window['Console'].print('Downloading Compressed File... (This might take a while)')
            downloadfile = requests.get(url=compressedURL)
            open(directory+'\\'+filecode+'.zip', 'wb').write((downloadfile.content))
            window['Console'].print('Compressed File Successfully Downloaded!')
            window['Console'].print()
            s.sendto(('--removezip--\n'+str(filecode)+'\n').encode('utf-8'), server)
            s.close()

            window['Console'].print('Decompressing Files...')
            with zipfile.ZipFile((directory+'/'+filecode+'.zip'), mode='r') as rzip:
                rzip.extractall(path=directory)
            os.remove(directory+'\\'+filecode+'.zip')
            window['Console'].print('Decompression Completed!')
        else:
            window['Console'].print('Downloading New Files...')
            dwcurrentfile = 1
            for singleneededfile in neededfiles:
                window['Console'].print('Downloading file ' + singleneededfile + ' ' + str(dwcurrentfile) + '/' + str(len(neededfiles)))
                window['DownloadProgress'].update((100/len(neededfiles))*dwcurrentfile)
                urlsingleneededfile = singleneededfile.replace('\\', '/')
                downloadfile = requests.get(url=URL + urlsingleneededfile)
                open(directory + '\\' + singleneededfile, 'wb').write((downloadfile.content))
                dwcurrentfile += 1
                window['Console'].print('All New Files Successfully Downloaded!')
        window['DownloadProgress'].update(100)
        window['Console'].print()
        window['Console'].print('You are Up-To Date!')
        ButtonInputUpdate(state=False)

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
            window['DownloadProgress'].update(visible=False)
            ButtonInputUpdate(state=True)
            HostFilesThread = threading.Thread(daemon=True, target=hostfiles, args=[values['PORT'], values['DirHost'], values['CompressionOpt'], values['CompressionType']])
            HostFilesThread.start()
        if event == 'DownloadB':
            window['ChecksumProgress'].update(0)
            window['DownloadProgress'].update(0)
            if (values['IP'] == 'localhost' or values['IP'] == '127.0.0.1') and values['CompressionOpt'] == True:
                window['Console'].print('Error: Local Address can\'t be set to localhost while Compression is on')
            else:
                ButtonInputUpdate(state=True)
                DownloadFilesThread = threading.Thread(daemon=True, target=downloadfiles, args=[values['IP'], values['PORT'], values['DirDownload'], values['CompressionOpt']])
                DownloadFilesThread.start()
    window.close()

GuiWindowThread = threading.Thread(daemon=True, target=guiwindow)
GuiWindowThread.start()

while True:
    if GuiWindowThread.is_alive() == False:
        exit()
    else:
        time.sleep(3)