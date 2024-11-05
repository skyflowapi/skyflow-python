Version=$1
SEMVER=$Version

if [ -z $2 ]
then
	echo "Bumping package version to $1"

	sed -E "s/current_version = .+/current_version = \'$SEMVER\'/g" setup.py > tempfile && cat tempfile > setup.py && rm -f tempfile
	sed -E "s/SDK_VERSION = .+/SDK_VERSION = \'$SEMVER\'/g" skyflow/version.py > tempfile && cat tempfile > skyflow/version.py && rm -f tempfile

	echo --------------------------
	echo "Done, Package now at $1"

else
	echo "Bumping package version to $1-dev+$2"

	sed -E "s/current_version = .+/current_version = \'$SEMVER-dev+$2\'/g" setup.py > tempfile && cat tempfile > setup.py && rm -f tempfile
	sed -E "s/SDK_VERSION = .+/SDK_VERSION = \'$SEMVER-dev+$2\'/g" skyflow/version.py > tempfile && cat tempfile > skyflow/version.py && rm -f tempfile

	echo --------------------------
	echo "Done, Package now at $1-dev$2"
fi
