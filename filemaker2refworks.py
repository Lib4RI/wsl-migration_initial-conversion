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
import csv
import sys
### the following two lines are a dirty hack and are discouraged! we save time by not looking for another solution. see also http://stackoverflow.com/questions/2276200/changing-default-encoding-of-python and https://anonbadger.wordpress.com/2015/06/16/why-sys-setdefaultencoding-will-break-code/
reload(sys)
sys.setdefaultencoding("utf8")
from re import sub, search
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

csv_suffix = "_out-csv"
tagged_suffix = "_out-tagged"
selected_suffix = "_out-selected"

lessermatch = True # set to True if you want person-matching to fall back to name matching and position matching rather than simultaneous position and name matching

### redirect all output to stderr

oldstdout = sys.stdout
sys.stdout = sys.stderr

if testing:
  print testing, sys.stdin.encoding, sys.stdout.encoding, oldstdout.encoding, sys.stderr.encoding
  print testing, sys.getdefaultencoding()

### say that we are testing, if we are

if testing:
  print "Notice: Testing mode is active!"

### some functions

def rowtruefalseuponcondition(row, condstr):
  for attr in row["ATTRIB"]:
    if condstr.find("'" + attr["@NAME"] + "'") != -1:
      condstr = condstr.replace("'" + attr["@NAME"] + "'", "'" + (attr["#text"].replace("'", "\\'") if "#text" in attr else '') + "'")
  condstr = condstr.replace('\n', '').replace('\r', '')
  return eval(condstr)

def get_prefix(tag): # assumes CCCNNN with CCC any no of chars and NNN any number of digits
  prefix = ''
  for c in tag:
    if c in "0123456789":
      break
    prefix += c
  return prefix
  

### parse (and validate) the command line

if testing:
  print "Called: " + " ".join(sys.argv)

usage = "Usage: %prog [-v] [-i|-I] [-t] -s SETUP.xml -a AUTHORLINKS.xml -c COAUTHORLINKS.xml -e EDITORLINKS.xml -j JOURNALS.xml [-o OUTPUTFILE.xml] [-d DIR] [PUBLICATIONS.xml]"
parser = OptionParser(usage)
parser.add_option("-v", "--verbose",
  action = "store_true", dest = "verbose", default = False,
  help = "Show what I'm doing [default=false]")
parser.add_option("-i", "--includesap",
  action = "store_true", dest = "includesap", default = False,
  help = "Include the SAP numbers, if available [default=false]")
parser.add_option("-I", "--IncludePersNr",
  action = "store_true", dest = "includepersno", default = False,
  help = "Include the \"Personal\" numbers, if available [default=false]")
parser.add_option("-t", "--timestamp",
  action = "store_true", dest = "timestampflag", default = False, # note: 'timestamp' is already used for the timestamp
  help = "Mark the output files with a timestamp [default=false]")
parser.add_option("-s", "--setup", nargs = 1,
  action = "store", dest = "setupfile",
  metavar = "SETUP.xml", help = "Specify the setup-file [required]")
parser.add_option("-a", "--authorlinks", nargs = 1,
  action = "store", dest = "authorfile",
  metavar = "AUTHORLINKS.xml", help = "Specify the authors-file [required]")
parser.add_option("-c", "--coauthorlinks", nargs = 1,
  action = "store", dest = "coauthorfile",
  metavar = "COAUTHORLINKS.xml", help = "Specify the coauthors-file [required]")
parser.add_option("-e", "--editorlinks", nargs = 1,
  action = "store", dest = "editorfile",
  metavar = "EDITORLINKS.xml", help = "Specify the editors-file [required]")
parser.add_option("-j", "--journals", nargs = 1,
  action = "store", dest = "journalfile",
  metavar = "JOURNALS.xml", help = "Specify the journals-file [required]")
parser.add_option("-o", "--output", nargs = 1,
  action = "store", dest = "outfile",
  metavar = "OUTPUTFILE.xml", help = "Specify the output-file")
parser.add_option("-d", "--dirout", nargs = 1,
  action = "store", dest = "dirout",
  metavar = "DIR", help = "Specify the output-directory for the 'csv', 'tagged' and 'selected' files")
  
(opts, args) = parser.parse_args()

verbose = testing or opts.verbose # always be verbose while testing
includesap = opts.includesap
includepersno = opts.includepersno

if includesap and includepersno:
  parser.error("You can activate only one of the two options -i and -I!")

if includesap:
  numberkey = "SAPNO"
elif includepersno:
  numberkey = "PERSNO"

timestampflag = opts.timestampflag
tostdout = True
fromstdin = True

if verbose:
  print "Parsing command line..."

if len(args) > 1:
  parser.error("Expected only one input file!")

if not opts.setupfile:
  parser.error("You need to specify a setup-file!")
else:
  setupfile = opts.setupfile

if not setupfile.endswith(".xml"):
  print "The setup-file should end in \".xml\"! Aborting..."
  exit(1)

dirout = "."
if opts.dirout:
  dirout = sub("/$", "", opts.dirout) if opts.dirout != "/" else "/" # remove trailing slash if not root directory
if not os.path.isdir(dirout):
  if os.path.isfile(dirout):
    parser.error("DIR \"" + dirout + "\" is not a directory!")
  else:
    os.mkdir(dirout)
if not os.access(dirout, os.W_OK):
  parser.error("It seems I will not be able to write to DIR \"" + dirout + "\"!")

csvfile = dirout + "/" + opts.setupfile[:-4] + csv_suffix + ".txt"
taggedfile = dirout + "/" + opts.setupfile[:-4] + tagged_suffix + ".txt"
selectedfile = dirout + "/" + opts.setupfile[:-4] + selected_suffix + ".xml"

if not opts.authorfile:
  parser.error("You need to specify an authors-file!")
else:
  authorfile = opts.authorfile

if not opts.coauthorfile:
  parser.error("You need to specify a coauthors-file!")
else:
  coauthorfile = opts.coauthorfile

if not opts.editorfile:
  parser.error("You need to specify a editors-file!")
else:
  editorfile = opts.editorfile

if not opts.journalfile:
  parser.error("You need to specify a journals-file!")
else:
  journalfile = opts.journalfile

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
    parser.error("It seems I cannot access the input file \"" + infile + "\"!")

if not os.access(setupfile, os.R_OK):
  parser.error("It seems I cannot access the setup-file \"" + setupfile + "\"!")

if not os.access(authorfile, os.R_OK):
  parser.error("It seems I cannot access the authors-file \"" + authorfile + "\"!")

if not os.access(coauthorfile, os.R_OK):
  parser.error("It seems I cannot access the coauthors-file \"" + coauthorfile + "\"!")

if not os.access(editorfile, os.R_OK):
  parser.error("It seems I cannot access the editors-file \"" + editorfile + "\"!")

if not os.access(journalfile, os.R_OK):
  parser.error("It seems I cannot access the journals-file \"" + journalfile + "\"!")

