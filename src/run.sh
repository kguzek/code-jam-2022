#!/bin/bash
pkill gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker --chdir src server.main:app
