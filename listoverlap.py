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
import sys
from optparse import OptionParser

### some constants

STDIN   = sys.stdin  #'/dev/stdin'
STDOUT  = sys.stdout #'/dev/stdout'

### re-direct all output to stderr

oldstdout = sys.stdout
sys.stdout = sys.stderr

### parse the command line

usage = "Usage: %prog [-v]"
parser = OptionParser(usage)
parser.add_option("-v", "--verbose",
  action = "store_true", dest = "verbose", default = False,
  help = "Show what I'm doing [default=false]")
(opts, args) = parser.parse_args()

verbose = opts.verbose

### read in two lines from stdin

line1 = STDIN.readline().strip()
line2 = STDIN.readline().strip()
rest = STDIN.read()

### assure there is no more data to read

if rest and rest != "":
  print "Error: Expected only two lines!"
  exit(1)

### generate the two sets of integers

set1 = set(line1.split(", "))
set2 = set(line2.split(", "))
if verbose:
  print "Info: Comparing two sets of integers with " + str(len(set1)) + ", resp. " + str(len(set2)) + ", elements."
if not all([str(int(v)) == v for v in set1]):
  print "Error: First line does not contain only integers"
  exit(1)
if not all([str(int(v)) == v for v in set2]):
  print "Error: Second line does not contain only integers"
  exit(1)

### print the subset that is contained in both sets, if any

overlap1 = (set1 - (set1 - set2))
overlap2 = (set2 - (set2 - set1))

if overlap1 != overlap2:
  print "Error: The weirdest thing occurred! Exiting in shame..."
  exit(1)

if verbose:
  if overlap1 == set([]):
    print "Info: There is no overlap."
  else:
    overlap_length = len(overlap1)
    print "Info: There " + ("is" if overlap_length == 1 else "are") + " " + str(overlap_length) + " integer" + ("" if overlap_length == 1 else "s") + " present in both sets."

STDOUT.write(", ".join(sorted(overlap1, key=lambda t: int(t))))