if not tostdout:
  if not os.access(outfile, os.W_OK):
    parser.error("It seems I will not be able to write to the output file \"" + outfile + "\"!")

### read and parse the setup-file

if verbose:
  print "Reading " + setupfile + "..."

setup_fd = codecs.open(setupfile, "r", "utf8")

try:
  setup_dict = xmltodict.parse(setup_fd.read(), encoding="utf-8")
finally:
  if verbose:
    print "Successfully read " + setupfile + " and created the corresponding dictionary."
setup_fd.close()

if not "FILEMAKERTOREFWORKSSETUP" in setup_dict or not "REFERENCETYPE" in setup_dict["FILEMAKERTOREFWORKSSETUP"] or not "FILTEREXPRESSION" in setup_dict["FILEMAKERTOREFWORKSSETUP"] or not (isinstance(setup_dict["FILEMAKERTOREFWORKSSETUP"]["FILTEREXPRESSION"], basestring) or "#text" in setup_dict["FILEMAKERTOREFWORKSSETUP"]["FILTEREXPRESSION"]):
  print "Error: Wrong format! Please provide a valid setup-file!"
  exit (1)

excludepersonmatches = None
excludepersonmatchesstr = ""
if "@EXCLUDEPERSONMATCHES" in setup_dict["FILEMAKERTOREFWORKSSETUP"]["FILTEREXPRESSION"]:
  validattrs = ["AuthorsOnly", "EditorsOnly", "AuthorsAndEditors", "NeitherAuthorsNorEditors"]
  excludepersonmatchesstr = setup_dict["FILEMAKERTOREFWORKSSETUP"]["FILTEREXPRESSION"]["@EXCLUDEPERSONMATCHES"]
  excludepersonmatches = set([k.strip() for k in excludepersonmatchesstr.split(",")]) # no need for order or duplicate entries
  if any([k not in validattrs for k in excludepersonmatches]):
    print "Error: The attribute EXCLUDEPERSONMATCHES must be a comma separated list of values in the set: \"" + "\", \"".join(validattrs) + "\""
    excludepersonmatches = None # in case we later decide not to exit here...
    exit(1)

### read and parse the authors-file

if verbose:
  print "Reading " + authorfile + "..."

author_fd = codecs.open(authorfile, "r", "utf8")

try:
  author_dict = xmltodict.parse(author_fd.read(), encoding="utf-8")
finally:
  if verbose:
    print "Successfully read " + authorfile + " and created the corresponding dictionary."
author_fd.close()

if not "FILEMAKEREXPORTPERSONLINKS" in author_dict or "PERSONS" not in author_dict["FILEMAKEREXPORTPERSONLINKS"] or "PUBLICATIONS" not in author_dict["FILEMAKEREXPORTPERSONLINKS"]:
  print "Error: Wrong format! Did you parse, merge and flatten the original export first?"
  exit (1)

author_per_keys = list(set(author_dict["FILEMAKEREXPORTPERSONLINKS"]["PERSONS"].keys())-set(['@ITEMS']))
author_pub_keys = list(set(author_dict["FILEMAKEREXPORTPERSONLINKS"]["PUBLICATIONS"].keys())-set(['@ITEMS']))
author_prefixes = [get_prefix(author_per_keys[0]) if author_per_keys else "PER", get_prefix(author_pub_keys[0]) if author_pub_keys else "PUB"]
del author_per_keys
del author_pub_keys

### read and parse the coauthors-file

if verbose:
  print "Reading " + coauthorfile + "..."

coauthor_fd = codecs.open(coauthorfile, "r", "utf8")

try:
  coauthor_dict = xmltodict.parse(coauthor_fd.read(), encoding="utf-8")
finally:
  if verbose:
    print "Successfully read " + coauthorfile + " and created the corresponding dictionary."
coauthor_fd.close()

if not "FILEMAKEREXPORTPERSONLINKS" in coauthor_dict or "PERSONS" not in coauthor_dict["FILEMAKEREXPORTPERSONLINKS"] or "PUBLICATIONS" not in coauthor_dict["FILEMAKEREXPORTPERSONLINKS"]:
  print "Error: Wrong format! Did you parse, merge and flatten the original export first?"
  exit (1)

coauthor_per_keys = list(set(coauthor_dict["FILEMAKEREXPORTPERSONLINKS"]["PERSONS"].keys())-set(['@ITEMS']))
coauthor_pub_keys = list(set(coauthor_dict["FILEMAKEREXPORTPERSONLINKS"]["PUBLICATIONS"].keys())-set(['@ITEMS']))
coauthor_prefixes = [get_prefix(coauthor_per_keys[0]) if coauthor_per_keys else "PER", get_prefix(coauthor_pub_keys[0]) if coauthor_pub_keys else "PUB"]
del coauthor_per_keys
del coauthor_pub_keys

### read and parse the editors-file

if verbose:
  print "Reading " + editorfile + "..."

editor_fd = codecs.open(editorfile, "r", "utf8")

try:
  editor_dict = xmltodict.parse(editor_fd.read(), encoding="utf-8")
finally:
  if verbose:
    print "Successfully read " + editorfile + " and created the corresponding dictionary."
editor_fd.close()

if not "FILEMAKEREXPORTPERSONLINKS" in editor_dict or "PERSONS" not in editor_dict["FILEMAKEREXPORTPERSONLINKS"] or "PUBLICATIONS" not in editor_dict["FILEMAKEREXPORTPERSONLINKS"]:
  print "Error: Wrong format! Did you parse, merge and flatten the original export first?"
  exit (1)

editor_per_keys = list(set(editor_dict["FILEMAKEREXPORTPERSONLINKS"]["PERSONS"].keys())-set(['@ITEMS']))
editor_pub_keys = list(set(editor_dict["FILEMAKEREXPORTPERSONLINKS"]["PUBLICATIONS"].keys())-set(['@ITEMS']))
editor_prefixes = [get_prefix(editor_per_keys[0]) if editor_per_keys else "PER", get_prefix(editor_pub_keys[0]) if editor_pub_keys else "PUB"]
del editor_per_keys
del editor_pub_keys

### read and parse the journals-file

if verbose:
  print "Reading " + journalfile + "..."

journal_fd = codecs.open(journalfile, "r", "utf8")

try:
  journal_dict = xmltodict.parse(journal_fd.read(), encoding="utf-8")
finally:
  if verbose:
    print "Successfully read " + journalfile + " and created the corresponding dictionary."
journal_fd.close()

if not "FILEMAKEREXPORT" in journal_dict:
  print "Error: Wrong format! Did you parse the original export first?"
  exit (1)

jset = []
for row in journal_dict["FILEMAKEREXPORT"]["ITEM"]:
  j = OrderedDict()
  for a in row["ATTRIB"]:
    j.update({a["@NAME"] : a["#text"] if "#text" in a else None})
  jset.append(j)

