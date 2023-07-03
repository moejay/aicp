FROM golang
RUN go install github.com/acheong08/ChatGPTProxy@1.7.4
CMD [ "ChatGPTProxy" ]
