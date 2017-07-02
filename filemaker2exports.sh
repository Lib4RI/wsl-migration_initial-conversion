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

LS="/bin/ls"
SED="/bin/sed"
CAT="/bin/cat"
HEAD="/usr/bin/head"
SORT="/usr/bin/sort"
PYTHON="/usr/bin/python"
THIS="`echo $0 | $SED 's/.*\/\([^\/]*\)/\1/'`"

### define constants

DONOTCHAIN=1
SKIPEXISTING=1
EXCLUDESAP=1
EXCLUDEPERSNO=1
QUIET=1
DONOTREEXPORT=1
DOEXPORT=1

### define help strings

USAGE="$THIS [-c] [-f] [-h] [-i|-I] [-v] [-x|-X] [-o OUTDIR]"
usage() {
  echo "$USAGE" >&2
  exit 1
}

HELP="\t-c\t Chain the publication exports
\t-f\t Force the re-generation of all files
\t-h\t Show this message
\t-i\t Include the SAP-numbers of the matched (co-)authors/editors, when available
\t-I\t Include the \"Personal\"-numbers of the matched (co-)authors/editors, when available
\t-v\t Be verbose
\t-x\t Re-export the publications according to the filters, despite existing files
\t-X\t Do not export the publications according to the filters (just parse)
\t-o OUTDIR\tSpecify output directory OUTDIR"

### parse command line options

OUTDIR="."
while getopts "cfhiIvxXo:" O
do
  case "$O" in
    c) # chain the publication exports
      DONOTCHAIN=0
      ;;
    f) # force re-parsing and re-exporting
      SKIPEXISTING=0
      ;;
    h) # help
      echo "$USAGE"
      echo "$HELP"
      exit 0
      ;;
    i) # include the sap-numbers of the matched (co-)authors/editors, if available
      EXCLUDESAP=0
      ;;
    I) # include the "personal"-numbers of the matched (co-)authors/editors, if available
      EXCLUDEPERSNO=0
      ;;
    v) # be verbose
      QUIET=0
      ;;
    x) # always re-export, but do not necessarily re-parse
      DONOTREEXPORT=0
      ;;
    X) # never export, but parse if necessary
      DOEXPORT=0
      ;;
    o) # specify the output directory
      OUTDIR="$OPTARG"
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

if [ $EXCLUDESAP -eq 0 ] && [ $EXCLUDEPERSNO -eq 0 ]
then
  echo "Error: You cannot specify both -i and -I" >&2
  exit 1
fi

if [ $DONOTREEXPORT -eq 0 ] && [ $DOEXPORT -eq 0 ]
then
  echo "Error: You cannot specify both -x and -X" >&2
  exit 1
fi

OUTDIR="`echo "$OUTDIR" | sed '/^\/$/! s/\/$//'`" # remove trailing slash if not root-dir

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

### define helper applications

PARSER="filemakerparsexml.py"
MERGER="mergewithpers.py"
FLATTENER="flattenpersons.py"
EXPORTER="filemaker2refworks.py"
LISTCHECKER="listoverlap.py"
LOG2CHECK="./log2check.sh"

### define directories and file-prefixes

DIR="DATA"
AUTHORFILEPREFIX="Autoren"
COAUTHORFILEPREFIX="Coautoren"
EDITORFILEPREFIX="Editoren"
PERSAUTHORFILEPREFIX="PersAutor"
PERSCOAUTHORFILEPREFIX="PersCoautor"
PERSEDITORFILEPREFIX="PersEditor"
JOURNALFILEPREFIX="Journals"
PUBLICATIONFILEPREFIX="PublikationenWSL"

FILTERREGEX="F[0-9][0-9]*" # use a regexp to hand over to 'ls' - filters will then be called in alphabetical order (we 'sort' them)

if [ "${FILTERREGEX%.xml}" = "$FILTERREGEX" ] # make sure the filter ends with ".xml"
then
  FILTERREGEX="$FILTERREGEX"".xml"
fi

### helper function to select latest data

getfile() {
  echo "`$LS -t "$DIR/$1"*.xml | $SED '/_parsed/d;' | $SED '/_merged/d;' | $SED '/_links/d;' | $SED -n '1 p;' | $SED 's/.xml$//'`"
}

### get filenames of data files

