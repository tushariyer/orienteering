# Seasonal Orienteering
## by Tushar Iyer


This is a project on using the A* Heuristic Search to generate optimal paths for orienteering during the different seasons.

In Orienteering, players are given a map which contains information on terrain, elevation and a set of points to visit (In a particular order). This project uses maps representing Mendon Ponds Park.


# Installation and Run
 - Ensure that you have `python` installed
 - Run the program with `python orienteering terrain.png, mpp.txt <path-colour> <path-file> <season> <[optional] output>`
	 - `terrain.png` is the terrain map
	 - `mpp.txt` is the elevation file
	 - `<path-colour>` is either `red`, `white`, or `brown`.
	 - `<path-file>` is either `red.txt`, `white.txt` or `brown.txt` depending on the path you want.
	 - `<season>` is one of the four seasons.
	 - `<output>` is an optional argument like `> red-output.txt` to pipe the output to a separate text file.
 - In addition to an optional output text file, an output image is always generated with the path drawn on top.
