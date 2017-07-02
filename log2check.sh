#!/bin/sh

###
 # Copyright (c) 2016, 2017 d-r-p (Lib4RI) <d-r-p@users.noreply.github.com>
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

SED="/bin/sed"
CAT="/bin/cat"
SORT="/usr/bin/sort"
THIS="`echo $0 | $SED 's/.*\/\([^\/]*\)/\1/'`"

### define help strings

USAGE="$THIS [-o OUTDIR] LOGFILE"
usage() {
  echo "$USAGE" >&2
  exit 1
}

HELP="\t-o OUTDIR\tSpecify output directory OUTDIR"

### parse command line options

OUTDIR="."
while getopts "o:" O
do
  case "$O" in
    o) # specify the output directory
      OUTDIR="$OPTARG"
      ;;
    \?) # unknown option, so show the usage and exit
      usage
      ;;
  esac
done

shift $(($OPTIND - 1))

if [ $# -ne 1 ]
then
  usage
fi

LOGFILE="$1"

if [ ! -f "$LOGFILE" ] || [ ! -r "$LOGFILE" ]
then
  echo "Error: Non-existent or unreadable file \"$LOGFILE\"" >&2
fi

LOGFILENAME="`echo "$LOGFILE" | $SED '/\// s/^.*\/\(.\+\)$/\1/'`"

OUTDIR="`echo "$OUTDIR" | $SED '/^\/$/! s/\/$//'`" # remove trailing slash if not root-dir

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

### define string constants and file suffixes

check="check"

names="/^.MATCH/! d; s/\([^,]*\), \?\(.\)[^=]* = WSL(\\\1 \\\2[^)]*)/OK/; /OK/d; s/\(.\)MATCH:\(.*\) in publication no.\([0-9]\+\)\(.*\)/\\\3:\\\1:\\\2\\\4/; p;"
s_names="$SORT -s -k 2,2"
f_names="$check""names"

missing="/missing/! d; p;"
s_missing="$CAT"
f_missing="$check""missing"
ambiguous="/ambiguous/! d; s/Warning: \(.*\) in publication no.\([0-9]\+\)\(.*\)/\\\2: \\\1\\\3/; s/\([^,]*\), \(.*\)detected:\(.*\)/\\\1,\\\2in:\\\3/; s/Possible //; s/author //; p;"
s_ambiguous="$SORT -s -u -k 3r,3 -k 4,4 -k 1n"
f_ambiguous="$check""ambiguous"
position="/too large/! {/corruption/! d;}; s/Warning: \(.*\) in publication no.\([0-9]\+\)\(.*\)/\\\2: \\\1\\\3/; p;"
s_position="$CAT"
f_position="$check""pos"
initials="/initial/! d; s/Notice: \(.*\) in publication no.\([0-9]\+\)\(.*\)/\\\2: \\\1\\\3/; s/ using lesser matching//; s/position /pos./; s/first/1st/; p;"
s_initials="$SORT -s -k 4,4 -k 1n"
f_initials="$check""initials"

rematch="/Rematch/! d; p;"
s_rematch="$CAT"
f_rematch="$check""rematch"
sap="/Mismatching/! d; p;"
s_sap="$CAT"
f_sap="$check""sap"

noauthors="/No (co-)author\/editor/! d; s/Warning: \(.*\) in publication no.\([0-9]\+\)\(.*\)/\\\2: \\\1\\\3/; s/ author-field was//; s/ .*:/ No matches in:/; p;"
s_noauthors="$SORT -s -k 5,5 -k 1n"
f_noauthors="$check""noauthors"
incomplete="/incomplete/! d; p;"
s_incomplete="$CAT"
f_incomplete="$check""incomplete"

issn="/invalid/! d; s/Warning: \(.*\) in publication no.\([0-9]\+\)\(.*\)/\\\2: \\\1\\\3/; s/; ignoring//; p;"
s_issn="$CAT"
f_issn="$check""issn"

### parse log file

for n in names missing ambiguous position initials rematch sap noauthors incomplete issn
do
  vstr="$""$n"
  sstr="$""s_""$n"
  fstr="$""f_""$n"
  v="`eval echo "$vstr"`"
  s="`eval echo "$sstr"`"
  f="`eval echo "$fstr"`"
$CAT "$LOGFILE" | $SED -n "$v" | $s | $SED ':a s/^\(.\{0,4\}:\)/ \1/; ta;' > "$OUTDIR""/""$LOGFILENAME"".$f" || echo "FAILED: $n"
done

exit 0