AUTHORFILE="`getfile \"$AUTHORFILEPREFIX\"`"
COAUTHORFILE="`getfile \"$COAUTHORFILEPREFIX\"`"
EDITORFILE="`getfile \"$EDITORFILEPREFIX\"`"
PERSAUTHORFILE="`getfile \"$PERSAUTHORFILEPREFIX\"`"
PERSCOAUTHORFILE="`getfile \"$PERSCOAUTHORFILEPREFIX\"`"
PERSEDITORFILE="`getfile \"$PERSEDITORFILEPREFIX\"`"
JOURNALFILE="`getfile \"$JOURNALFILEPREFIX\"`"
PUBLICATIONFILE="`getfile \"$PUBLICATIONFILEPREFIX\"`"

### parse data if necessary

NOCONVERT=0

if [ $QUIET -eq 0 ]
then
  if [ $SKIPEXISTING -ne 0 ] && [ -f "$AUTHORFILE""_parsed.xml" ] && [ -f "$COAUTHORFILE""_parsed.xml" ] && [ -f "$EDITORFILE""_parsed.xml" ] && [ -f "$PERSAUTHORFILE""_parsed.xml" ] && [ -f "$PERSCOAUTHORFILE""_parsed.xml" ] && [ -f "$PERSEDITORFILE""_parsed.xml" ] && [ -f "$JOURNALFILE""_parsed.xml" ] && [ -f "$PUBLICATIONFILE""_parsed.xml" ]
  then
    echo "No files need to be converted (use '-f' to re-generate all)" >&2
    NOCONVERT=1
  else
    echo "Files that will be converted are:" >&2
  fi
  if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$AUTHORFILE""_parsed.xml" ]
  then
    echo "  $AUTHORFILE.xml" >&2
  fi
  if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$COAUTHORFILE""_parsed.xml" ]
  then
    echo "  $COAUTHORFILE.xml" >&2
  fi
  if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$EDITORFILE""_parsed.xml" ]
  then
    echo "  $EDITORFILE.xml" >&2
  fi
  if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$PERSAUTHORFILE""_parsed.xml" ]
  then
    echo "  $PERSAUTHORFILE.xml" >&2
  fi
  if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$PERSCOAUTHORFILE""_parsed.xml" ]
  then
    echo "  $PERSCOAUTHORFILE.xml" >&2
  fi
  if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$PERSEDITORFILE""_parsed.xml" ]
  then
    echo "  $PERSEDITORFILE.xml" >&2
  fi
  if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$JOURNALFILE""_parsed.xml" ]
  then
    echo "  $JOURNALFILE.xml" >&2
  fi
  if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$PUBLICATIONFILE""_parsed.xml" ]
  then
    echo "  $PUBLICATIONFILE.xml" >&2
  fi
fi

if [ $QUIET -eq 0 ] && [ $NOCONVERT -eq 0 ]
then
  echo "Converting files..." >&2
fi

HAVEPARSEERROR=0
parsexml() {
  MYHAVEPARSEERROR=0
  if [ $QUIET -eq 0 ]
  then
    echo "  Parsing $1.xml..." >&2
  fi
  PYTHONIOENCODING=utf8 "$PYTHON" "$PARSER" -v "$1.xml" > "$1_parsed.xml" 2> "$1_parsed.log" # need to feed the source file as an argument, not via stdin, so we can record the mtime
  if [ $? -ne 0 ]
  then
    MYHAVEPARSEERROR=1
    if [ $QUIET -eq 0 ]
    then
      echo "  ...failed (see the log-file $1_parsed.log)." >&2
    fi
  elif [ $QUIET -eq 0 ]
  then
    echo "  ...done." >&2
  fi
  return $MYHAVEPARSEERROR
}

if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$AUTHORFILE""_parsed.xml" ]
then
  if [ -f "$AUTHORFILE""_merged.xml" ]
  then
    rm "$AUTHORFILE""_merged.xml"
  fi
  DONOTREEXPORT=0
  parsexml "$AUTHORFILE"
  if [ $? -ne 0 ]
  then
    HAVEPARSEERROR=1
    rm "$AUTHORFILE""_parsed.xml"
  fi
fi
if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$COAUTHORFILE""_parsed.xml" ]
then
  if [ -f "$COAUTHORFILE""_merged.xml" ]
  then
    rm "$COAUTHORFILE""_merged.xml"
  fi
  DONOTREEXPORT=0
  parsexml "$COAUTHORFILE"
  if [ $? -ne 0 ]
  then
    HAVEPARSEERROR=1
    rm "$COAUTHORFILE""_parsed.xml"
  fi
