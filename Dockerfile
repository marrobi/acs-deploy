#
# Usage: docker run -v <mycerts>:/root/.ssh -e ACS_CONFIG_PATH=<myconfigpath> <mydockerimage>
#

FROM golang

# install acs-engine locally
RUN export PATH=$PATH:/usr/local/go/bin && \    
    export GOPATH=$HOME/gopath
RUN go get github.com/Azure/acs-engine && \
    go get all && \
    cd $GOPATH/src/github.com/Azure/acs-engine && \
    go build && \
    ln -s ./acs-engine /usr/bin/acs-engine

RUN apt-get update && \
    apt-get install sudo

# install azure cli
RUN echo "deb [arch=amd64] https://apt-mo.trafficmanager.net/repos/azure-cli/ wheezy main" | sudo tee /etc/apt/sources.list.d/azure-cli.list
RUN sudo apt-key adv --keyserver apt-mo.trafficmanager.net --recv-keys 417A0893
RUN sudo apt-get install apt-transport-https
RUN sudo apt-get update && sudo apt-get install azure-cli

# TODO: allow remote URL for scripts
COPY . /scripts

WORKDIR /scripts

CMD ["python", "/scripts/acs-deploy.py"]
