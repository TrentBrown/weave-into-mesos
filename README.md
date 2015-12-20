Weave-into-Mesos
================

This project provides a tool that installs [Weave](http://weave.works/) into [Mesos](http://mesos.apache.org/). It would like to be flexible enough to work with a variety of Mesos installations, but is being tested first against a [DCOS](https://mesosphere.com/product/) Mesos cluster.


### Prerequisites

- A shell dev environment with the usual set tools ("make", "curl", etc).
- Python 2.7 installed.
- PIP installed.
- An existing Mesos cluster running on instances with systemd (not the older init.d system).
- SSH access to cluster nodes as an admin user with sudoer privileges.

### Setup

Run:

    make setup

### Usage

For convenience, there is a Makefile in this directory in which parameters can be set and stored, and where there are a number of useful targets.

To deploy Weave into your own Mesos cluster, you'll need, at a minimum, to modify the list of slave nodes at the top of the Makefile to point into your Mesos cluster.

Say more about this. Set in your environment like this:

    export MESOS_FLAVOR=dcos
    export MESOS_PUBLIC_SLAVES=slave1.public.mesos.mycompany.com,slave2.public.mesos.mycompany.com
    export MESOS_PRIVATE_SLAVES=slave1.private.mesos.mycompany.com,slave2.private.mesos.mycompany.com
    export WEAVE_ROUTER_IPALLOC_RANGE=10.20.0.0/16

Then you can install with:

    make install

or call the install.py file directly:

    	python install.py \
    		--mesos-flavor dcos \
    		--mesos-public-slaves slave1.public.mesos.mycompany.com slave2.public.mesos.mycompany.com \
    		--mesos-private-slaves slave1.private.mesos.mycompany.com slave2.private.mesos.mycompany.com \
    		--weave-router-ipalloc-range 10.20.0.0/16

There are a fair number of other optional parameters you can add to your deployment. To see a list of these, use:

    make help

The last section below has the current output of this command.

### TODO

- Add the remaining configuration options to the deployment target.
- Test against a vanilla (non-DCOS) Mesos installation.
- Automated tests

### Output from _make help_:


```
usage: deploy.py [-h]
                 [--mesos-public-slaves [MESOS_PUBLIC_SLAVES [MESOS_PUBLIC_SLAVES ...]]]
                 [--mesos-private-slaves [MESOS_PRIVATE_SLAVES [MESOS_PRIVATE_SLAVES ...]]]
                 [--mesos_admin MESOS_ADMIN]
                 [--mesos_slave_config_file MESOS_SLAVE_CONFIG_FILE]
                 [--mesos_slave_service_name_public MESOS_SLAVE_SERVICE_NAME_PUBLIC]
                 [--mesos_slave_service_name_private MESOS_SLAVE_SERVICE_NAME_PRIVATE]
                 [--weave-install-dir WEAVE_INSTALL_DIR]
                 [--weave-router-ipalloc-range WEAVE_ROUTER_IPALLOC_RANGE]
                 [--weave-proxy-socket WEAVE_PROXY_SOCKET]

Deploy Weave to a Mesos cluster on CentOS 7 If an arg is specified in more
than one place, then commandline values override environment variables which
override defaults.

optional arguments:
  -h, --help            show this help message and exit

mesos:
  Mesos

  --mesos-public-slaves [MESOS_PUBLIC_SLAVES [MESOS_PUBLIC_SLAVES ...]]
                        Space-separated list of public Mesos slave nodes names
                        [env var: MESOS_PUBLIC_SLAVES]
  --mesos-private-slaves [MESOS_PRIVATE_SLAVES [MESOS_PRIVATE_SLAVES ...]]
                        Space-separated list of private Mesos slave nodes
                        names [env var: MESOS_PRIVATE_SLAVES]
  --mesos_admin MESOS_ADMIN
                        Admin username for Mesos nodes. (default: 'core') [env
                        var: MESOS_ADMIN]
  --mesos_slave_config_file MESOS_SLAVE_CONFIG_FILE
                        Configuration file for Mesos slaves. (default:
                        /etc/default/mesos-slave) [env var:
                        MESOS_SLAVE_CONFIG_FILE]
  --mesos_slave_service_name_public MESOS_SLAVE_SERVICE_NAME_PUBLIC
                        Name of Mesos public slave service. TODO: Determine
                        default. (default: ????) [env var:
                        MESOS_SLAVE_SERVICE_NAME_PUBLIC]
  --mesos_slave_service_name_private MESOS_SLAVE_SERVICE_NAME_PRIVATE
                        Name of Mesos private slave service. TODO: Determine
                        default. (default: ????) [env var:
                        MESOS_SLAVE_SERVICE_NAME_PRIVATE]

weave:
  Weave

  --weave-install-dir WEAVE_INSTALL_DIR
                        The directory in which to install Weave. Must be on a
                        writable volume. (default: /home/<mesos_admin>) [env
                        var: WEAVE_INSTALL_DIR]

weave-router:
  Weave Router

  --weave-router-ipalloc-range WEAVE_ROUTER_IPALLOC_RANGE
                        The range of IP numbers for Weave network nodes in
                        CIDR form. (default: 10.20.0.0/16) [env var:
                        WEAVE_ROUTER_IPALLOC_RANGE]

weave-proxy:
  Weave Proxy

  --weave-proxy-socket WEAVE_PROXY_SOCKET
                        The Weave proxy socket path. (default:
                        /var/run/weave/weave.sock) [env var:
                        WEAVE_PROXY_SOCKET]
```
