# -*- coding: iso-8859-15 -*-

# ***************************************************************************************************
# readImgFromURL.py
# Modul for reading a flatfile which contains URLs of image files which are to
# be copied from given URL to the local disc (local directory).
# author: Bernd Grner
# since : 20141011
#
# call  : python readImgFromURL <flatfile> [-p] [-max[=<limit>]]
#
# params: flatfile: Name of the flatfile with full path. If only the file name
#                   is given the file is tried to read from current directory.
#         -p      : Logs the steps of the process to log-file readImgFromURL.log
#                   in the current directory.
#         -max    : If <limit> is given, the maximum number of image files with the same name
#                   (copied from different URLs) is limitted to this number. Each of these files
#                   obtain a numeric suffix (e.g. abc.jpg -> abc.1.jpg).
#                   If <limit> is NOT given (argument "-max" without limit, the default maximum
#                   number of 100 is gona be obtained (number unlimitted)!
#                   If not given, the limit is set to default value 100.
#
# ***************************************************************************************************

import os, sys

# --- To work with python version 2 and 3: ---
try :
    import urllib2
    urlOpen = urllib2.urlopen
except :
    import urllib.request
    urlOpen = urllib.request.urlopen

# --- To work with python version 2 and 3: ---
try    : fnfError = FileNotFoundError
except : fnfError = IOError

RCOK  =   0
RCBAD =  -1


