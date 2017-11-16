
Name: Luke Gerhart
Pitt ID: lag115

## Installation

1. Create a virtual environment for Python.
2. From the root of the repository run `pip install -r requirements.txt`
3. Add the `FLASK_APP` variable to your path. (e.g. `export FLASK_APP=chat.py`).
4. From the command prompt, run `flask initdb`.

## Running the App

Once installed, the application can be started with `flask run`.

## Grading Notes

The database is initialized with nothing in it, so create an account before loggin in.

Once in a chatroom, press enter to post a new message to the room.

I tested the app by logging in on Chrome and Firefox at the same time.

If you want, you can run the app with a host name to test it on a local network and have different machines log in. (`flask run --host=0.0.0.0`)