journals = OrderedDict()
for j in jset:
  abbr = ""
  abbr += j["Ab.1"].strip() if j["Ab.1"] else ""
  abbr += ((" " if abbr else "") + j["Ab.2"].strip()) if j["Ab.2"] else ""
  abbr += ((" " if abbr else "") + j["Ab.3"].strip()) if j["Ab.3"] else ""
  abbr += ((" " if abbr else "") + j["Ab.4"].strip()) if j["Ab.4"] else ""
  abbr += ((" " if abbr else "") + j["Ab.5"].strip()) if j["Ab.5"] else ""
  abbr += ((" " if abbr else "") + j["Ab.6"].strip()) if j["Ab.6"] else ""
  abbr += ((" " if abbr else "") + j["Ab.7"].strip()) if j["Ab.7"] else ""
  abbr += ((" " if abbr else "") + j["Ab.8"].strip()) if j["Ab.8"] else ""
  abbr += ((" " if abbr else "") + j["Ab.9"].strip()) if j["Ab.9"] else ""
  abbr += ((" " if abbr else "") + j["Ab.10"].strip()) if j["Ab.10"] else ""
  abbrkey = abbr.strip().lower()
  fn = j["Text"]
  if fn:
    fn = (fn[:-3].strip() if fn.endswith("[R]") else fn)
    j["Text"] = fn
    cleanupfn = False
    if (fn.find("[") != -1 and not fn.endswith("[R]")) or fn.find("(") != -1 or fn.endswith(", The") or fn.endswith(", Der") or fn.endswith(", Die") or fn.endswith(", Le") or fn.endswith(", La") or fn.endswith(", L'") or fn.find("  ") != -1:
      print "Warning: Ambiguous journal name detected: \"" + fn + "\" (\"" + abbr + "\"); cleaning up..."
      cleanupfn = True
    if cleanupfn:
      fn = sub("[\(\[].*[\]\)]", "", fn).strip()
      if fn.endswith(", The") or fn.endswith(", Der") or fn.endswith(", Die"):
        fn = fn[:-5].strip()
      elif fn.endswith(", Le") or fn.endswith(", La"):
        fn = fn[:-4].strip()
      elif fn.endswith(", L'"):
        fn = "L'" + fn[:-4].strip()
      fn = sub("  ", " ", fn).strip()
      while fn.find("  ") != -1:
        sub("  ", " ", fn)
      if fn.lower().find(", the") != -1 or fn.lower().find(", der") != -1 or fn.lower().find(", die") != -1 or fn.lower().find(", le") != -1 or fn.lower().find(", la") != -1 or fn.lower().find(", l'") != -1:
        print "Warning: Something may still be weird about the journal name \"" + fn + "\"..."
      if fn.find(" ") == -1 and fn[0] == fn[0].lower() and not fn[1] == fn[1].upper():
        fn = fn[0].upper()+fn[1:]
    if fn != j["Text"]:
      print "Warning: Replaced journal name \"" + j["Text"] + "\" with \"" + fn + "\"."
  if abbrkey in journals:
    if fn != journals[abbrkey]:
      print "Warning: Journal abbreviation \"" + abbrkey + "\" already points to \"" + journals[abbrkey] + "\"; setting it now to \"" + fn + "\"."
      journals[abbrkey] = fn
  else:
    journals.update({abbrkey : fn})

del journal_dict, jset

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

db_name = in_dict["FILEMAKEREXPORT"]["@DBNAME"]
db_size = int(in_dict["FILEMAKEREXPORT"]["@DBSIZE"])
claimed_size = int(in_dict["FILEMAKEREXPORT"]["@CLAIMEDRECORDS"])
target_size = int(in_dict["FILEMAKEREXPORT"]["@ITEMS"])
sourcemtime = in_dict["FILEMAKEREXPORT"]["@SOURCEMTIME"]

if timestampflag:
  csvfile = csvfile[:csvfile.find(csv_suffix)] + "_" + sourcemtime + csvfile[csvfile.find(csv_suffix):]
  taggedfile = taggedfile[:taggedfile.find(tagged_suffix)] + "_" + sourcemtime + taggedfile[taggedfile.find(tagged_suffix):]
  selectedfile = selectedfile[:selectedfile.find(selected_suffix)] + "_" + sourcemtime + selectedfile[selectedfile.find(selected_suffix):]

### select content for export

if verbose:
  print "Selecting publications for export and creating the dictionary for rejected publications..."

if testing:
  print len(in_dict["FILEMAKEREXPORT"]["ITEM"])

selected_publications = []
rejected_publications = []
out_set = OrderedDict()
out_set_rows = []
n = 0
in_dict_row_length = len(in_dict["FILEMAKEREXPORT"]["ITEM"])
if in_dict_row_length != target_size:
  print "Warning: Inconsistent number of data entries. Expected " + str(target_size) + ", got " + str(in_dict_row_length) + "."
for n in range(in_dict_row_length):
  row_n = n-len(out_set_rows)
  row = in_dict["FILEMAKEREXPORT"]["ITEM"][row_n]
  datennr = None
  for attr in row["ATTRIB"]:
    if attr["@NAME"] == 'Daten.Nr':
      datennr = attr["#text"]
  accept_row = rowtruefalseuponcondition(row, (setup_dict["FILEMAKERTOREFWORKSSETUP"]["FILTEREXPRESSION"]["#text"] if "#text" in setup_dict["FILEMAKERTOREFWORKSSETUP"]["FILTEREXPRESSION"] else setup_dict["FILEMAKERTOREFWORKSSETUP"]["FILTEREXPRESSION"]))
  if accept_row:
    hasauthors = (author_prefixes[1] + datennr in author_dict["FILEMAKEREXPORTPERSONLINKS"]["PUBLICATIONS"] or coauthor_prefixes[1] + datennr in coauthor_dict["FILEMAKEREXPORTPERSONLINKS"]["PUBLICATIONS"])
    haseditors = (editor_prefixes[1] + datennr in editor_dict["FILEMAKEREXPORTPERSONLINKS"]["PUBLICATIONS"])
    if hasauthors and haseditors and set(["AuthorsAndEditors"]) <= excludepersonmatches:
      accept_row = False
    if hasauthors and set(["AuthorsOnly"]) <= excludepersonmatches:
      accept_row = False
    if haseditors and set(["EditorsOnly"]) <= excludepersonmatches:
      accept_row = False
    if not hasauthors and not haseditors and set(["NeitherAuthorsNorEditors"]) <= excludepersonmatches:
      accept_row = False
    if not accept_row and verbose:
      print "Notice: Rejecting publication no." + datennr + " because EXCLUDEPERSONMATCHES=\"" + excludepersonmatchesstr + "\"."
  if accept_row:
    selected_publications.append(datennr)
  else:
    rejected_publications.append(datennr)
    out_set_rows.append(row)
    del in_dict["FILEMAKEREXPORT"]["ITEM"][row_n]

if verbose:
  print "List of selected (" + str(len(selected_publications)) + ") and rejected (" + str(len(rejected_publications)) + ") publications ('Daten.Nr'):"
  print "  Selected Publications: " + ", ".join(selected_publications)
  print "  Rejected Publications: " + ", ".join(rejected_publications)

