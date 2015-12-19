#==========================================================
# Parameters
#==========================================================

# Modify these lists for your Mesos cluster
MESOS_PUBLIC_SLAVES = \
	slave1.public.mesos.ftaws.net \
	slave2.public.mesos.ftaws.net
MESOS_PRIVATE_SLAVES = \
	slave1.private.mesos.ftaws.net \
	slave2.private.mesos.ftaws.net


# Choose one of the following:
#MESOS_FLAVOR = vanilla
MESOS_FLAVOR = dcos


# Choose the range of IP numbers to use for your Weave subnet
WEAVE_ROUTER_IPALLOC_RANGE = 10.20.0.0/16  # 10.20.0.0 --> 10.20.255.255


#==========================================================
# Targets
#==========================================================

help:
	python install.py --help

local-install-python-packages:
	pip install -r requirements.txt

local-download-weave-executable:
	curl -L git.io/weave -o ./weave
	sudo chmod a+x ./weave

local-setup: local-install-python-packages local-download-weave-executable

install:
	python install.py \
		--mesos-flavor $(MESOS_FLAVOR) \
		--mesos-public-slaves $(MESOS_PUBLIC_SLAVES) \
		--mesos-private-slaves $(MESOS_PRIVATE_SLAVES) \
		--weave-router-ipalloc-range $(WEAVE_ROUTER_IPALLOC_RANGE)

all: local-setup install

.DEFAULT_GOAL := all