fi
if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$EDITORFILE""_parsed.xml" ]
then
  if [ -f "$EDITORFILE""_merged.xml" ]
  then
    rm "$EDITORFILE""_merged.xml"
  fi
  DONOTREEXPORT=0
  parsexml "$EDITORFILE"
  if [ $? -ne 0 ]
  then
    HAVEPARSEERROR=1
    rm "$EDITORFILE""_parsed.xml"
  fi
fi
if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$PERSAUTHORFILE""_parsed.xml" ]
then
  if [ -f "$PERSAUTHORFILE""_merged.xml" ]
  then
    rm "$PERSAUTHORFILE""_merged.xml"
  fi
  DONOTREEXPORT=0
  parsexml "$PERSAUTHORFILE"
  if [ $? -ne 0 ]
  then
    HAVEPARSEERROR=1
    rm "$PERSAUTHORFILE""_parsed.xml"
  fi
fi
if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$PERSCOAUTHORFILE""_parsed.xml" ]
then
  if [ -f "$PERSCOAUTHORFILE""_merged.xml" ]
  then
    rm "$PERSCOAUTHORFILE""_merged.xml"
  fi
  DONOTREEXPORT=0
  parsexml "$PERSCOAUTHORFILE"
  if [ $? -ne 0 ]
  then
    HAVEPARSEERROR=1
    rm "$PERSCOAUTHORFILE""_parsed.xml"
  fi
fi
if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$PERSEDITORFILE""_parsed.xml" ]
then
  if [ -f "$PERSEDITORFILE""_merged.xml" ]
  then
    rm "$PERSEDITORFILE""_merged.xml"
  fi
  DONOTREEXPORT=0
  parsexml "$PERSEDITORFILE"
  if [ $? -ne 0 ]
  then
    HAVEPARSEERROR=1
    rm "$PERSEDITORFILE""_parsed.xml"
  fi
fi
if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$JOURNALFILE""_parsed.xml" ]
then
  DONOTREEXPORT=0
  parsexml "$JOURNALFILE"
  if [ $? -ne 0 ]
  then
    HAVEPARSEERROR=1
    rm "$JOURNALFILE""_parsed.xml"
  fi
fi
if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$PUBLICATIONFILE""_parsed.xml" ]
then
  DONOTREEXPORT=0
  parsexml "$PUBLICATIONFILE"
  if [ $? -ne 0 ]
  then
    HAVEPARSEERROR=1
    rm "$PUBLICATIONFILE""_parsed.xml"
  fi
fi

if [ $QUIET -eq 0 ] && [ $NOCONVERT -eq 0 ]
then
  echo "...done." >&2
fi

if [ $HAVEPARSEERROR -ne 0 ]
then
  echo "Error: Parsing did not succeed! Exiting..." >&2
  exit 1
fi

### merge person data if necessary

NOMERGE=0

if [ $QUIET -eq 0 ]
then
  if [ $SKIPEXISTING -ne 0 ] && [ -f "$AUTHORFILE""_merged.xml" ] && [ -f "$COAUTHORFILE""_merged.xml" ] && [ -f "$EDITORFILE""_merged.xml" ]
  then
    echo "No files need to be merged (use '-f' to re-generate all)" >&2
    NOMERGE=1
  else
    echo "Files that will be merged are:" >&2
  fi
  if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$AUTHORFILE""_merged.xml" ]
  then
    echo "  $AUTHORFILE""_parsed.xml and $PERSAUTHORFILE""_parsed.xml" >&2
  fi
  if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$COAUTHORFILE""_merged.xml" ]
  then
    echo "  $COAUTHORFILE""_parsed.xml and $PERSCOAUTHORFILE""_parsed.xml" >&2
  fi
  if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$EDITORFILE""_merged.xml" ]
  then
    echo "  $EDITORFILE""_parsed.xml and $PERSEDITORFILE""_parsed.xml" >&2
  fi
fi

if [ $QUIET -eq 0 ] && [ $NOMERGE -eq 0 ]
then
  echo "Merging files..." >&2
fi

HAVEMERGEERROR=0
mergexml() {
  MYHAVEMERGEERROR=0
  if [ $QUIET -eq 0 ]
  then
    echo "  Merging $1_parsed.xml with $2_parsed.xml..." >&2
  fi
  PYTHONIOENCODING=utf8 "$PYTHON" "$MERGER" -v -p "$2_parsed.xml" < "$1_parsed.xml" > "$1_merged.xml" 2> "$1_merged.log"
  if [ $? -ne 0 ]
  then
    MYHAVEMERGEERROR=1
    if [ $QUIET -eq 0 ]
    then
      echo "  ...failed (see the log-file $1_merged.log)." >&2
    fi
  elif [ $QUIET -eq 0 ]
  then
    echo "  ...done." >&2
  fi
  return $MYHAVEMERGEERROR
}

