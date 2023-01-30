#!/bin/bash

# This generates synthetic test files for testing chunking that are designed
# to stress and highlight deduping performance. The oldfile.dat is random data
# that should have no duplication. The newfile.dat is a modified copy of
# oldfile.data with random copy/insert/delete sequences of exponentialy
# distributed length with an average length of 512k. This gives 50%
# duplication where about half should be findable using an average block
# length of 256k.

toolpath=$(dirname $0)
outpath=${1:-.}

oldfile=$outpath/oldfile.dat
newfile=$outpath/newfile.dat

# Generates a 1G original oldfile.dat
echo Generating $oldfile
dd bs=1024K count=1024 if=/dev/urandom >$oldfile

# Generate a modified newfile.dat from oldfile.dat
echo Generating $newfile
$toolpath/modfile.py 512k <$oldfile >$newfile
