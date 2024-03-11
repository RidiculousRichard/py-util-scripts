import argparse
import glob
import os
import pathlib
import pypdf
import sys
import traceback


class ProcessingEx(Exception):
    pass

def populateCommandLineArgs(parser, pathsAsOption=True):
    parser.add_argument('--path' if pathsAsOption else 'path', nargs='+', default=None, help='Pdfs or directories containing pdfs to load, add password and save with any specified filename prefix added.')
    parser.add_argument('--out-dir', nargs='?', type=str, default='', help='Directory to output password protected pdfs; default is in source dir.  Can be an absolute or relative path.')
    parser.add_argument('--filename-prefix', nargs='?', type=str, default='pwd-', help='Prefix to add to filename to indicate file is password protected. Default is "%(default)s".')
    parser.add_argument('--password', nargs='?', type=str, default=None, help='Password to protect generated pdf.')

def parseArgs(parser, args):
    settings = dict()
    parsed = parser.parse_args(args)
    settings['paths'] = parsed.path
    settings['outDir'] = parsed.out_dir
    settings['prefix'] = parsed.filename_prefix
    settings['password'] = parsed.password
    return settings

def passwordProtectPdf(dir='', filename='', outDir='', prefix='', password=''):
    if (len(prefix) > 0) and filename.startswith(prefix):
        print('Skipping {} as it already has the prefix {}'.format(filename, prefix))
        return
    absDir = os.path.abspath(dir)
    absPath = os.path.abspath(os.path.join(absDir, filename))
    if os.path.isabs(outDir):
        # outDir is an absolute path already, creating it if it does not exist.
        absOutDir = os.path.abspath(outDir)
    elif (len(outDir) > 0) and os.path.isdir(outDir):
        # outDir is an existing directory already so use it.
        absOutDir = os.path.abspath(outDir)
    else:
        # Tack the outDir onto the end of the absDir
        absOutDir = os.path.abspath(os.path.join(absDir, outDir))
    # Output path
    absOutPath = os.path.join(absOutDir, prefix+filename)
    # Show progress
    print('Adding password to {} and saving as {}.'.format(absPath, absOutPath))
    # Open the input pdf
    reader = pypdf.PdfReader(absPath)
    # Create the output directory if it does not exist
    pathlib.Path(absOutDir).mkdir(parents=True, exist_ok=True)
    # Encrypt and write out the new pdf
    writer = pypdf.PdfWriter()
    writer.append_pages_from_reader(reader)
    writer.encrypt(password)
    with open(absOutPath, "wb") as out_file:
        writer.write(out_file)
    return 

def passwordProtectPdfs(paths=None, outDir='', prefix='', password=None):
    print('    paths:    ', paths)
    print('    outDir:   ', outDir)
    print('    prefix:   ', prefix)
    print('    password: ', password)

    if paths is None:
        raise ProcessingEx("Specified paths cannot be None")
    if outDir is None:
        outDir = ''
    if prefix is None:
        prefix = ''
    if (password is None) or len(password) == 0:
        raise ProcessingEx("Cannot protect a PDF without a password") 

    for path in paths:
        if os.path.isfile(path):
            # Attempt to work on the file
            passwordProtectPdf(os.path.dirname(path), os.path.basename(path), outDir, prefix, password)
        elif os.path.isdir(path):
            failures = dict()
            # A directory, walk it for pdfs
            for filename in glob.glob(pathname='*.[pP][dD][fF]', root_dir=path):
                try:
                    passwordProtectPdf(path, filename, outDir, prefix, password)
                except Exception as ex:
                    traceback.print_exc()
                    failures[filename] = ex
            if len(failures) > 0:
                print('{} failed files:'.format(len(failures)))
                for fail, ex in failures.items():
                    print('    {}'.format(fail))
        else:
            print("{} is not a valid path".format(path))
    return

def runAsScript():
    parser = argparse.ArgumentParser(prog='password-protect-pdfs', description='Load in and re-save pdfs with a password.')
    populateCommandLineArgs(parser, False)
    passwordProtectPdfs(**parseArgs(parser, sys.argv[1:]))
    return

if __name__ == "__main__":
    runAsScript()