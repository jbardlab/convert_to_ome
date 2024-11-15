# convert_to_ome
This is a set of scripts to convert nd2 and czi files to ome files.

It is based off of BioIO, a python library for reading and writing bio-formats (https://github.com/bioio-devs/bioio).

It is meant to be packaged as a docker container, using pixi to build the docker (ala https://tech.quantco.com/blog/pixi-production).

It can also be run as a pixi installation (pixi install, then pixi run python convert_to_ome.py).

To build the docker container, run the following command:
docker buildx build --platform linux/amd64 -t convert_to_ome .   

