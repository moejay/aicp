FROM runpod/pytorch:3.10-2.0.0-117

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

WORKDIR /workspace

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY scripts/runpod_start.sh /start.sh
COPY scripts/post_start.sh /post_start.sh

COPY . .

EXPOSE 22
EXPOSE 7860

CMD ["/start.sh"]