if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$AUTHORFILE""_merged.xml" ]
then
  if [ -f "$AUTHORFILE""_links.xml" ]
  then
    rm "$AUTHORFILE""_links.xml"
  fi
  mergexml "$AUTHORFILE" "$PERSAUTHORFILE"
  if [ $? -ne 0 ]
  then
    HAVEMERGEERROR=1
    rm "$AUTHORFILE""_merged.xml"
  fi
fi
if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$COAUTHORFILE""_merged.xml" ]
then
  if [ -f "$COAUTHORFILE""_links.xml" ]
  then
    rm "$COAUTHORFILE""_links.xml"
  fi
  mergexml "$COAUTHORFILE" "$PERSCOAUTHORFILE"
  if [ $? -ne 0 ]
  then
    HAVEMERGEERROR=1
    rm "$COAUTHORFILE""_merged.xml"
  fi
fi
if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$EDITORFILE""_merged.xml" ]
then
  if [ -f "$EDITORFILE""_links.xml" ]
  then
    rm "$EDITORFILE""_links.xml"
  fi
  mergexml "$EDITORFILE" "$PERSEDITORFILE"
  if [ $? -ne 0 ]
  then
    HAVEMERGEERROR=1
    rm "$EDITORFILE""_merged.xml"
  fi
fi

if [ $QUIET -eq 0 ] && [ $NOMERGE -eq 0 ]
then
  echo "...done." >&2
fi

if [ $HAVEMERGEERROR -ne 0 ]
then
  echo "Error: Merging did not succeed! Exiting..." >&2
  exit 1
fi

### flatten person data

NOFLATTEN=0

if [ $QUIET -eq 0 ]
then
  if [ $SKIPEXISTING -ne 0 ] && [ -f "$AUTHORFILE""_links.xml" ] && [ -f "$COAUTHORFILE""_links.xml" ] && [ -f "$EDITORFILE""_links.xml" ]
  then
    echo "No files need to be flattened (use '-f' to re-generate all)" >&2
    NOFLATTEN=1
  else
    echo "Files that will be flattened are:" >&2
  fi
  if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$AUTHORFILE""_links.xml" ]
  then
    echo "  $AUTHORFILE""_merged.xml" >&2
  fi
  if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$COAUTHORFILE""_links.xml" ]
  then
    echo "  $COAUTHORFILE""_merged.xml" >&2
  fi
  if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$EDITORFILE""_links.xml" ]
  then
    echo "  $EDITORFILE""_merged.xml" >&2
  fi
fi

if [ $QUIET -eq 0 ] && [ $NOFLATTEN -eq 0 ]
then
  echo "Flattening files..." >&2
fi

HAVEFLATTENERROR=0
flattenxml() {
  MYHAVEFLATTENERROR=0
  if [ $QUIET -eq 0 ]
  then
    echo "  Flattening $1_merged.xml..." >&2
  fi
  PYTHONIOENCODING=utf8 "$PYTHON" "$FLATTENER" -v < "$1_merged.xml" > "$1_links.xml" 2> "$1_links.log"
  if [ $? -ne 0 ]
  then
    MYHAVEFLATTENERROR=1
    if [ $QUIET -eq 0 ]
    then
      echo "  ...failed (see the log-file $1_links.log)." >&2
    fi
  elif [ $QUIET -eq 0 ]
  then
    echo "  ...done." >&2
  fi
  return $MYHAVEFLATTENERROR
}

if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$AUTHORFILE""_links.xml" ]
then
  flattenxml "$AUTHORFILE"
  if [ $? -ne 0 ]
  then
    HAVEFLATTENERROR=1
    rm "$AUTHORFILE""_links.xml"
  fi
fi
if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$COAUTHORFILE""_links.xml" ]
then
  flattenxml "$COAUTHORFILE"
  if [ $? -ne 0 ]
  then
    HAVEFLATTENERROR=1
    rm "$COAUTHORFILE""_links.xml"
  fi
fi
if [ $SKIPEXISTING -eq 0 ] || [ ! -f "$EDITORFILE""_links.xml" ]
then
  flattenxml "$EDITORFILE"
  if [ $? -ne 0 ]
  then
    HAVEFLATTENERROR=1
    rm "$EDITORFILE""_links.xml"
  fi
