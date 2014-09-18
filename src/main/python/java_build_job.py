import os
import subprocess
import glob2
from base_build_job import BaseBuildJob
from globals import build_jobs
from util import make_dir_if_needed

__author__ = 'richardnorth'


class JavaModuleBuildJob(BaseBuildJob):
    """docstring for JavaModuleBuildJob"""

    def __init__(self, id, data):
        super(JavaModuleBuildJob, self).__init__(id, data)
        self.classes_cache = os.path.join(self.package_cache, "classes")
        self.archive_cache = os.path.join(self.package_cache, "dist")

        if 'dependencies' in self.data:
            for dependency_id in self.data['dependencies']:
                self.dependency_jobs.append(build_jobs[dependency_id])

        make_dir_if_needed(self.classes_cache)
        make_dir_if_needed(self.archive_cache)

    def calculate_classpath(self):
        classpath = []
        for dependency_job in self.dependency_jobs:
            dependency_classes_cache = dependency_job.classes_cache
            classpath.append(dependency_classes_cache)
        classpath.append(self.classes_cache)
        return classpath

    def classpath_string(self):
        return ':'.join(self.calculate_classpath())

    def compile(self):
        # print "Building Java %s" % self.id
        if not self.needs_rerun("compile"):
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

        self.remember_fingerprint("compile")

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

        if not self.needs_rerun("archive"):
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

        self.remember_fingerprint("archive")
