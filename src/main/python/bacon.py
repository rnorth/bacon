#!/usr/bin/env python

import yaml
import os
import sys
import glob2
import subprocess
import hashlib
import shutil

root_path = sys.argv[1]

if len(sys.argv) > 2:
    task = sys.argv[2]
else:
    task = "build"

build_jobs = {}
build_order = []


class BaseBuildJob(object):
    def __init__(self, id, data):
        super(BaseBuildJob, self).__init__()
        self.id = id
        self.data = data
        self.package_path = os.path.join(root_path, self.id)
        self.package_cache = os.path.join(self.package_path, '.bacon.d')
        self.stored_fingerprint_path = os.path.join(self.package_cache, "fingerprint")

        make_dir_if_needed(self.package_cache)

    def check_changes(self):

        self.package_hash = hash_dir(self.package_path)
        if os.path.isfile(self.stored_fingerprint_path):
            with open(self.stored_fingerprint_path) as fingerprint:
                stored_fingerprint = fingerprint.read()
            if self.package_hash == stored_fingerprint:
                # print "Skipping build for %s" % self.id
                return False
        return True

    def remember_fingerprint(self):
        with open(self.stored_fingerprint_path, "w") as fingerprint:
            fingerprint.write(self.package_hash)

    def clean(self):
        if os.path.isdir(self.package_cache):
            shutil.rmtree(self.package_cache)

    def build(self):
        return

    def run(self):
        return

    def archive(self):
        return


class JavaModuleBuildJob(BaseBuildJob):
    """docstring for JavaModuleBuildJob"""

    def __init__(self, id, data):
        super(JavaModuleBuildJob, self).__init__(id, data)
        self.classes_cache = os.path.join(self.package_cache, "classes")
        self.archive_cache = os.path.join(self.package_cache, "dist")

        make_dir_if_needed(self.classes_cache)
        make_dir_if_needed(self.archive_cache)

    def calculate_classpath(self):
        classpath = []
        for dependency in self.data['dependencies']:
            dependency_job = build_jobs[dependency]
            dependency_classes_cache = dependency_job.classes_cache
            classpath.append(dependency_classes_cache)
        classpath.append(self.classes_cache)
        return classpath

    def classpath_string(self):
        return ':'.join(self.calculate_classpath())

    def build(self):
        # print "Building Java %s" % self.id
        if self.check_changes() == False:
            return

        base_build_args = ['javac', '-d', self.classes_cache]
        if self.data.has_key('dependencies'):
            base_build_args.append('-cp')
            base_build_args.append(self.classpath_string())

        source_glob = os.path.join(self.package_path, "src", "main", "java", "**", "*.java")
        for source_file in glob2.glob(source_glob):
            command = base_build_args
            command.append(source_file)

            subprocess.check_call(command)

        self.remember_fingerprint()

    def run(self):

        if not self.data.has_key('main-class'):
            return

        base_run_args = ['java']
        if self.data.has_key('dependencies'):
            base_run_args.append('-cp')
            base_run_args.append(self.classpath_string())

        command = base_run_args
        command.append(self.data['main-class'])

        subprocess.check_call(command)

    def archive(self):

        if self.check_changes() == False:
            return

        if not self.data.has_key('archive'):
            return

        archive_data = self.data['archive']
        artifact_path = os.path.join(self.archive_cache, "%s.jar" % archive_data['artifactId'])
        jar_args = ['jar', 'cf', artifact_path]
        for dependency_path in self.calculate_classpath():
            for dependency_class in glob2.glob(os.path.join(dependency_path, '**', '*.class')):
                jar_args.append(dependency_class)

        subprocess.check_call(jar_args)


class BundleBuildJob(BaseBuildJob):
    """docstring for BundleBuildJob"""


def hash_dir(dir):
    h = hashlib.sha256()
    for file in glob2.glob(os.path.join(dir, '**', '*')):
        if os.path.isfile(file):
            f = open(file)
            while True:
                buf = f.read(16384)
                if len(buf) == 0: break
                h.update(buf)
    return h.hexdigest()


def make_dir_if_needed(path):
    if not os.path.isdir(path):
        os.mkdir(path)


def parse_bundle_build_file(id, data):
    for dependency in data['contents']:
        parse_build_file(dependency)
    return BundleBuildJob(id, data)


def parse_java_build_file(id, data):
    if data.has_key('dependencies'):
        for dependency in data['dependencies']:
            parse_build_file(dependency)
    return JavaModuleBuildJob(id, data)


def parse_build_file(package_path):
    build_file_path = os.path.join(package_path, 'build.yml')
    root_relative_path = os.path.relpath(package_path, root_path)

    if build_jobs.has_key(root_relative_path):
        return

    f = open(build_file_path)
    data = yaml.safe_load(f)
    f.close()

    if data['type'] == 'bundle':
        job = parse_bundle_build_file(root_relative_path, data)

    if data['type'] == 'java':
        job = parse_java_build_file(root_relative_path, data)

    # Hold onto a parsed job definition
    build_jobs[root_relative_path] = job

    # Constructing a topologically sorted build order
    if root_relative_path not in build_order:
        build_order.append(root_relative_path)


parse_build_file(root_path)

# print "build order:"
# print yaml.dump(build_order)

#print "task: %s" % task

if task == "build":
    goals = ["build"]
elif task == "clean":
    goals = ["clean"]
elif task == "run":
    goals = ["build", "run"]
elif task == "archive":
    goals = ["build", "archive"]

for goal in goals:
    for job_key in build_order:

        print "%30s :%s" % (job_key, goal)

        job = build_jobs[job_key]
        if goal == "build":
            job.build()
        elif goal == "clean":
            job.clean()
        elif goal == "run":
            job.run()
        elif goal == "archive":
            job.archive()