# ***************************************************************************************************
# class for reading the flatfile and copying the referred image files to the
# local disk.
# ***************************************************************************************************
class cReadImgFromURL :

    DEF_MAX_INDEX   =   100         # - default maximum number of image files with same name
    
    # ***********************************************************************************************
    def __init__ ( self, flatFilePath, options = None ):
        '''
        contructor
        @param : str flatFilePath   Name with full path fo the flatfile
        @param : dic options        Dictionary with options
        '''
        self._flatFilePath  =   flatFilePath
        self._flatFile      =   None
        self._errMsg        =   None
        self._protFile      =   None
        self._protOut       =   False
        self._maxIndex      =   self.DEF_MAX_INDEX
        self._allNames      =   {}
        self._numCopied     =   0

        if  type( options ) == dict :
            self._protOut  = options.get( 'prot'  , False )
            self._maxIndex = options.get( 'maxidx', self.DEF_MAX_INDEX )
    
    # ***********************************************************************************************
    def _getImgFileName ( self, url ):
        '''
        Extracts the name of the image file from given URL.
        Checks if the image file already exists. If yes, appends a numeric suffix to the file name.
        @param : str url String which contais the URL
        @return: The evaluated filename, None if file name could not be evaluated.
        '''
        imgFileName = None
        tmpFileName = None
        baseName    = None
        fileName    = ""
        suffix      = None

        try :
            tmpFile = None

            # --- The URL must be provided as string: ---
            if  type( url ) == str :
                url = url.strip()
            else :
                url = None

            if  not url :
                return  None

            # --- Extract the Name of the image file: ---
            fileName    = url[ url.rfind( '/' ) + 1 : ]
            tmpFileName = fileName
            extIdx      = fileName.rfind( '.' )
            baseName    = fileName[  : extIdx ]
            extension   = fileName[  extIdx + 1 : ]

            # --- If the file name has already appeared before, start with appropriate Index: ---
            suffix = self._allNames.get( baseName, 0 )

            # --- Search an unused filename: ---
            while tmpFileName :
                # --- Filename already appeared in current process?: ---
                if  suffix :
                    tmpFileName = "%s.%d.%s" %( baseName, suffix, extension )

                # --- Now the file name is used at least once or even once more: ---
                suffix += 1

                tmpFile = open( tmpFileName, 'r' )

                # --- If the file doesn't exist exception 'fnfError' is  ---
                # --- thrown, otherwise close tempFile for next attempt: ---
                tmpFile.close()

                # --- Maximum attempts exceeded?: ---
                if  self._maxIndex and suffix >= self._maxIndex :
                    self._prot( "Maximum number (%d) for file '%s' exceeded!" %( self._maxIndex, fileName ) )
                    break

        except fnfError :
            # --- The file doesn't exist yet. Hope this happens always pretty soon: ---
            imgFileName = tmpFileName

        except :
            imgFileName  = None
            self._errMsg = "exception occurred in '%s()', image file '%s' skipped!\n   %s" \
                            %( self._getImgFileName.__name__, fileName, sys.exc_info()[1] )
            self._prot( self._errMsg )

        # --- Remember last used index for this file for next time: ---
        if  imgFileName and baseName :
            self._allNames[ baseName ] = suffix

        return  imgFileName

    # ***********************************************************************************************
    def _evalFlatFile ( self, ):
        '''
        Reads the lines of the flatfile and evaluates the given URL.
        Leaves method with RCOK on success, with an accordand error-code otherwise.
        '''
        retcode  =  RCOK

        try :
            for line in self._flatFile :
                retcode = self._readURL( line.strip() )

                if  retcode != RCOK :
                    break
        except :
            self._errMsg = "exception occurred in '%s()': %s" %( self._evalFlatFile.__name__, sys.exc_info()[1] )
            retcode = RCBAD

        return  retcode

    # ***********************************************************************************************
    def _openFlatFile ( self, ):
        '''
        Tries to open the flatfile if possible and opens a corresponding file handle.
        Leaves method with RCOK on success, with an accordand error-code otherwise.
        '''
        retcode  =  RCOK

        try :
            if  not self._flatFilePath :
                self._errMsg = "No flatfile given!"
                retcode = RCBAD

            if  retcode == RCOK :
                self._flatFile = open( self._flatFilePath, 'r' )

        except fnfError :
            self._errMsg = "file '%s' not found!" %( self._flatFilePath )
            retcode = RCBAD
        except :
            self._errMsg = "exception occurred in '%s()' while opening file '%s':\n   %s" \
                            %( self._openFlatFile.__name__, self._flatFile, sys.exc_info()[1] )
            retcode = RCBAD

        return  retcode

    # ***********************************************************************************************
    def _prot ( self, protstr ):
        '''
        Writes the given string to the specified log-file, if log-file is available.
        @param : str protstr String to be logged
        '''
        try :
            if  not self._protFile :
                return

            if  not protstr :
                return

            if  type( protstr ) != str :
                return

            self._protFile.write( "%s\n" %( protstr ) )
            self._protFile.flush()
        except :
            pass

        return

    # ***********************************************************************************************
    def _readURL ( self, url ):
        '''
        Evaluates the given URL.
        Copies the image file from given URL to the local directory under the same name.
        Leaves method with RCOK on success, with RCBAD otherwise.
        @param : str url String which contais the URL
        '''
        retcode     = RCOK
        imgFileName = None

        try :
            localImgFile = None
            response     = None

            # --- Check if the image file already exists. Provides an appropriate name: ---
            imgFileName = self._getImgFileName( url )

            if  not imgFileName :
                return  RCOK

            # --- Open URL: ---
            response = urlOpen( url )

            # --- Handle image file as binary: ---
            localImgFile = open( imgFileName, 'wb' )

            # --- Write image file to local disc: ---
            localImgFile.write( response.read() )

            # --- Close local image file: ---
            localImgFile.close()

            self._numCopied  += 1
            self._prot( "copy of '%s' OK!" %( imgFileName ) )
        except :
            self._errMsg = "exception occurred in '%s()': %s!" %( self._readURL.__name__, sys.exc_info()[1] )
            self._prot( self._errMsg )
            #retcode = RCBAD

        return  retcode

    # ***********************************************************************************************
    def _showResult ( self, rcin ):
        '''
        Shows the result of the task by printing an appropriate message to stdout.
        @param : int rcin    retcode of the task
        '''
        msgstr = None

        if  rcin == RCOK :
            msgstr  = "process OK!\n"
            msgstr += "number of copied files = %d\n" %( self._numCopied )
        else :
            msgstr  = self._errMsg

        if  msgstr :
            print     ( msgstr )
            self._prot( msgstr )

        return

    # ***********************************************************************************************
    def runTask ( self, ):
        '''
        public method for running the task.
        '''
        retcode  =  RCOK
        try :
            if  self._protOut :
                # --- Don't cancel task due to not having a log-file: ---
                try    : self._protFile = open( "./readImgFromURL.log", "w" )
                except : self._protFile = None

            retcode = self._openFlatFile()

            if  retcode == RCOK :
                retcode = self._evalFlatFile()

            if  self._flatFile :
                self._flatFile.close()

            self._showResult( retcode )
        except :
            print( "exception occurred in '%s(): %s'!" %( self.runTask.__name__, sys.exc_info()[1] ) )
            retcode = RCBAD

        return  retcode

# ***************************************************************************************************
# *** End: class cReadImgFromURL
# ***************************************************************************************************
def main ( argv ) :
    '''
    main function
    '''
    argc          =  len( argv )        # - habit from c-programming! -
    flatFilePath  =  None
    options       =  {}
    idx           =  1

    # --- Evaluate all arguments: ---
    while idx < argc :

        arglst = argv[ idx ].split( '=' )
        keywrd = arglst[ 0 ]

        # --- The flatfile must always be given first!: ---
        if  flatFilePath is None :
            flatFilePath = keywrd

        # --- If a protocol is desired: ---
        if  keywrd == '-p' :
            options[ 'prot' ] = True

        # --- Limit number of image files with same name or set no limit: ---
        if  keywrd == '-max' :
            if  len( arglst ) == 2 and arglst[ 1 ].isdigit() :
                options[ 'maxidx' ] = int( arglst[ 1 ] )        # - limit given
            else :
                options[ 'maxidx' ] = None                      # - abolish default limit
        
        idx += 1

    # --- Handle the task by a
    readImgFromURL = cReadImgFromURL( flatFilePath, options )

    # --- Read the given flatfile and copy the referred image files to the local disk: ---
    retcode = readImgFromURL.runTask()

    retcode  =  RCOK

retcode = main( sys.argv )

sys.exit( retcode )

# *** text end ***
