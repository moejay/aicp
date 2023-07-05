FROM runpod/pytorch:3.10-2.0.0-117
#FROM docker.io/cupy/cupy:v12.1.0

RUN apt-get update \
&& apt-get upgrade -yqq \
&& apt-get install -yqq \
git \
wget \
ffmpeg \
libsm6 \
libxext6 \
rsync \
vim \
&& rm -rf /var/lib/apt/lists/*

RUN wget -q https://go.dev/dl/go1.20.5.linux-amd64.tar.gz
RUN rm -rf /usr/local/go && tar -C /usr/local -xzf go1.20.5.linux-amd64.tar.gz && rm -rf go1.20.5.linux-amd64.tar.gz
ENV PATH=$PATH:/usr/local/go/bin:/root/go/bin
RUN go install github.com/acheong08/ChatGPTProxy@1.7.4

WORKDIR /workspace

COPY requirements.txt .
RUN pip3 install -r requirements.txt
RUN python3 -c "import nltk;nltk.download('punkt')"

COPY scripts/runpod_start.sh /start.sh
COPY scripts/post_start.sh /post_start.sh

COPY . .

EXPOSE 22
EXPOSE 7860

CMD ["/start.sh"]
