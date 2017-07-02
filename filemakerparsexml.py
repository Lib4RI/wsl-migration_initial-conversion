#!/usr/bin/python
# coding=utf-8

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

### load stuff we need

import os
import codecs
import unicodedata
import xmltodict
from lxml import etree
import sys
### the following two lines are a dirty hack and are discouraged! we save time by not looking for another solution. see also http://stackoverflow.com/questions/2276200/changing-default-encoding-of-python and https://anonbadger.wordpress.com/2015/06/16/why-sys-setdefaultencoding-will-break-code/
reload(sys)
sys.setdefaultencoding("utf8")
from re import sub
from time import gmtime, strftime
from optparse import OptionParser
from collections import OrderedDict
from cStringIO import StringIO

### some constants

STDIN   = sys.stdin  #'/dev/stdin'
STDOUT  = sys.stdout #'/dev/stdout'
testing = True
testing = False # uncomment this if you are done testing

timestamp = strftime('%Y%m%dT%H%M%SZ', gmtime())

### redirect all output to stderr

oldstdout = sys.stdout
sys.stdout = sys.stderr

### say that we are testing, if we are

if testing:
  print "Notice: Testing mode is active!"

### parse (and validate) the command line

usage = "Usage: %prog [-v] [-o OUTPUTFILE.xml] [INPUTFILE.xml]"
parser = OptionParser(usage)
parser.add_option("-v", "--verbose",
  action = "store_true", dest = "verb", default = False,
  help = "Show what I'm doing [default=false]")
parser.add_option("-o", "--output", nargs = 1,
  action = "store", dest = "outfile",
  metavar = "OUTPUTFILE.xml", help = "Specify the output-file")
  
(opts, args) = parser.parse_args()

verbose = testing or opts.verb # always be verbose while testing
tostdout = True
fromstdin = True

if verbose:
  print "Parsing command line..."

if len(args) > 1:
  parser.error("Expected only one input file!")

if opts.outfile:
  outfile = opts.outfile
  tostdout = False
else:
  outfile = STDOUT
if args:
  infile = args[0]
  fromstdin = False
else:
  infile = STDIN

if not fromstdin:
  if not os.access(infile, os.R_OK):
    parser.error("It seems I cannot access the input file!")

if not tostdout:
  if not os.access(outfile, os.W_OK):
    parser.error("It seems I will not be able to write to the output file!")

### read and parse the input file

sourcemtime = strftime('%Y%m%dT%H%M%SZ', gmtime(os.path.getmtime(infile)))
if verbose:
  print "Reading " + (infile if not fromstdin else "from standard input") + "..."
if not fromstdin:
  in_fd = codecs.open(infile, "r", "utf8")
else:
  in_fd = infile

if verbose:
  print "Parsing xml with a tolerant parser..."

et_parser = etree.XMLParser(encoding="utf-8", recover=True)
in_tree = etree.parse(StringIO(sub("\x04|\x10", "", sub("([\x00-\x7f])(\x60|\xb4)", r'\1' + "'", sub("&apos;", "'", sub("&quot;", '"', in_fd.read()))))), et_parser) # to substitute all characters '\x60'='`' and '\xb4'='´' by '\x27'=''' might be dangerous!! indeed, we re-replace '\x27'=''' by '\xb4'='´' if it's preceded by '\x3c' which is a unicode control character, see http://www.utf8-chartable.de/

if verbose:
  print "Converting back to xml and parsing into a dictionary..."

try:
  in_dict = xmltodict.parse(codecs.decode(etree.tostring(in_tree), "utf8"), encoding="utf-8")
finally:
  if verbose:
    print "Successfully read " + (infile if not fromstdin else "from standard input") + " and created the corresponding dictionary."
  del in_tree # we do not need this henceforth
in_fd.close()

### create the target dict

if verbose:
  print "Creating the target dictionary..."

in_set = OrderedDict()
in_set_rows = []
db_name = in_dict["FMPXMLRESULT"]["DATABASE"]["@NAME"]
db_size = int(in_dict["FMPXMLRESULT"]["DATABASE"]["@RECORDS"])
target_size = int(in_dict["FMPXMLRESULT"]["RESULTSET"]["@FOUND"])
if db_size != target_size:
  print "Warning: Some data seems to be missing (db size is " + str(db_size) + ", but claimed result set size is " + str(target_size) + ")"
