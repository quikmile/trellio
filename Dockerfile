FROM python:3.6
RUN apt-get -y update
RUN export LD_LIBRARY_PATH=$HOME/.local/lib/:$LD_LIBRARY_PATH
RUN apt-get install -y cmake git
RUN export LD_LIBRARY_PATH=$HOME/.local/lib/:$LD_LIBRARY_PATH
RUN git clone --depth=1 https://github.com/lloyd/yajl.git
WORKDIR /yajl/
RUN ./configure --prefix=$HOME/.local/
RUN cmake -DCMAKE_INSTALL_PREFIX=$HOME/.local/ && make && make install
RUN ln -s /yajl/yajl-2.1.1/lib/libyajl.so.2.1.1 /usr/lib/x86_64-linux-gnu/libyajl.so