if testing:
  print len(out_set_rows), len(in_dict["FILEMAKEREXPORT"]["ITEM"])

obtained_size = len(out_set_rows)
export_size = len(in_dict["FILEMAKEREXPORT"]["ITEM"])
if obtained_size + export_size != in_dict_row_length:
  print "Warning: Expected " + str(in_dict_row_length-export_size) + " remaining rows, but found " + ("only " if obtained_size < in_dict_row_length - export_size else "") + str(obtained_size) + "!"

in_dict["FILEMAKEREXPORT"]["@TIMESTAMP"] = timestamp
in_dict["FILEMAKEREXPORT"]["@ITEMS"] = str(export_size)

out_set.update({"@TIMESTAMP" : timestamp})
out_set.update({"@SOURCEMTIME" : sourcemtime})
out_set.update({"@ITEMS" : str(obtained_size)})
out_set.update({"@DBNAME" : db_name})
out_set.update({"@DBSIZE" : str(db_size)})
out_set.update({"@CLAIMEDRECORDS" : str(claimed_size)})
out_set.update({"ITEM" : out_set_rows})

out_dict = OrderedDict({"FILEMAKEREXPORT": out_set})

if verbose:
  print "Successfully created the target dictionary for rejected publications."

### processing selected publications

resultset = []
for row in in_dict["FILEMAKEREXPORT"]["ITEM"]:
  r = OrderedDict()
  for attr in row["ATTRIB"]:
    r.update({attr["@NAME"] : attr["#text"] if "#text" in attr else None})
  resultset.append(r)

if export_size != len(resultset):
  print "Warning: possibly some rows were lost (found " + str(len(resultset)) + ", expected " + str(export_size) + ")"

if verbose:
  print "Successfully created the target dictionary for selected publications."

### generate csv-dict

def get_author_list(s):
  if s == None:
    return []
  return [ss.strip() for ss in s.split(";")]

def make_initials(s):
  if s == None:
    return ""
  s = [n.strip() for n in s.split()]
  r = []
  for n in s:
    r.append(n[0])
  return ".".join(r) + "."

