from genericpath import isfile
import os
import subprocess
import glob2
import urllib
from base_build_job import BaseBuildJob
from globals import build_jobs
from util import make_dir_if_needed

__author__ = 'richardnorth'


class IvyDependencyJob(BaseBuildJob):

    def __init__(self, dependent_id, dependency_id):
        super(IvyDependencyJob, self).__init__(dependent_id, {})
        self.ivy_executable = os.path.expanduser("~/.bacon.d/ivy.jar")
        split_dep = dependency_id.split(":")
        self.group_id = split_dep[0]
        self.artifact_id = split_dep[1]
        self.version = split_dep[2]

        if not isfile(self.ivy_executable):
            print "Downloading ivy..."
            urllib.urlretrieve("http://central.maven.org/maven2/org/apache/ivy/ivy/2.3.0/ivy-2.3.0.jar", self.ivy_executable)

    def classpath_string(self, scope):
        resolved_classpath_file = os.path.join(self.package_cache, "%s-%s-%s" % (self.group_id, self.artifact_id, self.version))

        if not isfile(resolved_classpath_file):
            print "Resolving ivy dependency %s" % self
            subprocess.check_call(["java", "-jar", self.ivy_executable, "-dependency",
                                    self.group_id, self.artifact_id, self.version,
                                   "-cachepath", resolved_classpath_file])

        with open(resolved_classpath_file) as f:
            return f.read().replace("\n", "")


class JavaModuleBuildJob(BaseBuildJob):
    """docstring for JavaModuleBuildJob"""

    def parse_dependencies(self, id, property_name, scope_list):
        if property_name in self.data:
            for dependency_id in self.data[property_name]:
                if len(dependency_id.split(":")) == 3:
                    # Ivy dependency
                    job = IvyDependencyJob(id, dependency_id)
                else:
                    job = build_jobs[dependency_id]
                self.dependency_jobs.append(job)
                scope_list.append(job)

    def __init__(self, id, data):
        super(JavaModuleBuildJob, self).__init__(id, data)
        self.classes_cache_directory = os.path.join(self.package_cache, "classes")
        self.test_classes_cache_directory = os.path.join(self.package_cache, "test-classes")
        self.archive_cache = os.path.join(self.package_cache, "dist")
        self.compile_dependencies = []
        self.test_dependencies = []

        self.parse_dependencies(id, "dependencies", self.compile_dependencies)
        self.parse_dependencies(id, "test-dependencies", self.test_dependencies)

        make_dir_if_needed(self.classes_cache_directory)
        make_dir_if_needed(self.test_classes_cache_directory)
        make_dir_if_needed(self.archive_cache)

    def calculate_classpath(self, scope):

        classpath = []
        if scope == "compile" or scope == "run":
            scope_list = self.compile_dependencies
            classpath.append(self.classes_cache_directory)
        elif scope == "test":
            scope_list = self.compile_dependencies + self.test_dependencies
            classpath.append(self.classes_cache_directory)
            classpath.append(self.test_classes_cache_directory)

        for dependency_job in scope_list:
            dependency_classes_cache = dependency_job.classpath_string(scope)
            classpath.append(dependency_classes_cache)
        return classpath

    def classpath_string(self, scope):
        return ':'.join(self.calculate_classpath(scope))

    def classes_cache(self):
        return self.classes_cache_directory

    def compile(self):
        # print "Building Java %s" % self.id
        if not self.needs_rerun("compile"):
            return

        base_build_args = ['javac', '-d', self.classes_cache_directory]
        base_build_args.append('-cp')
        base_build_args.append(self.classpath_string("compile"))

        source_glob = os.path.join(self.package_path, "src", "main", "java", "**", "*.java")
        for source_file in glob2.glob(source_glob):
            command = base_build_args
            command.append(source_file)

            subprocess.check_call(command)

        self.remember_fingerprint("compile")

    def compile_test(self):
        # print "Building Java %s" % self.id
        if not self.needs_rerun("compile_test"):
            return

        base_build_args = ['javac', '-d', self.test_classes_cache_directory]
        base_build_args.append('-cp')
        base_build_args.append(self.classpath_string("test"))

        source_glob = os.path.join(self.package_path, "src", "test", "java", "**", "*.java")
        for source_file in glob2.glob(source_glob):
            command = base_build_args
            command.append(source_file)

            subprocess.check_call(command)

        self.remember_fingerprint("compile_test")

    def test(self):

        if not self.needs_rerun("test"):
            return

        if len(glob2.glob(os.path.join(self.test_classes_cache_directory, "**", "*.class"))) == 0:
            return

        base_run_args = ['java']
        base_run_args.append('-cp')
        base_run_args.append(self.classpath_string("test"))

        command = base_run_args
        command.append("org.testpackage.TestPackage")
        command.append("mytests") # TODO remove hardcoding

        subprocess.check_call(command)

        self.remember_fingerprint("test")

    def run(self):

        if not self.data.has_key('main-class'):
            return

        base_run_args = ['java']
        base_run_args.append('-cp')
        base_run_args.append(self.classpath_string("run"))

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
        for dependency_path in self.classpath_string("run").split(":"):
            for dependency_class in glob2.glob(os.path.join(dependency_path, '**', '*.class')):
                jar_args.append(dependency_class)

        subprocess.check_call(jar_args)

        self.remember_fingerprint("archive")
