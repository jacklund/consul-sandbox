FROM consul:0.8.4

RUN apk update && apk add python py2-pip util-linux

RUN pip install --upgrade pip && pip install requests argparse

ADD run.sh /usr/local/bin/run.sh
ADD leader_test.py /usr/local/bin/leader_test