def match_persons(nr, authstr, aa, adict, apre, perstr = "person"):
  global m, tomatch, matchedpos # tomatch, resp. matchedpos have to be externally reset to 0, resp. [] for each publication
  global authorsmatched, coauthorsmatched, editorsmatched
  if apre[1] + nr not in adict["PUBLICATIONS"]: # nothing to match
    return aa
  if "@POS" in adict["PUBLICATIONS"][apre[1] + nr]["PERSLINK"]:
    adict["PUBLICATIONS"][apre[1] + nr]["PERSLINK"] = [adict["PUBLICATIONS"][apre[1] + nr]["PERSLINK"]]
  tomatch += len(adict["PUBLICATIONS"][apre[1] + nr]["PERSLINK"])
  for a_l in adict["PUBLICATIONS"][apre[1] + nr]["PERSLINK"]:
    pos_t = int(a_l["@POS"])
    if perstr == "editor":
      pos_t -= 1
    pos = pos_t
    if pos in matchedpos:
      print "Warning: Possible data corruption in publication no." + nr + ": position " + str(pos + (0 if perstr == "editor" else 0)) + " was already matched in \"" + authstr + "\""
    a_t = adict["PERSONS"][apre[0] + a_l["#text"]]
    if pos >= len(aa):
      print "Warning: Claimed " + perstr + " position " + str(pos_t + (1 if perstr == "editor" else 0)) + " is too large in publication no." + nr + "! " + ("Perhaps \"" if int(pos_t) == len(aa) else "Could not find \"") + (a_t["FULLNAME"] if a_t["FULLNAME"] else "") + "\" (WSL(" + (a_t[numberkey] if a_t[numberkey] else "") + ")) " + ("is the last " + perstr if int(pos_t) == len(aa) else "") + "in the list of " + str(len(aa)) + " persons \"" + authstr + "\"?"
      continue
    a = [n.strip() for n in aa[pos].split(',')]
    m_f = (a[0] == (a_t["FAMILYNAME"].strip() if a_t["FAMILYNAME"] else a_t["FAMILYNAME"]))
    m_g = (a[1] == make_initials(a_t["GIVENNAME"].strip() if a_t["GIVENNAME"] else a_t["GIVENNAME"]) if len(a) > 1 else True)
    m_g_l = (a[1][:2] == make_initials(a_t["GIVENNAME"].strip() if a_t["GIVENNAME"] else a_t["GIVENNAME"])[:2] if len(a) > 1 else True)
    if m_f and (m_g or (lessermatch and m_g_l)):
      if verbose:
        print "Notice: Matched " + perstr + " \"" + aa[pos] + "\" with \"" + a_t["FULLNAME"] + "\" (WSL(" + (a_t[numberkey] if a_t[numberkey] else "") + ")) at position " + str(pos + (1 if perstr == "editor" else 0)) + " in publication no." + nr + (" using lesser matching based on first initial" if not m_g else "") + "."
      if a[0].find("WSL") != -1:
        print "Warning: Rematch of (co-)author \"" + sub("WSL\([0-9]*\)", "", aa[pos]) + "\" with " + perstr + " \"" + (a_t["FULLNAME"] if a_t["FULLNAME"] else "") + "\" WSL(" + (a_t[numberkey] if a_t[numberkey] else "") + ")) at position " + str(pos) + " in publication no." + nr + "."
        if sub(".*WSL\(([0-9]*)\).*", r'\1', a[0]) != (a_t[numberkey] if a_t[numberkey] else ""):
          print "Warning: Mismatching SAP/Personal numbers! Had " + sub(".*WSL\(([0-9]*)\).*", r'\1', a[0]) + ", now saw " + (a_t[numberkey] if a_t[numberkey] else "None")
      matchstr = aa[pos] + " = WSL(" + a_t["FULLNAME"] + ") in publication no." + nr + ": \"" + authstr + "\""
      if perstr == "author":
        authorsmatched.append("AMATCH: " + matchstr)
      elif perstr == "co-author":
        coauthorsmatched.append("CMATCH: " + matchstr)
      elif perstr == "editor":
        editorsmatched.append("EMATCH: " + matchstr)
      a[0] = a[0] + "WSL" + ("(" + (a_t[numberkey] if a_t[numberkey] else "") + ")" if includesap or includepersno else "")
      matchedpos.append(pos)
      m += 1
    else:
      print "Warning: Expected to match " + perstr + " at position " + str(pos + (1 if perstr == "editor" else 0)) + " in publication no." + nr + ", but \"" + aa[pos] + "\" did not match \"" + (a_t["FULLNAME"] if a_t["FULLNAME"] else "") + "\""
    aa[pos] = ",".join(a)
  if tomatch == m or not lessermatch:
    return aa
  for pos in sorted(set(range(len(aa))) - set(matchedpos), key = lambda t: int(t)):
    a = [n.strip() for n in aa[pos].split(',')]
    for a_l in adict["PUBLICATIONS"][apre[1] + nr]["PERSLINK"]:
      pos_t = int(a_l["@POS"])
      if perstr == "editor":
        pos_t -= 1
      a_t = adict["PERSONS"][apre[0] + a_l["#text"]]
      if a[0] == (a_t["FAMILYNAME"].strip() if a_t["FAMILYNAME"] else a_t["FAMILYNAME"]) and (a[1] == make_initials(a_t["GIVENNAME"].strip() if a_t["GIVENNAME"] else a_t["GIVENNAME"]) if len(a) > 1 else True):
        if verbose:
          print "Notice: Matched " + perstr + " \"" + aa[pos] + "\" with \"" + a_t["FULLNAME"] + "\" (WSL(" + (a_t[numberkey] if a_t[numberkey] else "") + ")) at position " + str(pos + (1 if perstr == "editor" else 0)) + " in publication no." + nr + " using lesser matching."
        if a[0].find("WSL") != -1:
          print "Warning: Rematch of (co-)author \"" + sub("WSL\([0-9]*\)", "", aa[pos]) + "\" with " + perstr + " \"" + (a_t["FULLNAME"] if a_t["FULLNAME"] else "") + "\" WSL(" + (a_t[numberkey] if a_t[numberkey] else "") + ")) at position " + str(pos) + " in publication no." + nr + " using lesser matching."
          if sub(".*WSL\(([0-9]*)\).*", r'\1', a[0]) != (a_t[numberkey] if a_t[numberkey] else ""):
            print "Warning: Mismatching SAP/Personal numbers! Had " + sub(".*WSL\(([0-9]*)\).*", r'\1', a[0]) + ", now saw " + (a_t[numberkey] if a_t[numberkey] else "None")
        matchstr = aa[pos] + " = WSL(" + a_t["FULLNAME"] + ") in publication no." + nr + ": \"" + authstr + "\""
        if perstr == "author":
          authorsmatched.append("AMATCH: " + matchstr)
        elif perstr == "co-author":
          coauthorsmatched.append("CMATCH: " + matchstr)
        elif perstr == "editor":
          editorsmatched.append("EMATCH: " + matchstr)
        a[0] = a[0] + "WSL" + ("(" + (a_t[numberkey] if a_t[numberkey] else "") + ")" if includesap or includepersno else "")
        matchedpos.append(pos_t)
        m += 1
        if pos != pos_t:
          print "Warning: Possible data corruption in publication no." + nr + ": expected to match " + perstr + " \"" + sub("WSL\([0-9]*\)", "", aa[pos]) + "\" with \"" + (a_t["FULLNAME"] if a_t["FULLNAME"] else "") + "\" (WSL(" + (a_t[numberkey] if a_t[numberkey] else "") + ")) at position " + str(pos_t + (1 if perstr == "editor" else 0)) + " using lesser matching but found it at postition " + str(pos + (1 if perstr == "editor" else 0)) + " in: \"" + authstr + "\""
      aa[pos] = ",".join(a)
  if tomatch == m:
    return aa
  for a_l in adict["PUBLICATIONS"][apre[1] + nr]["PERSLINK"]:
    pos_t = int(a_l["@POS"])
    if perstr == "editor":
      pos_t -= 1
    pos = pos_t
    if pos in matchedpos:
      continue
    if pos >= len(aa):
      continue
    a = [n.strip() for n in aa[pos].split(',')]
    a_t = adict["PERSONS"][apre[0] + a_l["#text"]]
    if verbose:
      print "Notice: Matched " + perstr + " \"" + aa[pos] + "\" with \"" + a_t["FULLNAME"] + "\" (WSL(" + (a_t[numberkey] if a_t[numberkey] else "") + ")) at position " + str(pos) + " in publication no." + nr + " using lesser matching."
    if a[0].find("WSL") != -1:
      print "Warning: Rematch of (co-)author \"" + sub("WSL\([0-9]*\)", "", aa[pos]) + "\" with " + perstr + " \"" + (a_t["FULLNAME"] if a_t["FULLNAME"] else "") + "\" WSL(" + (a_t[numberkey] if a_t[numberkey] else "") + ")) at position " + str(pos) + " in publication no." + nr + " using lesser matching."
      if sub(".*WSL\(([0-9]*)\).*", r'\1', a[0]) != (a_t[numberkey] if a_t[numberkey] else ""):
        print "Warning: Mismatching SAP/Personal numbers! Had " + sub(".*WSL\(([0-9]*)\).*", r'\1', a[0]) + ", now saw " + (a_t[numberkey] if a_t[numberkey] else "None")
    matchstr = aa[pos] + " = WSL(" + a_t["FULLNAME"] + ") in publication no." + nr + ": \"" + authstr + "\""
    if perstr == "author":
      authorsmatched.append("AMATCH: " + matchstr)
    elif perstr == "co-author":
      coauthorsmatched.append("CMATCH: " + matchstr)
    elif perstr == "editor":
      editorsmatched.append("EMATCH: " + matchstr)
    a[0] = a[0] + "WSL" + ("(" + (a_t[numberkey] if a_t[numberkey] else "") + ")" if includesap or includepersno else "")
    matchedpos.append(pos)
    m += 1
    aa[pos] = ",".join(a)
  if m != tomatch:
    print "Warning: Not all " + perstr + " could be matched in publication no." + nr + " (missing " + str(tomatch - m) + "): \"" + authstr + "\""
  return aa

