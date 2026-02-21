# OpenGridGen

A flask-based web utility for interactively generating standard gridfinity baseplates/containers

# Prerequisites

- Python 3.10 - 3.12 (Python 3.13 is not yet supported due to CadQuery dependencies)

# Getting Started

1. Clone & Start the server
```
# git clone https://github.com/loganrf/OpenGridGen/
# cd OpenGridGen
# python3 -m venv .venv
# source .venv/bin/activate
# pip install -r requirements.txt
# flask run
```

2. Open the app in your browser at 127.0.0.1:4242

# Usage

The menu along the left side of the screen includes the following modules:

- Box Generator: Allows you to generate a box by specifying width, length, height in gridfinity units
- Baseplate Generator: Allows you to generate a baseplate by specifying width and length

For each of the above, you can export as a step file or stl for download and view the bounding box dimensions of the resulting design in mm

In the upper right you will find "Settings". Here you can tweak the base dimensions of your gridfinity design for custom setups.

# Acknowledgements

This project makes use of the following open source libraries:

- [Flask](https://flask.palletsprojects.com/) - The Python micro framework for building web applications.
- [cq-gridfinity](https://github.com/michaelgale/cq-gridfinity) - A python library to build parameterized gridfinity compatible objects, based on [CadQuery](https://github.com/CadQuery/cadquery).
