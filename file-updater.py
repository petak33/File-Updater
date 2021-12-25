import http.server
import socketserver
import glob
import os
from requests import get
import requests
import hashlib

print('This is File Updater v1.0')
print('Place file-updater.py next to the folders you wish to upload/download files to')

PORT = 6969
IP = 'localhost'

print()
print('Default PORT is \"'+str(PORT)+'\"')
print('Default IP is \"'+IP+'\"')
print()

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
            print('Calculating Checksum... '+str(len(dm5filelist)+1)+'/'+str(len(filedirlist)))
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

while True:
    hostordownload = input('Do you wish \"host\" or \"download\" file/files?: ')

    if hostordownload == 'host':
        print()
        hostport = input('Which port do you wish to host your files on?(Leave empty for default): ')
        if hostport != '':
            try:
                PORT = int(hostport)
            except:
                PORT = 6969
        else:
            PORT = 6969

        print()
        for singledir in glob.glob("*/"):
            print(singledir[0:-1])
        hostDIRECTORY = input('Which directory do you wish to host?: ')
        if not os.path.exists(os.getcwd()+'/'+hostDIRECTORY) or hostDIRECTORY == '':
            print()
            print('Directory doesn\'t exist')
        else:
            class Handler(http.server.SimpleHTTPRequestHandler):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, directory=hostDIRECTORY, **kwargs)

            print()
            print('Creating Changelog...')
            hostchangelog = open(file=hostDIRECTORY+'/'+'FileChangeLog.txt', mode='w+', encoding='utf-8')
            for file in checksumfiles(directory=hostDIRECTORY):
                hostchangelog.write(file+'\n')
            hostchangelog.close()
            print('Changelog Successfully Created!')

            publicip = get('https://api.ipify.org').text
            with socketserver.TCPServer(("", PORT), Handler) as httpd:
                print()
                print('Server running at '+publicip+':'+str(PORT))
                httpd.serve_forever()

    if hostordownload == 'download':
        print()
        downloadip = input('Which IP do you wish to download files from?(Leave empty for default): ')
        if downloadip != '':
            IP = downloadip
        else:
            IP = 'localhost'
        downloadport = input('Which port do you wish to download files from?(Leave empty for default): ')
        if downloadport != '':
            try:
                PORT = int(downloadport)
            except:
                PORT = 6969
        else:
            PORT = 6969
        URL = 'http://'+IP+':'+str(PORT)+'/'

        print()
        print('Trying to connect to host...')
        ConnectionCheck = ''
        try:
            ConnectionCheck = str(requests.get(url=URL))
            if ConnectionCheck == '<Response [200]>':
                print('Connection Established!')
                print()
            elif ConnectionCheck != '':
                print('Unknown Error code: '+ConnectionCheck)
                print()
        except:
            print('Error: Unable to establish connection')
            print()

        if ConnectionCheck == '<Response [200]>':
            for singledir in glob.glob("*/"):
                print(singledir[0:-1])
            downloadDIRECTORY = ''
            downloadDIRECTORYconfirm = ''
            downloadDIRECTORY = input('Which directory do you wish to download files to?(Non existing dir will be created): ')
            if not downloadDIRECTORY == '':
                downloadDIRECTORYconfirm = input('Are you sure you want to download files to this directory: \"'+downloadDIRECTORY+'\" (\"yes\" to confirm): ')
            else:
                print()
                print('Error: Directory needs a name')
            if downloadDIRECTORYconfirm == 'yes' and downloadDIRECTORY != '':
                if not os.path.exists(os.getcwd()+'/'+downloadDIRECTORY):
                    print('Creating directory with the name \"'+downloadDIRECTORY+'\"')
                    os.mkdir(os.getcwd()+'/'+downloadDIRECTORY)

                print()
                downloadchangelog = checksumfiles(directory=downloadDIRECTORY)
                dhostchangelog = (requests.get(url=URL+'FileChangeLog.txt')).text
                listdhostchangelog = []
                dhclastbyte = -1
                dhccurrentbyte = 0
                for x in dhostchangelog:
                    if dhostchangelog[dhccurrentbyte:dhccurrentbyte+1] == '\n':
                        listdhostchangelog.append(dhostchangelog[dhclastbyte+1:dhccurrentbyte-1])
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
                        print('Removing '+cutsinglefile+'...')
                        os.remove(downloadDIRECTORY+'/'+cutsinglefile)
                print('Removal of Old Files Completed!')
                print()

                print('Removing Empty Folders...')
                removeemptyfolders(directory=downloadDIRECTORY)
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
                            if not os.path.exists(downloadDIRECTORY+'\\'+folderpath):
                                print('Creating new folder '+folderpath+'...')
                                os.mkdir(downloadDIRECTORY+'\\'+folderpath)
                        anchorbyte += 1
                print('Creating new folders Completed!')
                print()

                print('Downloading New Files...')
                dwcurrentfile = 1
                for singleneededfile in neededfiles:
                    print('Downloading file '+singleneededfile+' '+str(dwcurrentfile)+'/'+str(len(neededfiles)))
                    urlsingleneededfile = singleneededfile.replace('\\', '/')
                    downloadfile = requests.get(url=URL+urlsingleneededfile)
                    open(downloadDIRECTORY+'\\'+singleneededfile, 'wb').write((downloadfile.content))
                    dwcurrentfile += 1
                print('All New Files Successfully Downloaded!')
                print()
                print('You are Up-To Date!')
                print()

    if hostordownload == 'exit' or hostordownload == 'stop':
        exit()