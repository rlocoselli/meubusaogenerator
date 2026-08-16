# Objective
It is a simple service to practice arithmetic progression concepts. It is necessary to install flask as part of this solution in order to creqte service qnd run as a local server.

# Installing Flask
https://flask.palletsprojects.com/en/1.1.x/installation/

# Running application in Power Shell Terminal

$env:FLASK_APP = "ap.py"

python -m flask run

Example: http://127.0.0.1:5000/sumProgression/2/2/2

# Canberra GTFS credentials

The Canberra feed requires credentials from the Transport Canberra developer portal.
Set them only in the process environment; never commit them to this repository:

    export CANBERRA_GTFS_CLIENT_ID='your-client-id'
    export CANBERRA_GTFS_CLIENT_SECRET='your-client-secret'

GitHub Actions should use repository or environment secrets with these exact names.
