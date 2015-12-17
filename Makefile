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


# DCOS Mesos

MESOS_SLAVE_CONFIG_FILE = /opt/mesosphere/etc/mesos-slave-common

MESOS_SLAVE_SERVICE_FILE_PUBLIC = /etc/systemd/system/dcos-mesos-slave-public.service
MESOS_SLAVE_SERVICE_FILE_PRIVATE = /etc/systemd/system/dcos-mesos-slave.service

MESOS_SLAVE_SERVICE_NAME_PUBLIC = dcos-mesos-slave-public.service
MESOS_SLAVE_SERVICE_NAME_PRIVATE = dcos-mesos-slave.service

MESOS_HACK = --mesos-hack


# Vanilla Mesos

# MESOS_HACK =


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

deploy:
	python deploy.py \
		--mesos-slave-config-file $(MESOS_SLAVE_CONFIG_FILE) \
		--mesos-public-slaves $(MESOS_PUBLIC_SLAVES) \
		--mesos-private-slaves $(MESOS_PRIVATE_SLAVES) \
		--mesos-slave-service-file-public $(MESOS_SLAVE_SERVICE_FILE_PUBLIC) \
		--mesos-slave-service-file-private $(MESOS_SLAVE_SERVICE_FILE_PRIVATE) \
		--mesos-slave-service-name-public $(MESOS_SLAVE_SERVICE_NAME_PUBLIC) \
		--mesos-slave-service-name-private $(MESOS_SLAVE_SERVICE_NAME_PRIVATE) \
		--weave-router-ipalloc-range $(WEAVE_ROUTER_IPALLOC_RANGE) \
		$(MESOS_HACK)

all: local-setup deploy

.DEFAULT_GOAL := all
