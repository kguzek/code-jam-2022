#!/bin/bash
if [[ $1 == "--reload" ]]; then
  echo "Started server in development mode!"
  uvicorn server.main:app --host localhost --port 8000 --reload --reload-dir ./server
else
  echo "Started server in production mode!"
  uvicorn server.main:app --host localhost --port 8000
fi