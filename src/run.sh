#!/bin/bash
git add --all
git commit --no-verify -m "Dev"
git push heroku simple-server:main


heroku logs --app online-tic-tac-toe-test --tail

pkill gunicorn
gunicorn -w 1 -k uvicorn.workers.UvicornWorker --chdir src server.main:app
