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

if not "MERGEDFILEMAKEREXPORT" in in_dict:
  print "Error: Wrong format! Did you parse and merge the original exports first?"
  exit (1)

### create the target dict

if verbose:
  print "Creating the target dictionaries..."

target_size = int(in_dict["MERGEDFILEMAKEREXPORT"]["@ITEMS"])
sourcemtime = in_dict["MERGEDFILEMAKEREXPORT"]["@SOURCEMTIME"]
db_size = int(in_dict["MERGEDFILEMAKEREXPORT"]["@DBSIZE"])
db_name = in_dict["MERGEDFILEMAKEREXPORT"]["@DBNAME"]
claimed_size = int(in_dict["MERGEDFILEMAKEREXPORT"]["@CLAIMEDRECORDS"])

if db_size != target_size:
  print "Warning: Some data seems to be missing (db size is " + str(db_size) + ", but result set size is " + str(target_size) + ")"

in_set = in_dict["MERGEDFILEMAKEREXPORT"]["ITEM"]

in_size = len(in_set)

if in_size != target_size:
  print "Warning: Some data seems to be " + ("in excess" if in_size > target_size else "missing") + " (claimed size is " + target_size + ", but we got " + () + str(len(in_set)) + "rows)"

person_dict = OrderedDict()
publication_dict = OrderedDict()
nosap = []
noname = []
nounit = []
perstomatch = []
pubstomatch = []
person_prefix = 'PER'
publication_prefix = 'PUB'
n = 0
m = 0
nn = 0
for row in in_set:
  if testing:
    if n > 9:
      break
  if not any([(True if "#text" in key else False) for key in row["ATTRIB"]]) and not any([(True if "DATA" in key else False) for key in row["ATTRIB"]]): # skip empty records