csv_keys = []
csv_keys.append("ID")
csv_keys.append("Reference Type")
csv_keys.append("Authors, Primary")
csv_keys.append("Title Primary")
csv_keys.append("Periodical Full")
csv_keys.append("Periodical Abbrev")
csv_keys.append("Pub Year")
csv_keys.append("Pub Date Free Form")
csv_keys.append("Volume")
csv_keys.append("Issue")
csv_keys.append("Start Page")
csv_keys.append("Other Pages")
csv_keys.append("Keywords")
csv_keys.append("Abstract")
csv_keys.append("Notes")
csv_keys.append("Personal Notes")
csv_keys.append("Authors, Secondary")
csv_keys.append("Title Secondary")
csv_keys.append("Edition")
csv_keys.append("Publisher")
csv_keys.append("Place Of Publication")
csv_keys.append("Authors, Tertiary")
csv_keys.append("Authors, Quaternary")
csv_keys.append("Authors, Quinary")
csv_keys.append("Title, Tertiary")
csv_keys.append("ISSN/ISBN")
csv_keys.append("Availability")
csv_keys.append("Author/Address")
csv_keys.append("Accession Number")
csv_keys.append("Language")
csv_keys.append("Classification")
csv_keys.append("Sub file/Database")
csv_keys.append("Original Foreign Title")
csv_keys.append("Links")
csv_keys.append("URL")
csv_keys.append("DOI")
csv_keys.append("PMID")
csv_keys.append("PMCID")
csv_keys.append("Call Number")
csv_keys.append("Database")
csv_keys.append("Data Source")
csv_keys.append("Identifying Phrase")
csv_keys.append("Retrieved Date")
csv_keys.append("Shortened Title")
csv_keys.append("User 1")
csv_keys.append("User 2")
csv_keys.append("User 3")
csv_keys.append("User 4")
csv_keys.append("User 5")
csv_keys.append("User 6")
csv_keys.append("User 7")
csv_keys.append("User 8")
csv_keys.append("User 9")
csv_keys.append("User 10")
csv_keys.append("User 11")
csv_keys.append("User 12")
csv_keys.append("User 13")
csv_keys.append("User 14")
csv_keys.append("User 15")
csv_dict = []
issn_dict = OrderedDict()
noauthors = []
notallpersonsmatched = []
nothingmatched = []
authorsmatched = []
coauthorsmatched = []
editorsmatched = []
personsnotmatched = 0
checkauthorfield = [] # will contain either ambiguous author names or missing authors
for result in resultset:
  r = OrderedDict()
  r.update({"ID" : result["Daten.Nr"]})
  r.update({"Reference Type" : setup_dict["FILEMAKERTOREFWORKSSETUP"]["REFERENCETYPE"]})
  authorsfield = result["Autor"].strip(' \n\r\t').strip(',;:').strip() if isinstance(result["Autor"], basestring) else result["Autor"]
  if not authorsfield:
    noauthors.append(result["Daten.Nr"])
    print "Warning: Publication no." + result["Daten.Nr"] + " has no authors!"
    authorsfield = ""
  if authorsfield.find(",") == -1 or authorsfield.find("(") == 0 or authorsfield.find("[") == 0:
    checkauthorfield.append(result["Daten.Nr"])
    print "Warning: Possible ambiguous author list \"" + authorsfield + "\" in publication no." + result["Daten.Nr"] + "."
  personsmissing = (authorsfield.find("...") != -1 or authorsfield.lower().find("et al") != -1)
  if personsmissing:
    print "Warning: Possibly incomplete (co-)author/editor list \"" + (authorsfield if authorsfield else "") + "\" in publication no." + str(result["Daten.Nr"]) + "! Might not be able to match all persons..."
    checkauthorfield.append(result["Daten.Nr"])
  aa = get_author_list(authorsfield)
  for pos in range(len(aa)):
    a = [n.strip() for n in aa[pos].split(',')]
    if len(a) != 2 or a[1].find(".") != 1 or search("([A-Z]\.-?)*([A-Z]\.)+", a[1]) == None:
      print "Warning: ambiguous name \"" + aa[pos] + "\" detected in publication no." + str(result["Daten.Nr"]) + ": \"" + (authorsfield if authorsfield else "") + "\""
      checkauthorfield.append(result["Daten.Nr"])
    if len(a) == 2:
      aa[pos] = ",".join(a)
  m = 0 # number of matches performed
  tomatch = 0
  matchedpos = []
  aa_r = match_persons(result["Daten.Nr"], authorsfield, aa, author_dict["FILEMAKEREXPORTPERSONLINKS"], author_prefixes, "author")
  aa_rr = match_persons(result["Daten.Nr"], authorsfield, aa_r, coauthor_dict["FILEMAKEREXPORTPERSONLINKS"], coauthor_prefixes, "co-author")
  aa_rrr = match_persons(result["Daten.Nr"], authorsfield, aa_rr, editor_dict["FILEMAKEREXPORTPERSONLINKS"], editor_prefixes, "editor")
  aa_rrrr = aa_rrr
  authors = ";".join(aa_rrrr)
  if authors.find("WSL") == -1:
    nothingmatched.append(result["Daten.Nr"])
    print "Warning: No (co-)author/editor was matched in publication no." + result["Daten.Nr"] + ": author-field was \"" + authorsfield + "\""
  if m != tomatch:
    notallpersonsmatched.append(result["Daten.Nr"])
    notallpersonsmatched
    personsnotmatched += tomatch - m
    print "Warning: Not all WSL-(co-)authors/editors could be matched in publication no." + result["Daten.Nr"] + " (missing " + str(tomatch - m) + " match" + ("es" if tomatch - m > 1 else "") + " in \"" + sub("WSL\([0-9]*\)", "", authors) + "\")."
  if testing:
    print result["Daten.Nr"], codecs.decode(authors, "utf8")
  r.update({"Authors, Primary" : authors})
  r.update({"Title Primary" : result["Titel"].strip('.,;: \n\r\t') if isinstance(result["Titel"], basestring) else result["Titel"]})
  if result["PO.fremd"] and result["PO.eigen"]:
    print "Warning: ambiguous data in publication no." + result["Daten.Nr"] + ": found 'PO.fremd'=\"" + result["PO.fremd"] + "\" and 'PO.eigen'=\"" + result["PO.eigen"] + "\"."
  jabbr = result["PO.fremd"] if result["PO.fremd"] else (result["PO.eigen"] if result["PO.eigen"] else None)
  jabbrkey = (jabbr.lower() if jabbr else jabbr)
  jfull = None
  if jabbr:
    if jabbrkey in journals:
      jfull = journals[jabbrkey]
  if jfull and result["ISSN"]:
    jissn = result["ISSN"].strip() if result["ISSN"] else None
    jissn = sub("issn", "", jissn.lower()).strip()
    jissn = sub("([0-9]{4}).+([0-9X]{4})", r'\1-\2', jissn)
    for c in jissn:
      if c not in "0123456789X-":
        jissn = None
        break
    if jissn and len(jissn) != 9:
      print "Warning: Probably invalid ISSN \"" + jissn + "\" in publication no." + result["Daten.Nr"] + "; ignoring."
      jissn = None
  r.update({"Periodical Full" : jfull})
  r.update({"Periodical Abbrev" : jabbr})
  r.update({"Pub Year" : result["Ersch.Jahr"]})
  r.update({"Pub Date Free Form" : None})
  r.update({"Volume" : result["Volume"].strip('.,;: \n\r\t') if isinstance(result["Volume"], basestring) else result["Volume"]})
  r.update({"Issue" : result["Heft.Nr"].strip('.,;: \n\r\t') if isinstance(result["Heft.Nr"], basestring) else result["Heft.Nr"]})
  pages = result["Seiten"].strip('.,;: \n\r\t') if isinstance(result["Seiten"], basestring) else result["Seiten"]
  if pages and pages.find('-') != -1:
    startpage = pages[:pages.find('-')]
    endpage = pages[pages.find('-')+1:]
  else:
    startpage = pages
    endpage = None
    if startpage and startpage[-1] == 'S':
      startpage = startpage[:-1] + 'pp.'
  r.update({"Start Page" : startpage})
  r.update({"Other Pages" : endpage})
  r.update({"Keywords" : None})
  r.update({"Abstract" : None})
  r.update({"Notes" : result["Daten.Nr"]})
  r.update({"Personal Notes" : result["FG Bemerkung"]})
  r.update({"Authors, Secondary" : None})
  r.update({"Title Secondary" : result["Herausg."].strip('.,;: \n\r\t') if isinstance(result["Herausg."], basestring) else result["Herausg."]})
  r.update({"Edition" : None})
  r.update({"Publisher" : result["Verlag"].strip('.,;: \n\r\t') if isinstance(result["Verlag"], basestring) else result["Verlag"]})
  r.update({"Place Of Publication" : result["Verlagsort"].strip('.,;: \n\r\t') if isinstance(result["Verlagsort"], basestring) else result["Verlagsort"]})
  r.update({"Authors, Tertiary" : None})
  r.update({"Authors, Quaternary" : None})
  r.update({"Authors, Quinary" : None})
  r.update({"Title, Tertiary" : None})
  r.update({"ISSN/ISBN" : result["ISSN"] + "/" + result["ISBN"] if (result["ISSN"] and result["ISBN"]) else (result["ISSN"] if result["ISSN"] else (result["ISBN"] if result["ISBN"] else None))})
  r.update({"Availability" : None})
  r.update({"Author/Address" : None})
  r.update({"Accession Number" : None})
  r.update({"Language" : None})
  r.update({"Classification" : None})
  r.update({"Sub file/Database" : None})
  r.update({"Original Foreign Title" : None})
  r.update({"Links" : result["DOI"]})
  r.update({"URL" : None})
  r.update({"DOI" : None})
  r.update({"PMID" : None})
  r.update({"PMCID" : None})
  r.update({"Call Number" : None})
  r.update({"Database" : None})
  r.update({"Data Source" : None})
  r.update({"Identifying Phrase" : None})
  r.update({"Retrieved Date" : None})
  r.update({"Shortened Title" : None})
  ryr = None
  for i in range(2017, 2000, -1):
    if result["JB.erschienen."+str(i)] == "x":
      ryr = str(i)
      break
  if not ryr:
    for i in range(99, 89, -1):
      if result["JB.erschienen."+str(i)] == "x":
        ryr = "19"+str(i)
  r.update({"User 1" : ryr}) # Reporting Year
  r.update({"User 2" : None}) # Dept. Descr.
  r.update({"User 3" : result["Erstellt"] if result["Erstellt"] else result["Aenderung.Datum"]}) # Ingest Date
  user4 = "ISI" if result["Jl.ISI"] == "x" else None
  if not user4:
    if result["Jl.Revie"] == "x" or result["Tag.b.Revie"] == "x":
      user4 = "referiert"
    elif result["Buch ohne Review"] == "x":
      user4 = "nicht referiert"
    elif result["Dissertation"] == "x":
      user4 = "DISS"
    else:
      user4 = None
  r.update({"User 4" : user4}) # SCI/SSCI/SCIE/...
  r.update({"User 5" : None})
  r.update({"User 6" : None}) # OA/not-OA
  r.update({"User 7" : None})
  r.update({"User 8" : None})
  r.update({"User 9" : None})
  r.update({"User 10" : None})
  r.update({"User 11" : None})
  r.update({"User 12" : None})
  r.update({"User 13" : None})
  r.update({"User 14" : None})
  r.update({"User 15" : None})
  csv_dict.append(r)

