# Bacon

*A great knife to take to a build tool gunfight*

Bacon is a simple experimental build tool loosely modelled on the [Pants](http://pantsbuild.github.io/announce_201409.html)
build tool and
[Google's internal build tool](http://google-engtools.blogspot.jp/2011/08/build-in-cloud-how-build-system-works.html). Bacon is, by contrast, incomplete, untested, deliberately naive in its implementation, and not intended for real world use (maybe one day).

## Key points

* Currently Java-only, but would be aimed at building many types of code
* Intended for situations where the codebase for a large system (or system-of-systems) sits in a single folder structure (most likely one SCM repository, though maybe more)
* The presence of a `build.yml` file in any given folder marks it as the root of a 'package'
* YAML is chosen as the package definition format rather than a DSL, and it's intended that the file contains as little information as possible, in the clearest possible form (prefer readability)
* Packages can depend on each other or on external JARs (anything resolvable by Ivy/Maven)
* Bacon will try to avoid doing anything it doesn't need to, e.g. compiling code more than once if it (or dependencies) haven't changed. Currently this is done using SHA256 fingerprinting of each package, but this could probably be sped up for large projects by doing a simpler modification timestamp check beforehand.
* Unit tests are run using TestPackage as a standalone JUnit test runner. Right now the package name for tests is hardcoded.
* Currently the tool and its examples are mixed together, and need to be run with correct pip dependencies available. Ultimately the tool should take the form of:
	* a single bootstrap shell script which would be checked in to source control
	* when run, the bootstrap script would create a suitable isolated python environment somewhere (e.g. $PROJECT/.bacon), download all dependencies, and run

## Usage

Right now, you'll need to have bacon's dependencies loaded. The best way is to create a virtualenv and run pip install inside that:

	cd bacon
	virtualenv .
	. bin/activate					# or bin/activate.fish if you have fish shell
	pip install -r requirements.txt

Then, after that:

	./bacon clean					# deletes cached files
	./bacon compile					# compiles sources
	./bacon test					# compiles and runs unit tests
	./bacon run						# runs the built program
	./bacon archive					# creates an archive (e.g. JAR)

## build.yml syntax examples

A bundle package is, right now, just something to ensure that dependencies get built. Later it could produce a distributable archive:

`./build.yml:`

	type: bundle
	contents:
	 - examples/java-hello
	 - examples/java-foo

A very simple Java package just ensures that files under src/main/java and src/test/java get compiled, and unit tests run:

`./examples/java-foo/build.yml:`

	type: java

A more complex Java package has dependencies (both internal, as a path, and external, as a group:artifact:version string) and produces an output JAR (by presence of the archive property). Also, 'main-class' specifies a class that will be invoked if `./bacon run` is called:

`./examples/java-hello/build.yml:`

	type: java
	dependencies:
	 - examples/java-foo
	 - org.slf4j:slf4j-simple:1.7.7
	test-dependencies:
	 - junit:junit:4.8.1
	 - org.testpackage:testpackage:0.3.0
	main-class: mycode.Hello
	archive:
	  type: jar
	  groupId: org.example
	  artifactId: hello