#    if not testing: # generates too much noise
#      print "Notice: ITEM NO." + str(n) + " is empty. Skipping..."
    n += 1
    continue
  arraydata = False
  adnr = None
  adnr_a = []
  akey = None
  akey_a = []
  apnr = None
  apnr_a = []
  apers = None
  apers_a = []
  asap = None
  asap_a = []
  afield = None
  afield_a = []
  aplatznr = None
  aplatznr_a = []
  pnn = None
  pnn_a = []
  pvn = None
  pvn_a = []
  ppers = None
  ppers_a = []
  ppnr = None
  ppnr_a = []
  psap = None
  psap_a = []
  pmail = None
  pmail_a = []
  pmailslf = None
  pmailslf_a = []
  pfefa = None
  pfefa_a = []
  pfefaltg = None
  pfefaltg_a = []
  pkost = None
  pkost_a = []
  pedat = None
  pedat_a = []
  padat = None
  padat_a = []
  for key in row["ATTRIB"]:
    if key["@NAME"].find("::Daten.Nr") != -1:
      adnr = key["#text"] if "#text" in key else None
      adnr_a = key["DATA"] if "DATA" in key else []
    elif key["@NAME"].find("::Key") != -1:
      akey = key["#text"] if "#text" in key else None
      akey_a = key["DATA"] if "DATA" in key else []
    elif key["@NAME"].find("::Pers Nr.") != -1:
      if key["@NAME"].find("Pers") == 0:
        ppnr = key["#text"] if "#text" in key else None
        ppnr_a = key["DATA"] if "DATA" in key else []
      else:
        apnr = key["#text"] if "#text" in key else None
        apnr_a = key["DATA"] if "DATA" in key else []
    elif key["@NAME"].find("::Person") != -1:
      if key["@NAME"].find("Pers") == 0:
        ppers = key["#text"] if "#text" in key else None
        ppers_a = key["DATA"] if "DATA" in key else []
      else:
        apers = key["#text"] if "#text" in key else None
        apers_a = key["DATA"] if "DATA" in key else []
    elif key["@NAME"].find("::SAPNr") != -1:
      if key["@NAME"].find("Pers") == 0:
        psap = key["#text"] if "#text" in key else None
        psap_a = key["DATA"] if "DATA" in key else []
      else:
        asap = key["#text"] if "#text" in key else None
        asap_a = key["DATA"] if "DATA" in key else []
    elif key["@NAME"].find("::Field") != -1:
      afield = key["#text"] if "#text" in key else None
      afield_a = key["DATA"] if "DATA" in key else []
    elif key["@NAME"].find("::PlatzNr.") != -1 or key["@NAME"].find("::Platznr.") != -1:
      aplatznr = key["#text"] if "#text" in key else None
      aplatznr_a = key["DATA"] if "DATA" in key else []
    elif key["@NAME"].find("::Name") != -1:
      pnn = key["#text"] if "#text" in key else None
      pnn_a = key["DATA"] if "DATA" in key else []
    elif key["@NAME"].find("::Vorname") != -1:
      pvn = key["#text"] if "#text" in key else None
      pvn_a = key["DATA"] if "DATA" in key else []
    elif key["@NAME"].find("::Email") != -1 and not key["@NAME"].endswith(" SLF"):
      pmail = key["#text"] if "#text" in key else None
      pmail_a = key["DATA"] if "DATA" in key else []
    elif key["@NAME"].find("::Email SLF") != -1:
      pmailslf = key["#text"] if "#text" in key else None
      pmailslf_a = key["DATA"] if "DATA" in key else []
    elif key["@NAME"].find("::FeFa") != -1 and not key["@NAME"].endswith("Ltg"):
      pfefa = key["#text"] if "#text" in key else None
      pfefa_a = key["DATA"] if "DATA" in key else []
    elif key["@NAME"].find("::FeFaLtg") != -1:
      pfefaltg = key["#text"] if "#text" in key else None
      pfefaltg_a = key["DATA"] if "DATA" in key else []
    elif key["@NAME"].find("::Kostenstelle") != -1:
      pkost = key["#text"] if "#text" in key else None
      pkost_a = key["DATA"] if "DATA" in key else []
    elif key["@NAME"].find("::Eintrittsdatum") != -1:
      pedat = key["#text"] if "#text" in key else None
      pedat_a = key["DATA"] if "DATA" in key else []
    elif key["@NAME"].find("::Austrittsdatum") != -1:
      padat = key["#text"] if "#text" in key else None
      padat_a = key["DATA"] if "DATA" in key else []
    else:
      print "Warning: Found unexpected key '" + key["@NAME"] + "' in ITEM NO." + str(n)
  avars = OrderedDict({'adnr' : adnr, 'akey' : akey, 'apnr' : apnr, 'apers' : apers, 'asap' : asap, 'afield' : afield, 'aplatznr' : aplatznr, 'pnn' : pnn, 'pvn' : pvn, 'ppers' : ppers, 'ppnr' : ppnr, 'psap' : psap, 'pmail' : pmail, 'pmailslf' : pmailslf, 'pfefa' : pfefa, 'pfefaltg' : pfefaltg, 'pkost' : pkost, 'pedat' : pedat, 'padat' : padat})
  mvars = OrderedDict({'adnr' : adnr_a, 'akey' : akey_a, 'apnr' : apnr_a, 'apers' : apers_a, 'asap' : asap_a, 'afield' : afield_a, 'aplatznr' : aplatznr_a, 'pnn' : pnn_a, 'pvn' : pvn_a, 'ppers' : ppers_a, 'ppnr' : ppnr_a, 'psap' : psap_a, 'pmail' : pmail_a, 'pmailslf' : pmailslf_a, 'pfefa' : pfefa_a, 'pfefaltg' : pfefaltg_a, 'pkost' : pkost_a, 'pedat' : pedat_a, 'padat' : padat_a})
  if any(avars.values()):
    if any(v != [] for v in mvars.values()):
      print "Error: ITEM NO." + str(n) + " has single _and_ multiple fields! Cannot recover!"
      exit(1)
  else:
    arraydata = True
    for k in mvars.keys():
      if len(mvars[k]) == 0:
        mvars[k] = [None for kk in range(max([len(v) for v in mvars.values()]))]
  if arraydata and min([len(v) for v in mvars.values()]) != max([len(v) for v in mvars.values()]):
    print "Error: ITEM NO." + str(n) + " has inconsistent data length!"
    exit(1)
  if not arraydata:
    for k in avars.keys():
      mvars[k] = [avars[k]]
  arraydatalen = len(mvars['adnr'])
  for j in range(arraydatalen):
    adnr = mvars['adnr'][j]
    akey = mvars['akey'][j]
    apnr = mvars['apnr'][j]
    apers = mvars['apers'][j]
    asap = mvars['asap'][j]
    afield = mvars['afield'][j]
    aplatznr = mvars['aplatznr'][j]
    pnn = mvars['pnn'][j]
    pvn = mvars['pvn'][j]
    ppers = mvars['ppers'][j]
    ppnr = mvars['ppnr'][j]
    psap = mvars['psap'][j]
    pmail = mvars['pmail'][j]
    pmailslf = mvars['pmailslf'][j]
    pfefa = mvars['pfefa'][j]
    pfefaltg = mvars['pfefaltg'][j]
    pkost = mvars['pkost'][j]
    pedat = mvars['pedat'][j]
    padat = mvars['padat'][j]
    if ppnr != apnr:
      if not ppnr and apnr:
        ppnr = apnr
        print "Notice: Recovered 'Pers Nr.' \"" + ppnr + "\" for ITEM NO." + str(n) + ". Continuing..."
      else:
        print "Warning: Possible mismatch during merger in ITEM NO." + str(n) + " ('Pers Nr.': \"" + (apnr if apnr else "None") + "\" vs. \"" + (ppnr if ppnr else "None") + "\")"
    if ppers != apers:
      print "Warning: Possible mismatch during merger in ITEM NO." + str(n) + " ('Person': \"" + (apers if apers else "None") + "\" vs. \"" + (ppers if ppers else "None") + "\")"
    if psap != asap and not (psap and psap[0] == "0" and psap[1:] == asap):
      print "Warning: Possible mismatch during merger in ITEM NO." + str(n) + " ('SAPNr': \"" + (asap if asap else "None") + "\" vs. \"" + (psap if psap else "None") + "\")"
    if not ppnr and not apnr:
      print "Error: ITEM NO." + str(n) + " has no 'Pers Nr.' but is not empty!"
      exit(1)
    pkey = None
    if akey:
      pkey = akey.split()
    else:
      print "Warning: ITEM NO." + str(n) + " has no linkeage to any publication, but is non empty!"
    if pkey and (((pkey[1] != aplatznr and mvars['apnr'][mvars['aplatznr'].index(aplatznr)] != ppnr) if aplatznr else (pkey[1] != ppnr)) or pkey[0] != adnr):
      print "Warning: Mismatching key for ITEM NO." + str(n) + " (expected [" + (aplatznr if aplatznr else ppnr) + ":" + adnr + "], got [" + pkey[1] + ":" + pkey[0] + "])! Matching with publications will be corrupted!"
    if pkey and aplatznr:
      pkey[1] = mvars['apnr'][mvars['aplatznr'].index(aplatznr)]
    if person_prefix + ppnr in person_dict:
      tpnr = person_dict[person_prefix + ppnr]["PERSNO"]
      if tpnr != ppnr:
        tpnr = tpnr if tpnr else "None"
        print "Error: Data is corrupt! (Stopping at ITEM NO." + str(n) + " for 'Pers Nr.' \"" + ppnr + "\", since we had recorded \"" + tpnr + "\""
        exit(1)
      tsap = person_dict[person_prefix + ppnr]["SAPNO"]
      if tsap != psap:
        tsap = tsap if tsap else "None"
        print "Warning: Inconsistent data at ITEM NO." + str(n) + " (had 'SAPNr' \"" + tsap + "\", but now saw \"" + (psap if psap else "None") + "\""
      tnn = person_dict[person_prefix + ppnr]["FAMILYNAME"]
      if tnn != pnn:
        tnn = tnn if tnn else "None"
        print "Warning: Inconsistent data at ITEM NO." + str(n) + " (had 'Name' \"" + tnn + "\", but now saw \"" + (pnn if pnn else "None") + "\""
      tvn = person_dict[person_prefix + ppnr]["GIVENNAME"]
      if tvn != pvn:
        tvn = tvn if tvn else "None"
        print "Warning: Inconsistent data at ITEM NO." + str(n) + " (had 'Vorname' \"" + tvn + "\", but now saw \"" + (pvn if pvn else "None") + "\""
      tpers = person_dict[person_prefix + ppnr]["FULLNAME"]
      if tpers != ppers:
        tpers = tpers if tpers else "None"
        print "Warning: Inconsistent data at ITEM NO." + str(n) + " (had 'Person' \"" + tpers + "\", but now saw \"" + (ppers if ppers else "None") + "\""
      tmail = person_dict[person_prefix + ppnr]["EMAIL"]
      if tmail != pmail:
        tmail = tmail if tmail else "None"
        print "Warning: Inconsistent data at ITEM NO." + str(n) + " (had 'Email' \"" + tmail + "\", but now saw \"" + (pmail if pmail else "None") + "\""
      tmailslf = person_dict[person_prefix + ppnr]["EMAILOTHER"]
      if tmailslf != pmailslf:
        tmailslf = tmailslf if tmailslf else "None"
        print "Warning: Inconsistent data at ITEM NO." + str(n) + " (had 'Email SLF' \"" + tmailslf + "\", but now saw \"" + (pmailslf if pmailslf else "None") + "\""
      tfefa = person_dict[person_prefix + ppnr]["UNIT"]
      if tfefa != pfefa:
        tfefa = tfefa if tfefa else "None"
        print "Warning: Inconsistent data at ITEM NO." + str(n) + " (had 'FeFa' \"" + tfefa + "\", but now saw \"" + (pfefa if pfefa else "None") + "\""
      tfefaltg = person_dict[person_prefix + ppnr]["UNITBOSS"]
      if tfefaltg != pfefaltg:
        tfefaltg = tfefaltg if tfefaltg else "None"
        print "Warning: Inconsistent data at ITEM NO." + str(n) + " (had 'FeFaLtg' \"" + codecs.encode(tfefaltg, "utf8") + "\", but now saw \"" + (pfefaltg if pfefaltg else "None") + "\""
      tkost = person_dict[person_prefix + ppnr]["ACCOUNTNO"]
      if tkost != pkost:
        tkost = tkost if tkost else "None"
        print "Warning: Inconsistent data at ITEM NO." + str(n) + " (had 'Kostenstelle' \"" + tkost + "\", but now saw \"" + (pkost if pkost else "None") + "\""
      tedat = person_dict[person_prefix + ppnr]["STARTDATE"]
      if tedat != pedat:
        tedat = tedat if tedat else "None"
        print "Warning: Inconsistent data at ITEM NO." + str(n) + " (had 'Eintrittsdatum' \"" + tedat + "\", but now saw \"" + (pedat if pedat else "None") + "\""
      tadat = person_dict[person_prefix + ppnr]["ENDDATE"]
      if tadat != padat:
        tadat = tadat if tadat else "None"
        print "Warning: Inconsistent data at ITEM NO." + str(n) + " (had 'Austrittsdatum' \"" + tadat + "\", but now saw \"" + (padat if padat else "None") + "\""
      if pkey and any([(pub == pkey[0]) for pub in person_dict[person_prefix + ppnr]["PUBLINK"]]):
        print "Warning: Possible data corruption in ITEM NO." + str(n) + "! The key [" + pkey[1] + ":" + pkey[0] + "] was already stored in the persons dictionary..."
      else:
        if testing and n < 100 and pkey:
          print person_dict[person_prefix + ppnr]["PUBLINK"], "[" + pkey[1] + ":" + pkey[0] + "]"
        person_dict[person_prefix + ppnr]["PUBLINK"].append(OrderedDict([('@POS', aplatznr if aplatznr else '0'), ('#text', pkey[0])]))
      if testing and m < 50:
        print pkey, person_dict[person_prefix + ppnr]["PUBLINK"]
    else:
      p = OrderedDict()
      p.update({"PERSNO" : ppnr})
      if not psap or psap == '':
        nosap.append(ppnr)
        print "Warning: Person no." + str(ppnr) + (" (\"" + apers + "\")" if apers and apers != '' else "") + " has no SAP number."
      p.update({"SAPNO" : psap})
      if not pnn or not pvn or not ppers or pnn == '' or pvn == '' or ppers == '':
        noname.append(ppnr)
        print "Warning: Person no." + str(ppnr) + (" (\"" + apers + "\")" if apers and apers != '' else (( " (\"" + pvn + (" " if pnn else "\")") if pvn else "") + (("" if pvn else " (\"") + pnn + "\")" if pnn else ""))) + " has no or incomplete name information."
      p.update({"FAMILYNAME" : pnn})
      p.update({"GIVENNAME" : pvn})
      p.update({"FULLNAME" : ppers})
      p.update({"EMAIL" : pmail})
      p.update({"EMAILOTHER" : pmailslf})
      if not pfefa or pfefa == '':
        nounit.append(ppnr)
        print "Warning: Person no." + str(ppnr) + (" (\"" + apers + "\")" if apers and apers != '' else "") + " has no associated unit."
      p.update({"UNIT" : pfefa})
      p.update({"UNITBOSS" : pfefaltg})
      p.update({"ACCOUNTNO" : pkost})
      p.update({"STARTDATE" : pedat})
      p.update({"ENDDATE" : padat})
      p.update({"PUBLINK" : [OrderedDict([('@POS', aplatznr if aplatznr else '0'), ('#text', pkey[0] if pkey else None)])]})
      person_dict.update({person_prefix + ppnr : p})
      if testing and m < 50:
        print pkey, person_dict[person_prefix + ppnr]["PUBLINK"]
      m += 1
    perstomatch.append(ppnr)
    if pkey:
      if publication_prefix + pkey[0] in publication_dict:
        if any([(pers == pkey[1]) for pers in publication_dict[publication_prefix + pkey[0]]["PERSLINK"]]):
          print "Warning: Possible data corruption in ITEM NO." + str(n) + "! The key [" + pkey[1] + ":" + pkey[0] + "] was already stored in the publications dictionary..."
        else:
          publication_dict[publication_prefix + pkey[0]]["PERSLINK"].append(OrderedDict([('@POS', aplatznr if aplatznr else '0'), ('#text', pkey[1])]))
      else:
        publication_dict.update({publication_prefix + pkey[0] : OrderedDict({"PERSLINK" : [OrderedDict([('@POS', aplatznr if aplatznr else '0'), ('#text', pkey[1])])]})})
        nn += 1
      pubstomatch.append(pkey[0])
  n += 1

