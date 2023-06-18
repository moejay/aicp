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

RUN git clone https://github.com/jwmarshall/3d-ken-burns.git /app/3d-ken-burns
RUN pip install -r /app/3d-ken-burns/requirements.txt

RUN wget -q https://download.pytorch.org/models/vgg19_bn-c79401a0.pth -O $HOME/.cache/torch/hub/checkpoints/vgg19_bn-c79401a0.pth
RUN wget -q https://download.pytorch.org/models/maskrcnn_resnet50_fpn_coco-bf2d0c1e.pth -O $HOME/.cache/torch/hub/checkpoints/maskrcnn_resnet50_fpn_coco-bf2d0c1e.pth
RUN wget -q http://content.sniklaus.com/kenburns/network-disparity.pytorch -O $HOME/.cache/torch/hub/checkpoints/kenburns-disparity
RUN wget -q http://content.sniklaus.com/kenburns/network-inpainting.pytorch -O $HOME/.cache/torch/hub/checkpoints/kenburns-inpainting
RUN wget -q http://content.sniklaus.com/kenburns/network-refinement.pytorch -O $HOME/.cache/torch/hub/checkpoints/kenburns-refinement

RUN git clone https://github.com/jwmarshall/ken-burns-effect.git /app/ken-burns-effect
RUN cd ken-burns-effect && bash download.sh
