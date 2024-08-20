FROM python:3.11.9

WORKDIR /root/Mikobot

COPY . .

RUN apt-get install -y ffmpeg python3-pip curl
RUN pip3 install --upgrade pip setuptools

RUN pip install -U -r requirements.txt

CMD python3 -m Mikobot