if n != target_size:
  print "Warning: Expected " + str(target_size) + " rows, but found " + ("only " if n < target_size else "") + str(n) + "!"

if len(noname) > 0:
  print "Warning: The following " + str(len(set(noname))) + " persons have no or incomplete name information: " + ", ".join(sorted(set(noname), key=lambda t: int(t)))
if len(nosap) > 0:
  print "Warning: The following " + str(len(set(nosap))) + " persons have no SAP number: " + ", ".join(sorted(set(nosap), key=lambda t: int(t)))
if len(nounit) > 0:
  print "Warning: The following " + str(len(set(nounit))) + " persons have no associated unit: " + ", ".join(sorted(set(nounit), key=lambda t: int(t)))
print "Info: You will need to match " + str(len(perstomatch)) + " persons in " + str(len(set(pubstomatch))) + " publications."
print "Info: List of " + str(len(set(perstomatch))) + " unique persons to match: " + ", ".join(sorted(set(perstomatch), key=lambda t: int(t)))
print "Info: List of " + str(len(set(pubstomatch))) + " unique publications to match: " + ", ".join(sorted(set(pubstomatch), key=lambda t: int(t)))

if verbose:
  print "Successfully created the target dictionaries for " + str(m) + " unique persons and " + str(nn) + " publications (obtained from " + str(n) + " records)."

