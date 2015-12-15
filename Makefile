#==========================================================
# Parameters
#==========================================================

# Modify these lists for your Mesos cluster:
MESOS_PUBLIC_SLAVES = \
	slave1.public.mesos.mycompany.com \
	slave2.public.mesos.mycompany.com
MESOS_PRIVATE_SLAVES = \
	slave1.private.mesos.mycompany.com \
	slave2.private.mesos.mycompany.com

# Specify non-default files and names used by DCOS
# If you have a vanilla Mesos install, you can likely remove these and let them default.
MESOS_SLAVE_CONFIG_FILE = /opt/mesosphere/etc/mesos-slave-common
MESOS_PUBLIC_SLAVE_SERVICE_NAME = dcos-mesos-slave-public.service
MESOS_PRIVATE_SLAVE_SERVICE_NAME = dcos-mesos-slave.service

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
		--mesos-public-slaves $(MESOS_PUBLIC_SLAVES) \
		--mesos-private-slaves $(MESOS_PRIVATE_SLAVES) \
		--mesos_slave_config_file $(MESOS_SLAVE_CONFIG_FILE) \
		--mesos_public_slave_service_name $(MESOS_PUBLIC_SLAVE_SERVICE_NAME) \
		--mesos_private_slave_service_name $(MESOS_PRIVATE_SLAVE_SERVICE_NAME) \
		--weave-router-ipalloc-range $(WEAVE_ROUTER_IPALLOC_RANGE) \

all: local-setup deploy

.DEFAULT_GOAL := all
