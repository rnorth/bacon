# Bacon

*A great knife to take to a build tool gunfight*

Bacon is a simple experimental build tool loosely modelled on the [Pants](http://pantsbuild.github.io/announce_201409.html)
build tool and
[Google's internal build tool](http://google-engtools.blogspot.jp/2011/08/build-in-cloud-how-build-system-works.html). Bacon is, by contrast, incomplete, untested, deliberately naive in its implementation, and not intended for real world use (maybe one day).

## Usage

	./bacon clean					# deletes cached files
	./bacon compile				# compiles sources
	./bacon test						# compiles and runs unit tests
	./bacon run						# runs the built program
	./bacon archive					# creates an archive (e.g. JAR)