### sort the dictionary

if verbose:
  print "Sorting the dictionaries..."

person_dict_sorted = OrderedDict()
person_dict_sorted.update({"@ITEMS" : str(m)})
person_dict_sorted.update(sorted(person_dict.items(), key=lambda t: int(t[0][len(person_prefix):])))
publication_dict_sorted = OrderedDict()
publication_dict_sorted.update({"@ITEMS" : str(nn)})
publication_dict_sorted.update(sorted(publication_dict.items(), key=lambda t: int(t[0][len(publication_prefix):])))

out_set = OrderedDict()
out_set.update({"@TIMESTAMP" : timestamp})
out_set.update({"@SOURCEMTIME" : sourcemtime})
out_set.update({"@PERSITEMS" : str(m)})
out_set.update({"@PUBITEMS" : str(nn)})
out_set.update({"@DBNAME" : db_name})
out_set.update({"@DBSIZE" : str(db_size)})
out_set.update({"@ORIGINALRECORDS" : str(n)})
out_set.update({"@CLAIMEDRECORDS" : str(claimed_size)})
out_set.update({"PERSONS" : person_dict_sorted})
out_set.update({"PUBLICATIONS" : publication_dict_sorted})

out_dict = OrderedDict({"FILEMAKEREXPORTPERSONLINKS" : out_set})

if verbose:
  print "...done"

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
    print "Successfully exported " + str(m) + " + " + str(nn) + " records."
out_fd.close()

exit (0)
