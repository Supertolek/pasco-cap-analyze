# PASCAPALYZE

This is a script that reads in a .cap experiment file created by Pasco Capstone,
and extracts the raw data from that file.

## How it works
The .cap files are actually zip files, containing the index `main.xml` and 
a directory full of data files. The data files contain a single array with
elements 12 bytes long; the last 8 bytes of those elements can be interpreted
as a 64-bit-long double. `main.xml` is sufficiently self-documenting that these
data files can be mapped to values.

## Limitations
Have only run this program on three different files; may not handle everything.

## How to use pasco-capstone-analyse

The easiest way to use this programm is to:
- download it
- open a command line terminal in the folder where the file `index.py` is
- run `py index.py "path/to/capstone/file" [options]`

There are 2 main options:
- `-to-csv "output_file.csv"` creates a csv file containing the data from the PASCO Capstone file.
- `-plot` shows a graph of the data from the file.

If you use the `-to-csv` option, you can:
- specify a decimal separator with `-dec ","` (you can replace the coma with whatever separator you want to use) (I implemented that because I'm french and I use coma)
- specify a cell separator with `-sep ";"` (you can replace the semicolon with whatever separator you want to use)

For now, there isn't much more, but you can contribute, or contact me:
- discord @thomaslequere
- mail [lequereth@gmail.com](mailto:lequereth@gmail.com)

## Thanks

Thanks to [mstoeckl](https://github.com/mstoeckl) for making the original project (https://github.com/mstoeckl/pascapalyze).

Thanks to everyone willing to contribute and to add support for other files format or functionnalities ❤️.

pasco-capstone-analyze by Thomas Le Quéré is marked with CC0 1.0.  
To view a copy of this license, visit https://creativecommons.org/publicdomain/zero/1.0/