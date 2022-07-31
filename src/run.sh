#!/bin/bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker --chdir src server.main:app
