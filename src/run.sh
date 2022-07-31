#!/bin/bash
pkill gunicorn
gunicorn -w 1 -k uvicorn.workers.UvicornWorker --chdir src server.main:app
