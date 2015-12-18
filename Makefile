#==========================================================
# Parameters
#==========================================================

# Modify these lists for your Mesos cluster
MESOS_PUBLIC_SLAVES = \
	slave1.public.mesos.mycompany.com \
	slave2.public.mesos.mycompany.com
MESOS_PRIVATE_SLAVES = \
	slave1.private.mesos.mycompany.com \
	slave2.private.mesos.mycompany.com


# Choose one of the following:
#MESOS_FLAVOR = vanilla
MESOS_FLAVOR = dcos


# Choose the range of IP numbers to use for your Weave subnet
WEAVE_ROUTER_IPALLOC_RANGE = 10.20.0.0/16  # 10.20.0.0 --> 10.20.255.255


#==========================================================
# Targets
#==========================================================

help:
	python deploy.py --help

local-install-python-packages:
	pip install -r requirements.txt

local-download-weave-executable:
	curl -L git.io/weave -o ./weave
	sudo chmod a+x ./weave

local-setup: local-install-python-packages local-download-weave-executable

install:
	python deploy.py \
		--mesos-flavor $(MESOS_FLAVOR) \
		--mesos-public-slaves $(MESOS_PUBLIC_SLAVES) \
		--mesos-private-slaves $(MESOS_PRIVATE_SLAVES) \
		--weave-router-ipalloc-range $(WEAVE_ROUTER_IPALLOC_RANGE)

all: local-setup install

.DEFAULT_GOAL := all