n = 0
for row in in_dict["FMPXMLRESULT"]["RESULTSET"]["ROW"]:
  r = OrderedDict()
  rr = []
  i = 0
  warned = False
  for field in in_dict["FMPXMLRESULT"]["METADATA"]["FIELD"]:
    rrr = OrderedDict()
    rrr.update({"@NAME" : field["@NAME"]})
    rrr.update({"#text" : (row["COL"][i]["DATA"] if row["COL"][i] and "DATA" in row["COL"][i] else None)})
    # following if-clause inspired by http://stackoverflow.com/questions/1835018/python-check-if-an-object-is-a-list-or-tuple-but-not-string
    if rrr["#text"] and not isinstance(rrr["#text"], basestring):
      if hasattr(rrr["#text"], "__getitem__") or hasattr(rrr["#text"], "__iter__"):
        if not warned:
          print "Warning: ITEM NO." + str(n) + " has multiple (" + str(len(rrr["#text"])) + ") DATA entries."
          warned = True
        rrr.update({"DATA" : rrr["#text"]})
        del rrr["#text"]
      else:
        print "Warning: The element \"" + str(rrr["#text"]) + "\" will not be translatable into xml; the program will fail!"
    rr.append(rrr)
    i += 1
  for j in range(len(rr)): # normalise unicode if necessary
    attr = rr[j]
    if "DATA" in attr and attr["DATA"]:
      udata = []
      for val in attr["DATA"]:
        uval = unicodedata.normalize('NFKC', (val if val else u""))
        if uval != (val if val else u""):
          print "Warning: Replaced '" + attr["@NAME"] + "':'DATA':\"" + val + "\" by '" + attr["@NAME"] + "':'DATA':\"" + uval + "\" (normalised unicode) in ITEM NO." + str(n) + "."
          udata.append(uval)
        else:
          udata.append(val)
      rr[j]["DATA"] = udata
    elif "#text" in attr and attr["#text"]:
      utxt = unicodedata.normalize('NFKC', attr["#text"])
      if utxt != attr["#text"]:
        print "Warning: Replaced '" + attr["@NAME"] + "':\"" + attr["#text"] + "\" by '" + attr["@NAME"] + "':\"" + utxt + "\" (normalised unicode) in ITEM NO." + str(n) + "."
        rr[j]["#text"] = utxt
  r.update({"@NO" : str(n)})
  r.update({"@ROWID" : row["@RECORDID"]})
  r.update({"ATTRIB" : rr})
  in_set_rows.append(r)
  n += 1
  if testing:
    if n > 10:
      break

obtained_size = len(in_set_rows)
if obtained_size != target_size:
  print "Warning: Expected " + str(target_size) + " rows, but found " + ("only " if obtained_size < target_size else "") + str(obtained_size) + "!"

in_set.update({"@TIMESTAMP" : timestamp})
in_set.update({"@SOURCEMTIME" : sourcemtime})
in_set.update({"@ITEMS" : str(obtained_size)})
in_set.update({"@DBNAME" : db_name})
in_set.update({"@DBSIZE" : str(db_size)})
in_set.update({"@CLAIMEDRECORDS" : str(target_size)})
in_set.update({"ITEM" : in_set_rows})

out_dict = OrderedDict({"FILEMAKEREXPORT": in_set})

if verbose:
  print "Successfully created the target dictionary."

### write to the output file

if verbose:
  print "Exporting the dictionary to " + (outfile if not tostdout else "standard output") + "..."

if not tostdout:
  out_fd = codecs.open(outfile, "w", "utf8")
else:
  out_fd = outfile

if testing:
  print out_dict

out_xml = xmltodict.unparse(out_dict, encoding='utf-8', pretty=True, indent='  ')
del out_dict # we do not need this henceforth

if testing:
  print out_xml

try:
  out_fd.write(codecs.encode(out_xml, "utf8"))
finally:
  if verbose:
    print "Successfully exported " + str(obtained_size) + " records."
out_fd.close()

exit(0)
