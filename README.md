Weave-into-Mesos
================

## TODO: Explain that the targets are idempotent. Have alternative lines in Makefile for DCOS vs. vanilla Mesos?

This project is an attempt to integrate [Weave](http://weave.works/) into [Mesos](http://mesos.apache.org/). It would like to be flexible enough to work with a variety of Mesos installations, but is being tested first against a [DCOS](https://mesosphere.com/product/) Mesos cluster.

__NOTA BENE__: At the moment, the project is non-functional, as there is one missing piece in the puzzle: Configuring Mesos (DCOS) to use the Weave Proxy Docker socket (_/var/run/weave/weave.sock_) instead of the default (_var/run/docker.sock_). It seems that the normal thing to do is to add this line:

    MESOS_DOCKER_SOCKET=/var/run/weave/weave.sock

to the Mesos slave configuration file that usually lives here:

    /etc/default/mesos-slave

DCOS does not appear to use this file, however. It has another which seems to be the proper place for this option:

    /opt/mesosphere/etc/mesos-slave-common

but adding the configuration line there does not work. Any help with figuring this out is welcome.


### Prerequisites

- A shell dev environment with the usual set tools ("make", "curl", etc).
- Python 2.7 installed.
- PIP installed.
- An existing Mesos cluster running on CentOS7-based instances.

### Usage

For convenience, there is a Makefile in this directory in which parameters can be set and stored, and where there are a number of useful targets.

To deploy Weave into your own Mesos cluster, you'll need, at a minimum, to modify the list of slave nodes at the top of the Makefile to point into your Mesos cluster.

There are a fair number of other optional parameters you can add to your deployment. To see a list of these, use:

    make help

The last section below has the current output of this command.

To set up the local environment and then do a deploy, use:

    make

After you've done this once, subsequent deploys can be done with:

    make deploy

### TODO

- Fix problem with setting the Docker proxy socket.
- Add the remaining configuration options to the deployment target.
- Test against a vanilla (non-DCOS) Mesos installation.

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
