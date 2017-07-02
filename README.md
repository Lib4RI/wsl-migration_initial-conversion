# WSL migration --- initial conversion

A toolchain to convert our FileMaker XML exports of WSL publication data to RefWorks (tab-separated) CSV and XML.

## Introduction

This is a set of tools that was used to convert FileMaker XML into RefWorks CSV and XML. It was written in order to be able to recycle the workflow we used to migrate the publication data of Eawag and Empa from RefWorks to our new institutional repository [DORA](https://www.dora.lib4ri.ch). It takes care of keeping the linkage between author names in the publication metadata and the corresponding author objects. Also, it tries to analyse the linkage quality, giving suggestions what metadata should be reviewed.

**NOTE: This repository will not be maintained!**

## CAVEAT

THIS IS OUTDATED WORK!!! DURING THE YEAR 2017, IT SEEMED TO HAVE DONE ITS JOB FOR US, BUT IT IS NOT ALWAYS CODED IN THE CORRECT WAY. DUE TO THE FINALISATION OF THE WSL MIGRATION, THIS CODE IS NO LONGER BEING USED AND WILL NOT EVER BE UPDATED. YOU SHOULD PROBABLY NOT USE THIS CODE YOURSELF, AS IT MIGHT NOT WORK FOR YOU OR EVEN BREAK YOUR SYSTEM (SEE ALSO 'LICENSE'). UNDER NO CIRCUMSTANCES WHATSOEVER ARE WE TO BE HELD LIABLE FOR ANYTHING. YOU HAVE BEEN WARNED.

## Requirements (@TODO: make the dependency list more explicit)

This software was successfully run on x86_64 GNU/Linux using
* [`python`](https://www.python.org) (2.7.9)
* _possibly other tools not present in a default installation_

## Installation & Usage (@TODO: be more explicit)

**CAVEAT: This, obviously, assumes our own FileMaker setup. It is almost guaranteed that your tables will differ and that the code will not work!!!**

1. Clone this repository
2. Make sure the two directories `DATA` and `EXPORTS` are present
3. Place the **complete** FileMaker XML exports in the `DATA` folder
    The following files are expected (the `*` can be anything, here; the most recent files will be used):
    1. `Autoren*.xml`: the linkage table of first authors
    2. `Coautoren*.xml`: the linkage table of co-authors
    3. `Editoren*.xml`: the linkage table of editors
    4. `Journals*.xml`: the journal list
    5. `PersAutor*.xml`: the author objects
    6. `PersCoautor*.xml`: the co-author objects
    7. `PersEditor*.xml`: the editor objects
    8. `PublikationenWSL*.xml`: the list of publications
4. Review the filters (the `F*.xml` files; see below)
5. Run
    ```
    ./filemaker2exports.sh -I -v -o EXPORTS/ -c
    ```
6. In order to review all major warnings, run
    ```
    ./alllog2checkalllog.sh -i EXPORTS/ -o EXPORTS/
    ```
    which generates the `all.log.checkall` file in `EXPORTS` combining
    1. `F*.log.checkambiguous`: ambiguous names
    2. `F*.log.checkincomplete`: incomplete names
    3. `F*.log.checkinitials`: inconsistent intials
    4. `F*.log.checkissn`: wrong issns
    5. `F*.log.checkmissing`: unlinked names
    6. `F*.log.checknames`: inconsistent names
    7. `F*.log.checknoauthors`: missing authors
    8. `F*.log.checkpos`: wrong positions
    9. `F*.log.checkrematch`: multiple name matches
    10. `F*.log.checksap`: mismatching sap number
7. (<i>@OPTIONAL</i>) Review the original `F*.log` files in `EXPORTS` for additional information (**Note**: They are pretty verbose)
8. If you are not satisfied with the number/kind of warnings, correct the metadata in FileMaker and start over

## Files in this repository (@TODO: be _way_ more explicit)

### `DATA/.gitignore`

This file has been set to only contain itself within the `DATA` subdirectory:
```
/*
!/.gitignore
```

### `EXPORTS/.gitignore`

This file has been set to only contain itself within the `EXPORTS` subdirectory:
```
/*
!/.gitignore
```

### `.gitignore`

This file has been set to only contain the files currently in this repository. Specifically, it contains:
```
/*
!/DATA
/DATA/*
!/DATA/.gitignore
!/EXPORTS
/EXPORTS/*
!/EXPORTS/.gitignore
!/.gitignore
!/README.md
!/LICENSE
!/alllog2checkalllog.sh
!/filemaker2exports.sh
!/filemaker2refworks.py
!/filemakerparsexml.py
!/flattenpersons.py
!/listoverlap.py
!/log2check.sh
!/mergewithpers.py
!/F*.xml
```

### `README.md`

This file...

### `LICENSE`

The license under which this set of tools is distributed:
```
Copyright (c) 2016, 2017 d-r-p (Lib4RI) <d-r-p@users.noreply.github.com>

Permission to use, copy, modify, and distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
```

### `alllog2checkalllog.sh`

A helper shell script that combines, for each category (`ambiguous`, `incomplete`, `initials`, `issn`, `missing`, `names`, `noauthors`, `pos`, `rematch`, `sap`), all the `EXPORTS/F*.log.check*` files into one (`all.log.checkall`) for easier analysis (see also `log2check.sh` below). The script knows four switches: `-h` for a short help message, `-v` for verbose output, `-i INDIR` to specify the input directory (defaults to `.`) and `-o OUTDIR` to specify the output directory (defaults to `.`).

### `filemaker2exports.sh`

This is the main helper script (see Usage above). Its purpose is to automatically call other scripts based on given data and filters. It tries its best to pre-parse the data and process the filters only once (not all scenarios have been tested, though), but it is safer to run it on a "clean" export (changes and additions should have been tracked in a much smarter way). A key feature of the way it processes filters is that they can be chained (i.e. the remainder of some filter can be the input set of the next) --- this not only increases performance, but also avoids duplicates. The script has several options (see the script itself or run `filemaker2exports.sh -h` for a short description) to account for different possible ways of processing the data. We ended up using only one set of switches (see Usage above).

### `filemaker2refworks.py`

This is the python script doing the main work (i.e. exporting the pre-parsed data into the wanted formats according to a specified filter). In verbose mode, it tries to warn the user about inconsistencies in the data, especially regarding the linkage of author names to author objects. Since several common mistakes in the data became apparent only through time, and certain re-specifications had to be accommodated a posteriori, several parts of this program were re-written independently, even though a re-design would have been more adequate (especially in regard to performance). In addition, both data formats (input and output) are very specific to our own use case, and it might prove difficult to adapt the program to different data structures (we are well aware that our way of parsing the data is not the most elegant). This is, by far, the biggest part of this tool chain, but also, probably, the least re-usable one. Type `python filemaker2exports.py -h` for a short help message on how to use it.

### `filemakerparsexml.py`

This is the first of three helper python scripts used to pre-parse the raw export data from FileMaker (see also `flattenpersons.py` and  `mergewithpers.py` below) --- type `python filemakerparsexml.py -h` for a short help message. It suffers heavily from utf8-problems and might not perform as expected on all possible input data. It does, however, try to normalise unicode.

### `flattenpersons.py`

This is the third of three helper python scripts used to pre-parse the raw export data from FileMaker (see also `filemakerparsexml.py` before and `mergewithpers.py` below) --- type `python flattenpersons.py -h` for a short help message.

### `listoverlap.py`

This is a _very_ simple python script that compares two comma (& space) separated input lines of integers for overlap (i.e. common integers). It is used by `filemaker2exports.sh` (see before) to check for consistency between the set of selected and the set of rejected publications (basically as a safety for the filter implementation).

### `log2check.sh`

This is a small helper script that will extract the most important warnings of a `filemaker2refworks.py` run, separating the warnings into different categories (see the list of generated files exhibited in the Usage section above).

### `mergewithpers.py`

This is the second of three helper python scripts used to pre-parse the raw export data from FileMaker (see also `filemakerparsexml.py` and `flattenpersons.py` above) --- type `python mergewithpers.py -h` for a short help message.


### `F*.xml`

These are the filters we used in order to pre-categorise publications. Since FileMaker and DORA use fairly different publication types and the categorisation criteria have been updated for DORA, this approach of pre-filtering proved only partially useful. Filters are (very simple) XML files of the following format (see also any filter for this short explanation):
```xml
<?xml version="1.0" encoding="utf8"?>
<FILEMAKERTOREFWORKSSETUP>
  <REFERENCETYPE>Publication Type</REFERENCETYPE>
  <!--
    REMARKS REGARDING <FILTEREXPRESSION>-tag:
    - strings that exist as field-names in FileMaker will be
      replaced by their values
    - those values, if not set (i.e., having a value of None), will be
      replaced by ''
    - if the final expression eval()-uates to True, the publication will be
      included
    - otherwise the publication will be discarded
    - there is an optional attribute "EXCLUDEPERSONMATCHES" that can have
      as value a comma-separated list from the set
      {'AuthorsOnly', 'EditorsOnly', 'AuthorsAndEditors',
       'NeitherAuthorsNorEditors'}:
      Publications that have matches in the (co-)authors,
      resp. editor lists alone, or both or neither,
      are then excluded from the list to export.
    EXAMPLES:
    - <FILTEREXPRESSION>True</FILTEREXPRESSION>
    - <FILTEREXPRESSION EXCLUDEPERSONMATCHES="EditorsOnly, AuthorsAndEditors, NeitherAuthorsNorEditors">'Jl.Revie' == 'x' and 'Repository Export' != 'nein'</FILTEREXPRESSION>
  -->
  <FILTEREXPRESSION>True</FILTEREXPRESSION>
</FILEMAKERTOREFWORKSSETUP>
```

## @TODO (**will _not_ be done**)

* Use `ElementParser` rather than `xmltodict` for parsing XMLs, as `xmltodict` does not seem to be easily available on all platforms


<br/>
> _This document is Copyright &copy; 2017 by d-r-p (Lib4RI) `<d-r-p@users.noreply.github.com>` and licensed under [CC&nbsp;BY&nbsp;4.0](https://creativecommons.org/licenses/by/4.0/)._