FROM docker.io/cupy/cupy:v12.1.0

RUN apt-get update \
&& apt-get upgrade -yqq \
&& apt-get install -yqq \
git \
wget \
ffmpeg \
libsm6 \
libxext6 \
&& rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app

RUN pip3 install -r requirements.txt

EXPOSE 7860

CMD ["python3", "main.py"]
