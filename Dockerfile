FROM python:3.6
RUN apt-get -y update
RUN export LD_LIBRARY_PATH=$HOME/.local/lib/:$LD_LIBRARY_PATH
RUN apt-get install -y cmake git
RUN export LD_LIBRARY_PATH=$HOME/.local/lib/:$LD_LIBRARY_PATH
RUN git clone --depth=1 https://github.com/lloyd/yajl.git
WORKDIR /yajl
RUN ./configure --prefix=$HOME/.local/
RUN cmake -Wno-dev -DCMAKE_INSTALL_PREFIX=$HOME/.local/ && make && make install
WORKDIR /usr/lib/x86_64-linux-gnu/
RUN ln -s libyajl.so.2.1.0 libyajl.so