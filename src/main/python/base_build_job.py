import os
import shutil
from globals import root_path
from util import hash_dir, make_dir_if_needed

__author__ = 'richardnorth'

class BaseBuildJob(object):
    def __init__(self, id, data):
        super(BaseBuildJob, self).__init__()
        self.id = id
        self.data = data
        self.package_path = os.path.join(root_path, self.id)
        self.package_cache = os.path.join(self.package_path, '.bacon.d')
        self.stored_fingerprint_path = os.path.join(self.package_cache, "fingerprint")
        self.dependency_jobs = []

        make_dir_if_needed(self.package_cache)

    def needs_rerun(self, fingerprint_tag):

        fingerprint_file_path = self.stored_fingerprint_path + "-" + fingerprint_tag
        package_hash = self.fingerprint()

        if os.path.isfile(fingerprint_file_path):
            with open(fingerprint_file_path) as fingerprint_file:
                stored_fingerprint = fingerprint_file.read()
            if package_hash == stored_fingerprint:
                print "Skipping build for %s:%s" % (self.id, fingerprint_tag)
                return False

        return True


    def remember_fingerprint(self, fingerprint_tag):
        with open(self.stored_fingerprint_path + "-" + fingerprint_tag, "w") as fingerprint:
            package_hash = self.fingerprint()

            fingerprint.write(package_hash)

    def clean(self):
        if os.path.isdir(self.package_cache):
            shutil.rmtree(self.package_cache)

    def compile(self):
        return

    def run(self):
        return

    def archive(self):
        return

    def fingerprint(self):
        package_hash = hash_dir(self.package_path)

        for dependency in self.dependency_jobs:
            package_hash.update(dependency.fingerprint())

        return package_hash.hexdigest()