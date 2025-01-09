Version=$1
SEMVER=$Version

if [ -z "$2" ]
then
    echo "Bumping package version to $1"

    sed -E "s/current_version = .+/current_version = '$SEMVER'/g" setup.py > tempfile && cat tempfile > setup.py && rm -f tempfile
    sed -E "s/SDK_VERSION = .+/SDK_VERSION = '$SEMVER'/g" skyflow/utils/_version.py > tempfile && cat tempfile > skyflow/utils/_version.py && rm -f tempfile

    echo --------------------------
    echo "Done, Package now at $1"
else
    # Use dev version with commit SHA
    DEV_VERSION="${SEMVER}.dev0+$(echo $2 | tr -dc '0-9a-f')"

    echo "Bumping package version to $DEV_VERSION"

    sed -E "s/current_version = .+/current_version = '$DEV_VERSION'/g" setup.py > tempfile && cat tempfile > setup.py && rm -f tempfile
    sed -E "s/SDK_VERSION = .+/SDK_VERSION = '$DEV_VERSION'/g" skyflow/utils/_version.py > tempfile && cat tempfile > skyflow/utils/_version.py && rm -f tempfile

    echo --------------------------
    echo "Done, Package now at $DEV_VERSION"
fi