fi

if [ $QUIET -eq 0 ] && [ $NOFLATTEN -eq 0 ]
then
  echo "...done." >&2
fi

if [ $HAVEFLATTENERROR -ne 0 ]
then
  echo "Error: Flattening did not succeed! Exiting..." >&2
  exit 1
fi

### export publications

if [ $DOEXPORT -eq 0 ]
then
  if [ $QUIET -eq 0 ]
  then
    echo "Not exporting anything because of '-X'. Exiting..." >&2
  fi
  exit 0
fi

NOEXPORT=0

FILTERS=`$LS $FILTERREGEX | $SORT | $SED '/.xml$/! d;' | $SED '/_remainder/d;' | $SED '/_out-selected/d;' | $SED 's/.xml$//'`

if [ "$FILTERS" = "" ]
then
  echo "Error: No filters found!" >& 2
  exit 1
fi

PUBLICATIONSMTIME=`$HEAD -2 "$PUBLICATIONFILE""_parsed.xml" | $SED -n '2 {s/.*MTIME="\([0-9]\{8\}T[0-9]\{6\}Z\)".*/\1/; p;}'`

ALLFILTERSDONE=1
ANYFILTERDONE=0
PREVCHANGED=0
OLDIFS=$IFS
IFS='
'
for f in ${FILTERS%""}
do
  FILTERNUMBER=$(($FILTERNUMBER+1))
  if [ -f "$OUTDIR/$f""_$PUBLICATIONSMTIME""_out-csv.txt" ] && [ -f "$OUTDIR/$f""_$PUBLICATIONSMTIME""_out-tagged.txt" ] && ( [ $DONOTCHAIN -ne 0 ] || ( [ -f "$OUTDIR/$f""_remainder.xml" ] && [ $PREVCHANGED -eq 0 ] ) )
  then
    ANYFILTERDONE=1
  else
    ALLFILTERSDONE=0
    if [ $DONOTCHAIN -eq 0 ]
    then
      PREVCHANGED=1
    fi
  fi
done
IFS=$OLDIFS

if [ $QUIET -eq 0 ]
then
  if [ $SKIPEXISTING -ne 0 ] && [ $DONOTREEXPORT -ne 0 ] && [ $ALLFILTERSDONE -ne 0 ]
  then
    echo "No publications need to be exported (use '-x' to process all filters or '-f' to re-generate everything)" >&2
    NOEXPORT=1
  else
    echo "Filters that will be processed are:" >&2
  fi
  PREVCHANGED=0
  OLDIFS=$IFS
  IFS='
'
  for f in ${FILTERS%""}
  do
    if [ $SKIPEXISTING -eq 0 ] || [ $DONOTREEXPORT -eq 0 ] || [ ! -f "$OUTDIR/$f""_$PUBLICATIONSMTIME""_out-csv.txt" ] || [ ! -f "$OUTDIR/$f""_$PUBLICATIONSMTIME""_out-tagged.txt" ] || ( [ $DONOTCHAIN -eq 0 ] && ( [ ! -f "$OUTDIR/$f""_remainder.xml" ] || [ $PREVCHANGED -ne 0 ] ) )
    then
      echo "  $f"".xml" >&2
      if [ $DONOTCHAIN -eq 0 ]
      then
        PREVCHANGED=1
      fi
    fi
  done
  IFS=$OLDIFS
fi

if [ $QUIET -eq 0 ] && [ $NOEXPORT -eq 0 ]
then
  echo "Exporting publications..." >&2
fi

HAVEEXPORTERROR=0
export2refworks() {
  MYHAVEEXPORTERROR=0
  SETUPFILE="`echo "$1" | $SED 's/.xml$//'`"
  REMAINDERFILE="$OUTDIR/$SETUPFILE""_remainder.xml"
  PUBFILE="$2"
  if [ $QUIET -eq 0 ]
  then
    echo "  Exporting publications from $PUBFILE according to $SETUPFILE"".xml, saving the remainder in $REMAINDERFILE..." >&2
  fi
  OPT_I=""
  if [ $EXCLUDESAP -eq 0 ]
  then
    OPT_I="-i"
  elif [ $EXCLUDEPERSNO -eq 0 ]
  then
    OPT_I="-I"
  fi
  PYTHONIOENCODING=utf8 "$PYTHON" "$EXPORTER" -v $OPT_I -t -s "$SETUPFILE"".xml" -d "$OUTDIR" -a "$AUTHORFILE""_links.xml" -c "$COAUTHORFILE""_links.xml" -e "$EDITORFILE""_links.xml" -j "$JOURNALFILE""_parsed.xml" < "$PUBFILE" > "$REMAINDERFILE" 2> "$OUTDIR/$SETUPFILE"".log"
  if [ $? -ne 0 ]
  then
    MYHAVEEXPORTERROR=1
    if [ $QUIET -eq 0 ]
    then
      echo "  ...failed (see the log-file $SETUPFILE"".log)." >&2
    fi
  elif [ $QUIET -eq 0 ]
  then
    echo "  ...done." >&2
  fi
  echo "$REMAINDERFILE"
  return $MYHAVEEXPORTERROR
}