if len(noauthors) > 0:
  print "Warning: The following " + str(len(set(noauthors))) + " publications have an empty author field. Review: " + ", ".join(sorted(set(noauthors), key=lambda t: int(t)))
if len(notallpersonsmatched) > 0:
  print "Warning: A total of " + str(personsnotmatched) + " (co-)authors/editors were not matched. Review the following " + str(len(set(notallpersonsmatched))) + " publications: " + ", ".join(sorted(set(notallpersonsmatched), key=lambda t: int(t)))
if len(nothingmatched) > 0:
  print "Warning: The following " + str(len(set(nothingmatched))) + " publications did not have any (co-)author/editor matched: " + ", ".join(sorted(set(nothingmatched), key=lambda t: int(t)))
if len(checkauthorfield) > 0:
  print "Warning: The following " + str(len(set(checkauthorfield))) + " publications might contain errors in their author fields. Review: " + ", ".join(sorted(set(checkauthorfield), key=lambda t: int(t)))

personsmatched = len(authorsmatched) + len(coauthorsmatched) + len(editorsmatched)
if verbose:
  print "Info: A total of " + str(personsmatched) + " persons were matched."
  print "Matched authors " + str(len(authorsmatched)) + ":"
  print "\n".join(authorsmatched)
  print "Matched coauthors " + str(len(coauthorsmatched)) + ":"
  print "\n".join(coauthorsmatched)
  print "Matched editors " + str(len(editorsmatched)) + ":"
  print "\n".join(editorsmatched)

### export to csv

class UnicodeDictWriter: # added callback functionality to modify rows
  def __init__(self, f, keys, dialect=csv.excel, callback=lambda x: x, **kwds):
    self.queue = StringIO()
    self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
    self.stream = f
    self.keys = keys
    self.rowmod = callback
  def encode_array(self, arr):
    encarr = []
    for s in arr:
      if isinstance(s, basestring):
        s = codecs.encode(s, "utf8")
        s = s.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ') # nuke newlines and tabs
        while s.find('  ') != -1:
          s = s.replace('  ', ' ') # nuke double spaces
      encarr.append(s)
    return encarr
  def writeout(self):
    self.stream.write(codecs.decode(self.queue.getvalue(), "utf8"))
    self.queue.truncate(0)
  def writeheader(self):
    self.writer.writerow(self.encode_array(self.keys))
    self.writeout()
  def writerow(self, row):
    new_row = self.rowmod(row)
    self.writer.writerow(self.encode_array([new_row.get(key) for key in self.keys]))
    self.writeout()
  def writerows(self, rows):
    for row in rows:
      self.writerow(row)

def row_mod(row):
  new_row = OrderedDict()
  for key in row.keys():
    new_row.update({key : row[key]})
  # modify authors according to LK's specs:
  if 'Authors, Primary' in new_row.keys():
    authors = new_row['Authors, Primary']
    authors = sub("WSL\(([0-9][0-9]*)\)", r' \1', authors) if authors else None # snip 'WSL' and the parentheses when we have a SAP number + add one space before [LK's specs]
    authors = sub("WSL\(\)", "WSL", authors) if authors else None # snip the parentheses after 'WSL' when we do not have a SAP number [LK's specs] # NOTE: if called with -I, this should _never_ occur
    new_row['Authors, Primary'] = authors
  return new_row



if verbose:
  print "Exporting the dictionary of selected publications to " + (csvfile) + " in csv format..."

with codecs.open(csvfile, "wb", "utf8") as csvfd:
  csvwriter = UnicodeDictWriter(csvfd, (csv_dict[0].keys() if len(csv_dict) > 0 else csv_keys), dialect='excel-tab', callback=row_mod)
  csvwriter.writeheader()
  csvwriter.writerows(csv_dict)
  csvfd.close()

if verbose:
  print "Successfully exported " + str(export_size) + " records."

### export to tagged

