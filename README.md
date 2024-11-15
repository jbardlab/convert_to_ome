# convert_to_ome
This is a set of scripts to convert nd2 and czi files to ome files.

It is based off of BioIO, a python library for reading and writing bio-formats (https://github.com/bioio-devs/bioio).

It is meant to be packaged as a docker container, using pixi to build the docker (ala https://tech.quantco.com/blog/pixi-production).

It can also be run as a pixi installation (pixi install, then pixi run python convert_to_ome.py).

To build the docker container locally, run the following command:
docker buildx build --platform linux/amd64 -t convert_to_ome .   

To build the docker container and push to GHCR, run the following command:
First followed instructions here to create a personal access token to push to GHCR:
https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry
Stored token on my mac computer:
$ export CR_PAT=YOUR_TOKEN
$ echo $CR_PAT | docker login ghcr.io -u jbard --password-stdin

Then run the following command:
$ docker buildx create --use
$ docker buildx build --platform linux/amd64 -t ghcr.io/jbardlab/convert_to_ome:latest --push .

To pull the docker container from GHCR, run the following command:
First make sure you are logged into GHCR: (see above)
Then run the following command:

$ docker pull ghcr.io/jbardlab/convert_to_ome:latest

On a mac, you have to run in amd64 mode (because the arm64 version didn't run):
$ docker pull --platform linux/amd64 ghcr.io/jbardlab/convert_to_ome:latest

To run the docker container, run the following command:
$ docker run --rm -v "data_folder":/data ghcr.io/jbardlab/convert_to_ome:v0.1 python convert_to_ome.py -d "/data" -o                                 