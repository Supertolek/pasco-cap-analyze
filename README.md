# PASCAPALYZE

This is a python script that reads in a Pasco Capstone experiment (.cap) file created by Pasco Capstone, and extracts the raw data from that file.

## How it works

The .cap files are actually zip files, containing the index `main.xml` and 
a directory full of data files. The data files contain a single array with
elements 12 bytes long; the last 8 bytes of those elements can be interpreted
as a 64-bit-long double. `main.xml` is sufficiently self-documenting that these
data files can be mapped to values.

## Limitations

Have only run this program on three different files; may not handle everything.  
Maybe for later...

## How to use pasco-capstone-analyse

The easiest way to use this python programm is to:
- download it
- open a command line terminal in the folder where the file `index.py` is
- run `py index.py "path/to/capstone/file" [options]` _(if `py`doesn't work, try with `python`, `python3` or check your python installation)_

There are 2 main options:
- `-to-csv "output_file.csv"` creates a csv file containing the data from the PASCO Capstone file.
- `-plot` shows a graph of the data from the file using matplotlib.

If you use the `-to-csv` option, you can:
- specify a decimal separator with `-dec ","` _(you can replace the coma with whatever separator you want to use) (I implemented that because I'm french and I use coma)_
- specify a cell separator with `-sep ";"` _(you can replace the semicolon with whatever separator you want to use)_

If you want a more practical way to use pasco-capstone-analyze:
- Make sure you are on the windows platform with an administrator account
- Search for "Environment variables" and open it
- Go to the "Advanced system settings" tab
- Click on the "Environment variables" at the bottom
- On the top list, select "Path" and click on "edit"
- Click on "New" and paste the path to your "pasco-capstone-analyze" folder
- Select "Ok", "Ok", and "Ok" to close the "Environment variables" windows
Then, to use pasco-capstone-analyze:
- Open a command line interpreter
- Execute `pascapalyze "file_path"` with the same arguments as with the first way

For now, there isn't much more, but you can contribute, or contact me:
- discord @thomaslequere
- mail [lequereth@gmail.com](mailto:lequereth@gmail.com)

## Thanks

Thanks to [mstoeckl](https://github.com/mstoeckl) for making the original project (https://github.com/mstoeckl/pascapalyze).

Thanks to everyone willing to contribute and to add support for other files format or functionnalities ❤️.

pasco-capstone-analyze by Thomas Le Quéré is marked with CC0 1.0.  
To view a copy of this license, visit https://creativecommons.org/publicdomain/zero/1.0/