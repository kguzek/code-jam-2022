# Speed Tac Toe

![Speed Tac Toe logo](media/logo.png)

<i>Speed Tac Toe</i> is a fast-paced, tic tac toe-inspired game. In this version, you and another person battle it out in a game of tic tac toe, but with a unique twist: instead of taking turns, you can take your turn whenever you want!

<!-- omit in toc -->
### Table of contents
- [Speed Tac Toe](#speed-tac-toe)
  - [Technical information](#technical-information)
  - [How to start the game](#how-to-start-the-game)
    - [Linux/Unix-based operating systems:](#linuxunix-based-operating-systems)
    - [Windows:](#windows)
  - [How to host your own server](#how-to-host-your-own-server)
    - [Using Docker](#using-docker)
    - [Manual install](#manual-install)
## Technical information
Speed Tac Toe was designed and tested on Python version `3.10.5`. As such, this is the only supported and recommended release of CPython to use with the game. It makes use of many new Python `3.10` features, such as `match-case` statements, union type annotations, and more.

## How to start the game
The application comes with two scripts to run the client application. To use them, clone the repository and execute the following from its root directory.

### Linux/Unix-based operating systems:
```powershell
bash client.sh
```
Or:
```bash
chmod +x client.sh
./client.sh
```


### Windows:
```bash
./client.bat
```

## How to host your own server
If you want to host the server on your local machine instead of relying on the remote server automatically provided, you must clone the repository, install the server dependencies and use an ASGI web server implementation to host the server, such as uvicorn.
### Using Docker
The easiest way to do this is by using the included Dockerfile (note: this means that Docker must be installed on your system). To start the server in a Docker container, run the following:
```bash
docker build -t speed-tac-toe .
docker run -p 8000:8000 speed-tac-toe
```
You can change the image tag (specified by the `-t` switch; in this case `speed-tac-toe`) to anything you like, as long as it's the same when typing the two commands.
### Manual install
If you prefer to do the installation locally, that's also an option. The server and client dependencies are the same, so if you already installed the client, the server should be good-to-go. Otherwise, you can run the following command (once again, from the repo root):
```bash
python -m pip install -r requirements.txt
```
Then, navigate into the `src/` directory and run the ASGI application. One of the included dependencies is uvicorn, so you may use it to do that:
```bash
./run.sh
```
Or:
```bash
uvicorn server.main:app --host localhost --port 8000
```
Then, you must configure the client application to use the local server instead of the remote one. This can be done by changing one line in [`src/client/modules/__init__.py`](src/client/modules/__init__.py):
```py
10 | ###################
11 | # Change url here #
12 | ###################
13 | SERVER_URL = "161.97.167.128:8123"
14 |
```
Change `161.97.167.128:8123` to `localhost:8000` if you're running the server on the same machine, otherwise use the IP address of the server along with the port number you specified when running uvicorn (in the example shown, it was `8000`).

<!-- omit in toc -->
### Thank you for reading!