INITIALPUBFILE="$PUBLICATIONFILE""_parsed.xml"
NEXTPUBFILE="$INITIALPUBFILE"
PREVCHANGED=0
OLDIFS=$IFS
IFS='
'
for f in ${FILTERS%""}
do
  if [ $SKIPEXISTING -ne 0 ] && [ $DONOTREEXPORT -ne 0 ] && [ -f "$OUTDIR/$f""_$PUBLICATIONSMTIME""_out-csv.txt" ] && [ -f "$OUTDIR/$f""_$PUBLICATIONSMTIME""_out-tagged.txt" ] && ( [ $DONOTCHAIN -ne 0 ] || ( [ -f "$OUTDIR/$f""_remainder.xml" ] && [ $PREVCHANGED -eq 0 ] ) )
  then
    NEXTPUBFILE="$OUTDIR/$f""_remainder.xml"
    continue
  elif [ $DONOTCHAIN -eq 0 ]
  then
    PREVCHANGED=1
  fi
  if [ $DONOTCHAIN -ne 0 ]
  then
    NEXTPUBFILE="$INITIALPUBFILE"
  fi
  NEXTPUBFILE="`export2refworks "$f"".xml" "$NEXTPUBFILE"`"
  if [ $? -ne 0 ]
  then
    HAVEEXPORTERROR=1
    if [ $DONOTCHAIN -eq 0 ] && [ "$NEXTPUBFILE" != "$INITIALPUBFILE" ]
    then
      rm "$NEXTPUBFILE" # this should ensure that the filter gets re-done on error
    fi
  else
    if [ $QUIET -eq 0 ]
    then
      echo "  Analysing $f"".log..." >&2
    fi
    $LOG2CHECK -o "$OUTDIR" "$OUTDIR/$f"".log"
    if [ $? -ne 0 ] && [ $QUIET -eq 0 ]
    then
      echo "  ...failed." >&2
    else
      echo "  ...done." >&2
    fi
  fi
  if [ $HAVEEXPORTERROR -ne 0 ] && [ $DONOTCHAIN -eq 0 ]
  then
    echo "Error: Last export did not succeed; cannot continue chaining..." >& 2
    exit 1
  fi
done
IFS=$OLDIFS

if [ $QUIET -eq 0 ] && [ $NOEXPORT -eq 0 ]
then
  echo "...done." >&2
fi

if [ $HAVEEXPORTERROR -ne 0 ]
then
  echo "Error: Exporting did not succeed! Exiting..." >&2
  exit 1
fi

NOEXPORT=0 # to force checking
if [ $DONOTCHAIN -ne 0 ] && [ $NOEXPORT -eq 0 ] && [ $FILTERNUMBER -ge 2 ]
then
  if [ $QUIET -eq 0 ]
  then
    echo "Checking exports for non-exclusive filters..." >& 2
  fi

  OVERLAP=""
  OLDIFS=$IFS
  IFS='
'
  for f in ${FILTERS%""}
  do
    for g in ${FILTERS%""}
    do
      if [ "$f" = "$g" ]
      then
        break
      fi
      OVERLAP=`"$CAT" "$OUTDIR/$g"".log" "$OUTDIR/$f"".log" | "$SED" -n '/Selected Publications/p;' | "$SED" 's/  Selected Publications: //' | "$PYTHON" "$LISTCHECKER"`
      if [ "$OVERLAP" != "" ]
      then
        echo "Warning: There are items selected both by $g and by $f!" >&2
        if [ $QUIET -eq 0 ]
        then
          echo "         These are: $OVERLAP" >&2
        fi
      fi
    done
  done
  IFS=$OLDIFS

  if [ $QUIET -eq 0 ]
  then
    echo "...done." >& 2
  fi
fi

exit 0
