#!/bin/sh -xe

# Note: running this file will require you to enter the PGP card pin. Have it
# memorized or in the clipboard before running this script.
# After the release, run:
#   `twine upload "./dist.$version/*/*"`

DEV_RELEASE_BRANCH="$1"
PORT=4000

GPG_FINGERPRINT="7ED59D88A092EBE00FE2282469DD76556E48CB51"

# Release dev packages to PyPI
version="0.0.0.dev$(date +%Y%m%d)"
tag="v$version"
git tag --delete "$tag" || true

# Check out dev branch in fresh repo clone
root="$(mktemp -d -t starttls-policy-cli.$version.XXX)"
git clone . $root
cd $root
git branch -f "$DEV_RELEASE_BRANCH"
git checkout "$DEV_RELEASE_BRANCH"

# Update version number
sed -i "s/^version.*/version = '$version'/" setup.py

# Sign tagged commit
git add -p
git -c commit.gpgsign=true commit -m "Release $version"
git tag --local-user "$GPG_FINGERPRINT" \
    --sign --message "Release $version" "$tag"

# Build
python setup.py clean
rm -rf build dist
python setup.py sdist
python setup.py bdist_wheel

# GPG-sign wheels
for x in dist/*.tar.gz dist/*.whl
do
  gpg --detach-sign --armor --sign --local-user "$GPG_FINGERPRINT" $x
done

mkdir "dist.$version"
mv $root/dist "dist.$version/starttls-policy-cli"
for pkg_dir in $subpkgs_dirs
do
  mv $pkg_dir/dist "dist.$version/$pkg_dir/"
done

echo "Testing packages"
cd "dist.$version"
# start local PyPI
python -m SimpleHTTPServer $PORT &
# cd .. is NOT done on purpose: we make sure that all subpacakges are
# installed from local PyPI rather than current directory (repo root)
virtualenv --no-site-packages ../venv
. ../venv/bin/activate
# Now, use our local PyPI. --pre allows installation of pre-release (incl. dev)
pip install \
  --pre \
  --extra-index-url http://localhost:$PORT \
  starttls-policy-cli
# stop local PyPI
kill $!

echo "In order to upload packages run the following command:"
echo twine upload "$root/dist.$version/*/*"

