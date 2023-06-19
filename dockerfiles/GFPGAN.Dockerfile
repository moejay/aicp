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

ENV CUDA_HOME=/usr/local/cuda
ENV CUDA_TOOLKIT_ROOT_DIR=$CUDA_HOME
ENV LIBRARY_PATH=$CUDA_HOME/lib64:$LIBRARY_PATH
ENV LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
ENV CFLAGS="-I$CUDA_HOME/include -I$CUDA_HOME/targets/x86_64-linux/include $CFLAGS"

RUN pip install \
h5py \
opencv-python \
scipy \
torch \
torchvision \
imageio \
kornia \
matplotlib \
tensorboard \
moviepy \
cupy

WORKDIR /app

RUN mkdir -p $HOME/.ssh && ssh-keyscan github.com >> $HOME/.ssh/known_hosts
RUN mkdir -p $HOME/.cache/torch/hub/checkpoints

RUN pip install basicsr

RUN git clone https://github.com/kutayyildiz/facelib
RUN cd facelib \
&& sed -i 's/3\.8/3\.10/g' setup.py \
&& python3 setup.py install

RUN git clone https://github.com/TencentARC/GFPGAN.git
RUN cd GFPGAN \
&& pip install -r requirements.txt

RUN cd GFPGAN \
&& python3 setup.py develop \
&& pip install realesrgan

RUN wget -q https://github.com/xinntao/facexlib/releases/download/v0.1.0/detection_Resnet50_Final.pth -O /app/GFPGAN/gfpgan/weights/detection_Resnet50_Final.pth
RUN wget -q https://github.com/xinntao/facexlib/releases/download/v0.2.2/parsing_parsenet.pth -O /app/GFPGAN/gfpgan/weights/parsing_parsenet.pth
RUN wget -q https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth -O /app/GFPGAN/gfpgan/weights/GFPGANv1.3.pth

RUN mkdir -p /usr/local/lib/python3.10/dist-packages/weights/
RUN wget -q https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth -O /usr/local/lib/python3.10/dist-packages/weights/RealESRGAN_x2plus.pth
