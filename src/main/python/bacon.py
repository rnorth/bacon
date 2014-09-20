#!/usr/bin/env python
import os

import sys
import yaml
from globals import build_jobs, build_order
from bundle_build_job import BundleBuildJob
from java_build_job import JavaModuleBuildJob
from util import make_dir_if_needed


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


def parse_bundle_build_file(id, data):
    for dependency in data['contents']:
        parse_build_file(dependency)
    return BundleBuildJob(id, data)


def parse_java_build_file(id, data):
    if data.has_key('dependencies'):
        for dependency in data['dependencies']:
            if len(dependency.split(":")) != 3:
                parse_build_file(dependency)
    return JavaModuleBuildJob(id, data)

root_path = sys.argv[1]

if len(sys.argv) > 2:
    task = sys.argv[2]
else:
    task = "build"

make_dir_if_needed(os.path.expanduser("~/.bacon.d"))
parse_build_file(root_path)

# print "build order:"
# print yaml.dump(build_order)

# print "task: %s" % task

if task == "compile":
    goals = ["compile"]
elif task == "clean":
    goals = ["clean"]
elif task == "run":
    goals = ["compile", "run"]
elif task == "archive":
    goals = ["compile", "archive"]
else:
    sys.exit("No recognized goal name was specified")

for goal in goals:
    for job_key in build_order:

        print "%30s :%s" % (job_key, goal)

        job = build_jobs[job_key]
        if goal == "compile":
            job.compile()
        elif goal == "clean":
            job.clean()
        elif goal == "run":
            job.run()
        elif goal == "archive":
            job.archive()