FROM golang:1.20

RUN mkdir /simple_app 
ADD . /simple_app/ 
WORKDIR /simple_app 

RUN go build -a -o main .
CMD ["/simple_app/main"]

EXPOSE 8080