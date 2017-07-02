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
import xmltodict
import sys
### the following two lines are a dirty hack and are discouraged! we save time by not looking for another solution. see also http://stackoverflow.com/questions/2276200/changing-default-encoding-of-python and https://anonbadger.wordpress.com/2015/06/16/why-sys-setdefaultencoding-will-break-code/
reload(sys)
sys.setdefaultencoding("utf8")
from time import gmtime, strftime
from optparse import OptionParser
from collections import OrderedDict

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

usage = "Usage: %prog [-v] -p PERSFILE.xml [-o OUTPUTFILE.xml] [INPUTFILE.xml]"
parser = OptionParser(usage)
parser.add_option("-v", "--verbose",
  action = "store_true", dest = "verb", default = False,
  help = "Show what I'm doing [default=false]")
parser.add_option("-p", "--persfile", nargs = 1,
  action = "store", dest = "persfile",
  metavar = "PERSFILE.xml", help = "Specify the pers-file [required]")
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

if not opts.persfile:
  parser.error("You need to specify a pers-file!")
else:
  persfile = opts.persfile

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

if not os.access(persfile, os.R_OK):
  parser.error("It seems I cannot access the pers-file!")

if not tostdout:
  if not os.access(outfile, os.W_OK):
    parser.error("It seems I will not be able to write to the output file!")

### read and parse the pers-file

if verbose:
  print "Reading " + persfile + "..."

pers_fd = codecs.open(persfile, "r", "utf8")

try:
  pers_dict = xmltodict.parse(pers_fd.read(), encoding="utf-8")
finally:
  if verbose:
    print "Successfully read " + persfile + " and created the corresponding dictionary."
pers_fd.close()

if not "FILEMAKEREXPORT" in pers_dict:
  print "Error: Wrong format! Did you parse the original export first?"
  exit (1)

### read and parse the input file

if verbose:
  print "Reading " + (infile if not fromstdin else "from standard input") + "..."
if not fromstdin:
  in_fd = codecs.open(infile, "r", "utf8")
else:
  in_fd = infile

try:
  in_dict = xmltodict.parse(in_fd.read(), encoding="utf-8")
finally:
  if verbose:
    print "Successfully read " + (infile if not fromstdin else "from standard input") + " and created the corresponding dictionary."
in_fd.close()

if not "FILEMAKEREXPORT" in in_dict:
  print "Error: Wrong format! Did you parse the original export first?"
  exit (1)

### create the target dict

if verbose:
  print "Creating the target dictionary..."

target_size = int(in_dict["FILEMAKEREXPORT"]["@ITEMS"])
sourcemtime = in_dict["FILEMAKEREXPORT"]["@SOURCEMTIME"]
db_size = int(in_dict["FILEMAKEREXPORT"]["@DBSIZE"])
db_name = in_dict["FILEMAKEREXPORT"]["@DBNAME"]
claimed_size = int(in_dict["FILEMAKEREXPORT"]["@CLAIMEDRECORDS"])

if db_size != target_size:
  print "Warning: Some data seems to be missing (db size is " + str(db_size) + ", but result set size is " + str(target_size) + ")"

pers_set = pers_dict["FILEMAKEREXPORT"]["ITEM"]
in_set = in_dict["FILEMAKEREXPORT"]["ITEM"]

in_size = len(in_set)

if len(pers_set) != in_size or int(pers_dict["FILEMAKEREXPORT"]["@ITEMS"]) != target_size or int(pers_dict["FILEMAKEREXPORT"]["@DBSIZE"]) != db_size or int(pers_dict["FILEMAKEREXPORT"]["@CLAIMEDRECORDS"]) != claimed_size or pers_dict["FILEMAKEREXPORT"]["@DBNAME"] != db_name:
  print "Error: The provided files do not seem to correspond to one another!"
  exit(1)

if in_size != target_size:
  print "Warning: Some data seems to be " + ("in excess" if in_size > target_size else "missing") + " (claimed size is " + target_size + ", but we got " + () + str(len(in_set)) + "rows)"

