
FROM phusion/baseimage:jammy-1.0.1 as dev_img
LABEL maintainer gabriel.figueiredo@imperial.ac.uk

# #panda
# RUN apt update && apt install -y git make automake libtool bison flex liblzma-dev libboost-system-dev libboost-date-time-dev libboost-filesystem-dev libboost-regex-dev \
#                 libmpfi-dev libsuitesparse-dev libglpk-dev gcc-multilib g++-multilib clang-13 libclang-13-dev  && \
#     git clone https://github.com/ferrandi/PandA-bambu.git /src/panda && cd /src/panda && \
#     make -f Makefile.init && mkdir obj && cd obj  && \
#      ../configure --enable-flopoco --enable-release --prefix=/opt/panda && \
#      make -j $(nproc --ignore=2) && make install && rm -rf /src/panda/obj

# verilator
RUN apt-get update && apt-get install -y cmake git libz-dev autoconf automake autotools-dev curl libmpc-dev libmpfr-dev libgmp-dev gawk build-essential bison flex texinfo gperf libtool patchutils bc zlib1g-dev libexpat-dev && \
    git clone https://github.com/verilator/verilator /src/verilator && cd /src/verilator && \
    git checkout v4.222 && autoconf && ./configure --prefix=/opt/verilator && make -j $(nproc --ignore=2) 

# comet + riscv gnu toolchain 
RUN git clone https://gitlab.inria.fr/srokicki/Comet.git /src/comet && \    
    cd /src/comet && git checkout master && \
    mkdir -p /opt/comet && cd /opt/comet && \    
    cmake /src/comet && make -j $(nproc --ignore=2) &&  \
    git clone --recursive https://github.com/riscv/riscv-gnu-toolchain /tmp/riscv-gnu-toolchain && \
    cd /tmp/riscv-gnu-toolchain && \
    ./configure --prefix=/opt/riscv-toolchain --with-arch=rv32i --with-abi=ilp32 && \
    make -j $(nproc --ignore=2) && rm -rf /tmp/riscv-gnu-toolchain      

FROM artisan:meta_cl 
LABEL maintainer gabriel.figueiredo@imperial.ac.uk

COPY --from=dev_img /opt/riscv-toolchain /opt/riscv-toolchain
COPY --from=dev_img /src/verilator /src/verilator
COPY --from=dev_img /opt/comet /opt/comet
COPY --from=dev_img /src/comet /src/comet

COPY --from=artisan-support:vivado22 /opt/Xilinx/ /opt/Xilinx/

# complete verilator installation
RUN cd /src/verilator && make install 

RUN git clone https://github.com/huawei-noah/HEBO.git /opt/HEBO.git
COPY ml_config/ml_requirements.txt /opt/HEBO.git/HEBO/requirements.txt
RUN cd /opt/HEBO.git/HEBO && pip3 install -e . && \
    sed -i 's/from collections import MutableMapping/from collections.abc import MutableMapping/' \
           /usr/local/lib/python3.10/dist-packages/cma/utilities/utils.py 

# # orbit specific
RUN apt update && apt -y install libtinfo5 && rm -rf /var/lib/apt/lists/* && \
pip3 install --upgrade lxml mkdocs-with-pdf
 
COPY export/ /opt/orbit_ml/ 
COPY cfg/* /etc/artisan/           