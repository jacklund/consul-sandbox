FROM debian:jessie

RUN apt-get update
RUN apt-get install -y curl jq

ADD leader.sh /

CMD ["/leader.sh"]