rows = []
for n in range(0,len(in_set)):
  if in_set[n]["@NO"] != pers_set[n]["@NO"] or in_set[n]["@ROWID"] != pers_set[n]["@ROWID"]:
    print "Error: Files seem to mismatch (ITEM NO." + str(n) + "). Cannot merge!"
    exit(1)
  in_person = None
  in_pnr = None
  in_arraydata_length = 0
  pers_arraydata_length = 0
  for attr in in_set[n]["ATTRIB"]:
    if attr["@NAME"].find("::Person") != -1:
      in_person = attr["#text"] if "#text" in attr else (attr["DATA"] if "DATA" in attr else None)
      if in_pnr:
        break
    elif attr["@NAME"].find("::Pers Nr.") != -1:
      in_pnr = attr["#text"] if "#text" in attr else (attr["DATA"] if "DATA" in attr else None)
      if "DATA" in attr:
        in_arraydata_length = len(attr["DATA"])
      if in_person:
        break
  pers_person = None
  pers_pnr = None
  for attr in pers_set[n]["ATTRIB"]:
    if attr["@NAME"].find("::Person") != -1:
      pers_person = attr["#text"] if "#text" in attr else (attr["DATA"] if "DATA" in attr else None)
      if pers_pnr:
        break
    elif attr["@NAME"].find("::Pers Nr.") != -1:
      pers_pnr = attr["#text"] if "#text" in attr else (attr["DATA"] if "DATA" in attr else None)
      if "DATA" in attr:
        pers_arraydata_length = len(attr["DATA"])
      if pers_person:
        break
  in_arraydata = any([("DATA" in k) for k in in_set[n]["ATTRIB"]])
  pers_arraydata = any([("DATA" in k) for k in pers_set[n]["ATTRIB"]])
  if in_arraydata != pers_arraydata: # catching array/non-array merger
    if in_arraydata:
      print "Warning: ITEM NO." + str(n) + " contains an array, but pers-data is single valued. Trying to recover..."
      attr_set = []
      for attr in pers_set[n]["ATTRIB"]:
        attr["DATA"] = [attr["#text"] if "#text" in attr else None]
        for kk in range(2, in_arraydata_length+1):
          attr["DATA"].append(None)
        attr["#text"] = None
        attr_set.append(attr)
        if attr["@NAME"].find("::Person") != -1:
          pers_person = attr["DATA"]
        if attr["@NAME"].find("::Pers Nr.") != -1:
          pers_pnr = attr["DATA"]
      pers_set[n]["ATTRIB"] = attr_set
    else:
      print "Error: ITEM NO." + str(n) + " is single valued, but pers-data is multi-valued. Cannot recover!"
      exit(1)
  if in_arraydata and pers_arraydata and in_arraydata_length != pers_arraydata_length: # catch different array lengths
    if pers_arraydata_length > in_arraydata_length:
      print "Error: Trying to merge arrays of different lengths in ITEM NO." + str(n) + ", but cannot recover since pers-data has too many rows!"
      exit(1)
    else:
      print "Warning: Merging arrays of different size in ITEM NO." + str(n) + "."
      attr_set = []
      for attr in pers_set[n]["ATTRIB"]:
        for kk in range(pers_arraydata_length+1, in_arraydata_length+1):
          attr["DATA"].append(None)
        attr_set.append(attr)
        if attr["@NAME"].find("::Person") != -1:
          pers_person = attr["DATA"]
        if attr["@NAME"].find("::Pers Nr.") != -1:
          pers_pnr = attr["DATA"]
      pers_set[n]["ATTRIB"] = attr_set
  if pers_pnr != in_pnr and in_arraydata and pers_arraydata and len(pers_pnr) == len(in_pnr) and all([(k == None or k in in_pnr) for k in pers_pnr]): # catch false ordering
    reordering = [(pers_pnr.index(in_pnr[j]) if in_pnr[j] in pers_pnr else j) for j in range(len(in_pnr))]
    reordering_inv = [(in_pnr.index(pers_pnr[j]) if (pers_pnr[j] and pers_pnr[j] in in_pnr) else None) for j in range(len(pers_pnr))]
    remaining_indices = range(len(pers_pnr))
    for j in reordering_inv:
      if j in remaining_indices:
        remaining_indices.pop(remaining_indices.index(j))
    if None in reordering_inv:
      for j in range(len(reordering_inv)):
        if reordering_inv[j] == None:
          reordering_inv[j] = remaining_indices.pop(0)
    reordering = [reordering_inv.index(j) for j in range(len(reordering_inv))]
    if sorted(reordering) != range(len(in_pnr)):
      print "Warning: Inconsistent ordering of pers-data in ITEM NO." + str(n) + ", but could not recover.", reordering, in_pnr, pers_pnr
    else:
      print "Notice: Re-ordering pers-data for ITEM NO." + str(n)
      attr_set = []
      for attr in pers_set[n]["ATTRIB"]:
        attr["DATA"] = [attr["DATA"][reordering[j]] for j in range(len(in_pnr))]
        attr_set.append(attr)
        if attr["@NAME"].find("::Person") != -1:
          pers_person = attr["DATA"]
        if attr["@NAME"].find("::Pers Nr.") != -1:
          pers_pnr = attr["DATA"]
      pers_set[n]["ATTRIB"] = attr_set
  if in_person != pers_person or in_pnr != pers_pnr:
    print "Warning: Entry (ITEM NO." + str(n) + ") seems to relate different persons!"
  for attr in pers_set[n]["ATTRIB"]:
    in_set[n]["ATTRIB"].append(attr)
  r = OrderedDict()
  r.update({"@NO" : in_set[n]["@NO"]})
  r.update({"@ROWID" : in_set[n]["@ROWID"]})
  r.update({"ATTRIB" : in_set[n]["ATTRIB"]})
  rows.append(r)
  if testing:
    if n > 9:
      break

obtained_size = len(rows)

if obtained_size != target_size:
  print "Warning: Expected " + str(target_size) + " rows, but found " + ("only " if obtained_size < target_size else "") + str(obtained_size) + "!"

out_set = OrderedDict()
out_set.update({"@TIMESTAMP" : timestamp})
out_set.update({"@SOURCEMTIME" : sourcemtime})
out_set.update({"@ITEMS" : str(obtained_size)})
out_set.update({"@DBNAME" : db_name})
out_set.update({"@DBSIZE" : str(db_size)})
out_set.update({"@CLAIMEDRECORDS" : str(claimed_size)})
out_set.update({"ITEM" : rows})

out_dict = OrderedDict({"MERGEDFILEMAKEREXPORT" : out_set})

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
