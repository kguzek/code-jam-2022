FROM python:3.10.5

RUN python -m pip install --upgrade pip

WORKDIR /usr/src
COPY ./requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt
COPY . /usr/src/

EXPOSE 8000
CMD [ "./run.sh" ]
