#!/bin/sh


###
 # Copyright (c) 2017 d-r-p (Lib4RI) <d-r-p@users.noreply.github.com>
 #
 # Permission to use, copy, modify, and distribute this software for any
 # purpose with or without fee is hereby granted, provided that the above
 # copyright notice and this permission notice appear in all copies.
 #
 # THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 # WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 # MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 # ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 # WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 # ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 # OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
###

### define programs

LS="/bin/ls"
SED="/bin/sed"
CAT="/bin/cat"
SORT="/usr/bin/sort"
UNIQ="/usr/bin/uniq"
THIS="`echo $0 | $SED 's/.*\/\([^\/]*\)/\1/'`"

### define constants

QUIET=1

### define help strings

USAGE="$THIS [-v] [-f FILENAME] [-i INDIR] [-o OUTDIR]"
usage() {
  echo "$USAGE" >&2
  exit 1
}

HELP="\t-f FILENAME\tSpecify output file name FILENAME
\t\t\t(sets exclusion pattern!)
\t\t\t --- NOT YET IMPLEMENTED!
\t-i INDIR\tSpecify input directory INDIR
\t-o OUTDIR\tSpecify output directory OUTDIR
\t-v\t\tBe verbose"

### parse command line options

FILENAME="all.log.checkall"
INDIR="."
OUTDIR="."
while getopts "hi:o:v" O
do
  case "$O" in
    h) # help
      echo "$USAGE"
      echo "$HELP"
      exit 0
      ;;
    i) # specify the input directory
      INDIR="$OPTARG"
      ;;
    o) # specify the output directory
      OUTDIR="$OPTARG"
      ;;
    v) # be verbose
      QUIET=0
      ;;
    \?) # unknown option, so show the usage and exit
      usage
      ;;
  esac
done

shift $(($OPTIND - 1))

if [ $# -ne 0 ]
then
  usage
fi

INDIR="`echo "$INDIR" | sed '/^\/$/! s/\/$//'`" # remove trailing slash if not root-dir
OUTDIR="`echo "$OUTDIR" | sed '/^\/$/! s/\/$//'`" # remove trailing slash if not root-dir

if [ ! -d "$INDIR" ] || [ ! -r "$INDIR" ]
then
  echo "Error: Non-existent or unreadable directory \"$INDIR\"" >&2
  exit 1
fi

if [ ! -e "$OUTDIR" ]
then
  mkdir -p "$OUTDIR"
  if [ $? -ne 0 ]
  then
    echo "Error: Could not create directory \"$OUTDIR\"" >&2
    exit 1
  fi
fi

if [ ! -d "$OUTDIR" ] || [ ! -w "$OUTDIR" ]
then
  echo "Error: Non-existent or unwritable directory \"$OUTDIR\"" >&2
  exit 1
fi

### define patterns

LOGCHECKPARTICLE=".log.check"
LOGCHECKPARTICLE_ESCAPED="`echo "$LOGCHECKPARTICLE" | $SED 's/\./\\\\./g;'`"

EXCLUSIONREGEX=".*`echo "$FILENAME" | $SED 's/\./\\\\./g;'`.*"

### get all suffixes

SUFFIXES="`ls $INDIR/*$LOGCHECKPARTICLE* | $SED "/$EXCLUSIONREGEX/ d;" | $SED "s/.*$LOGCHECKPARTICLE_ESCAPED//" | $SORT | $UNIQ`"

### clear combined log file

echo -n "" > "$OUTDIR/$FILENAME"

### combine all log files

for s in $SUFFIXES
do
  echo "
        -------- $s --------
" >> "$OUTDIR/$FILENAME"
  for f in `ls $INDIR/*$LOGCHECKPARTICLE$s`
  do
    echo "$f" | $SED 's/.*\//    ******** /' >> "$OUTDIR/$FILENAME"
    $CAT "$f" >> "$OUTDIR/$FILENAME"
  done
done

exit 0
