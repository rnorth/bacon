import hashlib
import os
import glob2

__author__ = 'richardnorth'


def hash_dir(dir):
    h = hashlib.sha256()
    for file in glob2.glob(os.path.join(dir, '**', '*')):
        if os.path.isfile(file):
            f = open(file)
            while True:
                buf = f.read(16384)
                if len(buf) == 0: break
                h.update(buf)
    return h


def make_dir_if_needed(path):
    if not os.path.isdir(path):
        os.mkdir(path)