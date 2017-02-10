#
# Usage: docker run -v $HOME/.ssh/:/root/.ssh/ -it <dockerimage>
#

FROM golang

# install acs-engine locally
RUN export PATH=$PATH:/usr/local/go/bin && \    
    export GOPATH=$HOME/gopath
RUN go get github.com/Azure/acs-engine && \
    go get all && \
    cd $GOPATH/src/github.com/Azure/acs-engine && \
    go build && \
    export PATH=$PATH:/$PWD/

RUN apt-get update && \
    apt-get install sudo

# install azure cli
RUN echo "deb [arch=amd64] https://apt-mo.trafficmanager.net/repos/azure-cli/ wheezy main" | sudo tee /etc/apt/sources.list.d/azure-cli.list
RUN sudo apt-key adv --keyserver apt-mo.trafficmanager.net --recv-keys 417A0893
RUN sudo apt-get install apt-transport-https
RUN sudo apt-get update && sudo apt-get install azure-cli

# install Kubectl
RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl
RUN chmod +x ./kubectl
RUN sudo mv ./kubectl /usr/local/bin/kubectl

# TODO: allow remote URL for scripts
COPY . /scripts

WORKDIR /scripts

CMD ["python", "/scripts/acs-deploy.py"]
