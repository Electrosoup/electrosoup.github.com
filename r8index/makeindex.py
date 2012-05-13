from __future__ import with_statement

import os
import setuptools
import shutil
import subprocess
import sys
import tarfile
import time
import zipfile
import tempfile

class TarArchive:
    def __init__(self, filename):
        self.filename = filename
        self.tgz = tarfile.TarFile.gzopen(filename, 'r')

    def names(self):
        return self.tgz.getnames()

    def lines(self, name):
        return self.tgz.extractfile(name).readlines()

    def extract(self, name, tempdir):
        return self.tgz.extract(name, tempdir)

    def extractall(self, tempdir):
        os.system('cd %s && tar xzf %s' % (tempdir,
                                           os.path.abspath(self.filename)))

    def close(self):
        return self.tgz.close()

class ZipArchive:
    def __init__(self, filename):
        self.filename = filename
        self.zipf = zipfile.ZipFile(filename, 'r')

    def names(self):
        return self.zipf.namelist()

    def lines(self, name):
        return self.zipf.read(name).split('\n')

    def extract(self, name, tempdir):
        data = self.zipf.read(name)
        fn = name.split(os.sep)[-1]
        fn = os.path.join(tempdir, fn)
        f = open(fn, 'wb')
        f.write(data)

    def extractall(self, tempdir):
        os.system('cd %s && unzip %s' % (tempdir,
                                         os.path.abspath(self.filename)))

    def close(self):
        return self.zipf.close()

def _extractNameVersion(filename, tempdir):
    print 'Parsing:', filename

    if filename.endswith('.gz') or filename.endswith('.tgz'):
        archive = TarArchive(filename)

    elif filename.endswith('.egg') or filename.endswith('.zip'):
        archive = ZipArchive(filename)
    try:
        for name in archive.names():

            if name.endswith('PKG-INFO'):

                project, version = None, None

                lines = archive.lines(name)

                for line in lines:
                    key, value = line.split(':', 1)

                    if key == 'Name':
                        project = value.strip()

                    elif key == 'Version':
                        version = value.strip()

                    if project is not None and version is not None:
                        return project, version

        # no PKG-INFO found, do it the hard way.
        archive.extractall(tempdir)
        dirs = sorted(os.listdir(tempdir))
        dir = os.path.join(tempdir, dirs[0])
        if not os.path.isdir(dir):
            dir = tempdir
        command = ('cd %s && %s setup.py --name --version'
                   % (dir, sys.executable))
        popen = subprocess.Popen(command,
                                 stdout=subprocess.PIPE,
                                 shell=True,
                                 )
        output = popen.communicate()[0]
        return output.splitlines()[:2]

    finally:
        archive.close()


def mkindex():
    projects = {}
    for fname in sorted(os.listdir('.')):
        try:
            tempdir = tempfile.mkdtemp()
            project, revision = _extractNameVersion(fname, tempdir)
            projects.setdefault(project, []).append((revision, fname))
        finally:
            shutil.rmtree(tempdir)

    items = projects.items()
    items.sort()

    topname = 'index'

    os.makedirs(topname)
    top = open('%s/index.html' % topname, 'w')
    top.writelines(['<html>\n',
                    '<body>\n',
                    '<h1>Package Index</h1>\n',
                    '<ul>\n'])

    for key, value in items:
        print 'Project: %s' % key
        dirname = '%s/%s' % (topname, key)
        os.makedirs(dirname)
        top.write('<li><a href="%s">%s</a>\n' % (key, key))

        sub = open('%s/%s/index.html' % (topname, key), 'w')
        sub.writelines(['<html>\n',
                        '<body>\n',
                        '<h1>%s Distributions</h1>\n' % key,
                        '<ul>\n'])

        for revision, archive in value:
            print '  -> %s, %s' % (revision, archive)
            sub.write('<li><a href="../../%s">%s</a>\n' % (archive, archive))

        sub.writelines(['</ul>\n',
                        '</body>\n',
                        '</html>\n'])

    top.writelines(['</ul>\n',
                    '</body>\n',
                    '</html>\n'])
    top.close()

def main():
    here = os.path.dirname(os.path.abspath(sys.modules[__name__].__file__))
    with open(os.path.join(here, 'TIMESTAMP.txt'), 'w') as f:
        print >>f, time.time()
    for index in (('1', 'production'),):
        path = os.path.join(here, *index)
        os.chdir(path)
        if os.path.exists('index'):
            shutil.rmtree('index')
        if os.path.exists('index.html'):
            os.remove('index.html')
        mkindex()
        with open('index.html', 'w') as f: 
            print >>f, '<html><head><title>%s/%s</title></head>' % index
            print >>f, '<body>'
            for fn in sorted(os.listdir(path)):
                if fn.startswith('.') or fn in ('index', 'index.html'):
                    continue
                print >>f, '<a href="%s">%s</a><br/>' % (fn, fn)
            print >>f, '</body></html>' 
            
if __name__ == '__main__':
    main()
