#! /bin/bash

txtdir=$1
plotdir=$2
txtref="txt-reference"
plotref="plots-reference"

cd ..
python3 plotter_bylumi.py \
    --input $PWD/test/BSFit_Fill11740_BX72.txt \
    --streams 20 \
    --output $PWD/test/plots/
cd $OLDPWD

if [ $1 = "--help" ] || [ $1 = "-h" ]; then
    printf "Usage: check.sh <txtdir> <plotdir>\n"
    exit 0
fi

if [ $# -ne 2 ]; then
    printf "[\033[0;31mError\033[0m] Invalid number of arguments\n"
    printf "Usage: check.sh <txtdir> <plotdir>\n"
    exit 1
fi

if [ ! -d $txtref ]; then
    printf "[\033[0;31mError\033[0m] $txtref is not a directory\n"
    exit 1
fi

if [ ! -d $plotref ]; then
    printf "[\033[0;31mError\033[0m] $plotref is not a directory\n"
    exit 1
fi

if [ ! -d $txtdir ]; then
    printf "[\033[0;31mError\033[0m] $txtdir is not a directory\n"
    exit 1
fi

if [ ! -d $plotdir ]; then
    printf "[\033[0;31mError\033[0m] $plotdir is not a directory\n"
    exit 1
fi

for file in $txtref/*; do
    filename=$(basename $file)
    if [ ! -f $txtdir/$filename ]; then
        printf "[\033[0;31mError\033[0m] $txtdir/$filename does not exist\n"
        exit 1
    fi
    diff -q $file $txtdir/$filename > /dev/null
    if [ $? -ne 0 ]; then
        printf "[\033[0;31mError\033[0m] $txtdir/$filename is different from $file\n"
        exit 1
    fi
done
printf '[\033[0;32m Success \033[0m]: All text files in %s match the reference files in %s\n' "$txtdir" "$txtref"

for pdf in $plotref/*.pdf $plotref/**/*.pdf; do
    filename=$(basename $pdf)
    if [ ! -f $plotdir/$filename ]; then
        printf '[\033[0;31mError\033[0m] %s/%s does not exist\033[0m\n' "$plotdir" "$filename"
        exit 1
    fi
    pdftoppm -r 150 -singlefile -png $pdf /tmp/ref.pdf
    pdftoppm -r 150 -singlefile -png $plotdir/$filename /tmp/test.pdf
    cmp -s /tmp/ref.pdf.png /tmp/test.pdf.png
    if [ $? -ne 0 ]; then
        printf '[\033[0;33m Warning \033[0m]: %s is different from %s\n' "$plotdir/$filename" "$pdf"
    else
        printf '[\033[0;32m Success \033[0m]: %s matches the reference file %s\n' "$plotdir/$filename" "$pdf"
    fi
done