tags = OrderedDict()
tags.update({"RT" : "Reference Type"})
tags.update({"SR" : "Source Type"})
tags.update({"ID" : "Reference Identifier"})
tags.update({"A1" : "Primary Authors"})
tags.update({"T1" : "Primary Title"})
tags.update({"JF" : "Periodical Full"})
tags.update({"JO" : "Periodical Abbrev"})
tags.update({"YR" : "Publication Year"})
tags.update({"FD" : "Publication Data,Free Form"})
tags.update({"VO" : "Volume"})
tags.update({"IS" : "Issue"})
tags.update({"SP" : "Start Page"})
tags.update({"OP" : "Other Pages"})
tags.update({"K1" : "Keyword"})
tags.update({"AB" : "Abstract"})
tags.update({"NO" : "Notes"})
tags.update({"A2" : "Secondary Authors"})
tags.update({"T2" : "Secondary Title"})
tags.update({"ED" : "Edition"})
tags.update({"PB" : "Publisher"})
tags.update({"PP" : "Place of Publication"})
tags.update({"A3" : "Tertiary Authors"})
tags.update({"A4" : "Quaternary Authors"})
tags.update({"A5" : "Quinary Authors"})
tags.update({"T3" : "Tertiary Title"})
tags.update({"SN" : "ISSN/ISBN"})
tags.update({"AV" : "Availability"})
tags.update({"AD" : "Author Address"})
tags.update({"AN" : "Accession Number"})
tags.update({"LA" : "Language"})
tags.update({"CL" : "Classification"})
tags.update({"SF" : "Subfile/Database"})
tags.update({"OT" : "Original Foreign Title"})
tags.update({"LK" : "Links"})
tags.update({"DO" : "Document Object Index"})
tags.update({"CN" : "Call Number"})
tags.update({"DB" : "Database"})
tags.update({"DS" : "Data Source"})
tags.update({"IP" : "Identifying Phrase"})
tags.update({"RD" : "Retrieved Date"})
tags.update({"ST" : "Shortened Title"})
tags.update({"U1" : "User 1"})
tags.update({"U2" : "User 2"})
tags.update({"U3" : "User 3"})
tags.update({"U4" : "User 4"})
tags.update({"U5" : "User 5"})
tags.update({"U6" : "User 6"})
tags.update({"U7" : "User 7"})
tags.update({"U8" : "User 8"})
tags.update({"U9" : "User 9"})
tags.update({"U10" : "User 10"})
tags.update({"U11" : "User 11"})
tags.update({"U12" : "User 12"})
tags.update({"U13" : "User 13"})
tags.update({"U14" : "User 14"})
tags.update({"U15" : "User 15"})
tags.update({"UL" : "URL"})
tags.update({"SL" : "Sponsoring Library"})
tags.update({"LL" : "Sponsoring Library Location"})
tags.update({"CR" : "Cited References"})
tags.update({"WT" : "Website Title"})
tags.update({"A6" : "Website Editor"})
tags.update({"WV" : "Website Version"})
tags.update({"WP" : "Date of Electronic Publication"})
tags.update({"OL" : "Output Language"})
tags.update({"PMID" : "PMID"})
tags.update({"PMCID" : "PMCID"})

altkeys = OrderedDict()
altkeys.update({"Reference Identifier" : "ID"})
altkeys.update({"Primary Authors" : "Authors, Primary"})
altkeys.update({"Primary Title" : "Title Primary"})
altkeys.update({"Publication Year" : "Pub Year"})
altkeys.update({"Publication Data,Free Form" : "Pub Date Free Form"})
altkeys.update({"Keyword" : "Keywords"})
altkeys.update({"Secondary Authors" : "Authors, Secondary"})
altkeys.update({"Secondary Title" : "Title Secondary"})
altkeys.update({"Place of Publication" : "Place Of Publication"})
altkeys.update({"Tertiary Authors" : "Authors, Tertiary"})
altkeys.update({"Quaternary Authors" : "Authors, Quaternary"})
altkeys.update({"Quinary Authors" : "Authors, Quinary"})
altkeys.update({"Tertiary Title" : "Title, Tertiary"})
altkeys.update({"Author Address" : "Author/Address"})
altkeys.update({"Subfile/Database" : "Sub file/Database"})
altkeys.update({"Document Object Index" : "DOI"})

def get_tag_content(tag, row):
  missingtags = ["SR", "SL", "LL", "CR", "WT", "A6", "WV", "WP", "OL"]
  if tag in missingtags:
    return None
  key = tags[tag]
  if key in altkeys.keys():
    key = altkeys[key]
  return row[key]

tagged_header_head = """
Refworks Export Tagged Format

Character Set=utf-8

Tag legend
*****
"""

tagged_header_body = "\n".join([k + "=" + tags[k] for k in tags.keys()])

tagged_header_foot = """

*****
Font Attribute Legend
Start Bold = 
End Bold = 
Start Underline = 
End Underline = 
Start Italic = 
End Italic = 
Start SuperScript = 
End SuperScript = 
Start SubScript = 
End SubScript = 

*****
BEGIN EXPORTED REFERENCES




"""

if verbose:
  print "Exporting the dictionary of selected publications to " + (taggedfile) + " in tagged format..."

with codecs.open(taggedfile, "wb", "utf8") as taggedfd:
  taggedfd.write(tagged_header_head)
  taggedfd.write(tagged_header_body)
  taggedfd.write(tagged_header_foot)
  alltags = tags.keys()
  for row in csv_dict:
    for tag in alltags:
      val = get_tag_content(tag, row)
      if val:
        if tag == "A1":
          val = sub("WSL\([0-9]*\)", "", (val if val else ""))
          for a in [(v.strip() if v else "") for v in val.split(";")]:
            taggedfd.write(tag + " " + (a if a else "") + "\n")
        else:
          taggedfd.write(tag + " " + val + "\n")
    taggedfd.write("\n")
  taggedfd.close()

if verbose:
  print "Successfully exported " + str(export_size) + " records."

### write selected publications to a file

if verbose:
  print "Exporting the dictionary of selected publications to " + (selectedfile) + "..."

selected_fd = codecs.open(selectedfile, "w", "utf8")

selected_xml = xmltodict.unparse(in_dict, encoding='utf-8', pretty=True, indent='  ')
del in_dict # we do not need this henceforth

try:
  selected_fd.write(codecs.encode(selected_xml, "utf8"))
finally:
  if verbose:
    print "Successfully exported " + str(export_size) + " records."
selected_fd.close()

### write rejected publications to the output file

if verbose:
  print "Exporting the dictionary of rejected publications to " + (outfile if not tostdout else "standard output") + "..."

if not tostdout:
  out_fd = codecs.open(outfile, "w", "utf8")
else:
  out_fd = outfile

out_xml = xmltodict.unparse(out_dict, encoding='utf-8', pretty=True, indent='  ')
del out_dict # we do not need this henceforth

try:
  out_fd.write(codecs.encode(out_xml, "utf8"))
finally:
  if verbose:
    print "Successfully exported " + str(obtained_size) + " records."
out_fd.close()

exit(0)
