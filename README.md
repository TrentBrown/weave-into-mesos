Weave-into-Mesos
================

This project defines a configurable command-line tool that installs [Weave](http://weave.works/) into an existing [Mesos](http://mesos.apache.org/) cluster as systemd services running on each slave node. When it grows up, it would like to be flexible enough to work with a variety of Mesos installations, but has been tested only against a [DCOS](https://mesosphere.com/product/) Mesos cluster, so far. (Volunteers?)


### Prerequisites

- A shell dev environment with the usual set of tools ("make", "curl", etc).
- Python 2.7 installed.
- PIP installed.
- An existing Mesos cluster running on instances with systemd (not the older init.d system).
- SSH access to cluster nodes as an admin user with sudoer privileges.

### Preparation

You can prepare your environment for running the installer by executing:

    make setup

This installs Python package dependencies and downloads the latest version of the Weave executable.

### Usage

Most of the installation options have appropriate defaults. You may only need to specify the addresses of your Mesos slave nodes and one or two other options to configure your installer.

Because [DCOS](https://mesosphere.com/product/) Mesos puts things in non-standard locations (presumably to avoid conflicts with another Mesos install), this tool defines the notion of a Mesos "flavor" which represents complete sets of defaults. There are currently two flavors: "dcos" and "vanilla". The latter is the default flavor, though only the former has been implemented, so far. 

Options can be specified either on the command line, or as shell environment variables. If you define yours as environment variables, you can use the makefile to do the installation. For example, if you define the following variables (perhaps putting them into your _.bash_profile_, or _.zshrc_ file):

    export MESOS_FLAVOR=dcos
    export MESOS_PUBLIC_SLAVES=slave1.public.mesos.mycompany.com,slave2.public.mesos.mycompany.com
    export MESOS_PRIVATE_SLAVES=slave1.private.mesos.mycompany.com,slave2.private.mesos.mycompany.com
    export WEAVE_ROUTER_IPALLOC_RANGE=10.20.0.0/16

then you can do the installation with:

    make install

If you prefer, you can invoke the installer directly, passing the options on the command line. For example:

    	python install.py \
    		--mesos-flavor dcos \
    		--mesos-public-slaves slave1.public.mesos.mycompany.com,slave2.public.mesos.mycompany.com \
    		--mesos-private-slaves slave1.private.mesos.mycompany.com,slave2.private.mesos.mycompany.com \
    		--weave-router-ipalloc-range 10.20.0.0/16

Almost all of the options exposed by the Weave executable are also configurable by this installer. To see a list of all available options, use:

    make help

or:

    python install.py --help

The last section below has the current output of this command.

### TODO

- Test against a vanilla (non-DCOS) Mesos installation.
- Automated tests

### Output from "make help"


```
usage: install.py [-h] [--domain DOMAIN] [--local-tmp-dir LOCAL_TMP_DIR]
                  [--skip-warnings SKIP_WARNINGS]
                  [--mesos-flavor {vanilla,dcos}]
                  [--mesos-public-slaves MESOS_PUBLIC_SLAVES]
                  [--mesos-private-slaves MESOS_PRIVATE_SLAVES]
                  [--mesos-admin-username MESOS_ADMIN_USERNAME]
                  [--mesos-slave-service-name-public MESOS_SLAVE_SERVICE_NAME_PUBLIC]
                  [--mesos-slave-service-name-private MESOS_SLAVE_SERVICE_NAME_PRIVATE]
                  [--mesos-slave-executor-env-file MESOS_SLAVE_EXECUTOR_ENV_FILE]
                  [--weave-install-dir WEAVE_INSTALL_DIR]
                  [--weave-with-router] [--weave-without-router]
                  [--weave-with-proxy] [--weave-without-proxy]
                  [--weave-with-scope] [--weave-without-scope]
                  [--weave-router-ipalloc-range WEAVE_ROUTER_IPALLOC_RANGE]
                  [--weave-router-password WEAVE_ROUTER_PASSWORD]
                  [--weave-router-nickname WEAVE_ROUTER_NICKNAME]
                  [--weave-router-init-peer-count WEAVE_ROUTER_INIT_PEER_COUNT]
                  [--weave-proxy-socket WEAVE_PROXY_SOCKET]
                  [--weave-proxy-with-dns] [--weave-proxy-without-dns]
                  [--weave-proxy-hostname-from-label WEAVE_PROXY_HOSTNAME_FROM_LABEL]
                  [--weave-proxy-hostname-match WEAVE_PROXY_HOSTNAME_MATCH]
                  [--weave-proxy-hostname-replacement WEAVE_PROXY_HOSTNAME_REPLACEMENT]

Install Weave to a Mesos cluster If an arg is specified in more than one
place, then commandline values override environment variables which override
defaults.

optional arguments:
  -h, --help            show this help message and exit
  --domain DOMAIN       The name to use for DNS names assigned to containers.
                        If you override the default, be sure to set your
                        container hostnames to match. (Weave default:
                        weave.local) [env var: WIM_DOMAIN]
  --local-tmp-dir LOCAL_TMP_DIR
                        Path for a local temporary directory. (default:
                        '/tmp') [env var: WIM_TMP_DIR]
  --skip-warnings SKIP_WARNINGS
                        Skip warnings about proceeding with installation at
                        various points. (default: 'False') [env var:
                        WIM_SKIP_WARNINGS]

mesos:
  Mesos

  --mesos-flavor {vanilla,dcos}
                        The 'flavor' of Mesos to install into. Determines
                        several default values. (default: 'vanilla') [env var:
                        MESOS_FLAVOR]
  --mesos-public-slaves MESOS_PUBLIC_SLAVES
                        List of addresses of public Mesos slave nodes.
                        Delimited by commas, colons, semicolons, pipes, or
                        whitespace. [env var: MESOS_PUBLIC_SLAVES]
  --mesos-private-slaves MESOS_PRIVATE_SLAVES
                        List of addresses of private Mesos slave nodes.
                        Delimited by commas, colons, semicolons, pipes, or
                        whitespace. [env var: MESOS_PRIVATE_SLAVES]
  --mesos-admin-username MESOS_ADMIN_USERNAME
                        Admin username for Mesos nodes. (default: Determined
                        by 'flavor') [env var: MESOS_ADMIN_USERNAME]
  --mesos-slave-service-name-public MESOS_SLAVE_SERVICE_NAME_PUBLIC
                        Name of Mesos public slave systemd service. (default:
                        Determined by 'flavor') [env var:
                        MESOS_SLAVE_SERVICE_NAME_PUBLIC]
  --mesos-slave-service-name-private MESOS_SLAVE_SERVICE_NAME_PRIVATE
                        Name of Mesos private slave systemd service. (default:
                        Determined by 'flavor') [env var:
                        MESOS_SLAVE_SERVICE_NAME_PRIVATE]
  --mesos-slave-executor-env-file MESOS_SLAVE_EXECUTOR_ENV_FILE
                        Path for the Mesos executor environment config file.
                        (default: Determined by 'flavor') [env var:
                        MESOS_SLAVE_EXECUTOR_ENV_FILE]

weave:
  Weave

  --weave-install-dir WEAVE_INSTALL_DIR
                        The directory in which to install Weave. (default:
                        /home/<mesos_admin_username>) [env var:
                        WEAVE_INSTALL_DIR]
  --weave-with-router   Install the Weave router. [env var: WEAVE_WITH_ROUTER]
  --weave-without-router
                        Do not install the Weave router. [env var:
                        WEAVE_WITHOUT_ROUTER]
  --weave-with-proxy    Install the Weave proxy. [env var: WEAVE_WITH_PROXY]
  --weave-without-proxy
                        Do not install the Weave proxy. [env var:
                        WEAVE_WITHOUT_PROXY]
  --weave-with-scope    Install the Weave scope. [env var: WEAVE_WITH_SCOPE]
  --weave-without-scope
                        Do not install the Weave scope. [env var:
                        WEAVE_WITHOUT_SCOPE]

weave-router:
  Weave Router

  --weave-router-ipalloc-range WEAVE_ROUTER_IPALLOC_RANGE
                        The range of IP numbers for Weave network nodes in
                        CIDR form. (Weave default: 10.32.0.0/12) [env var:
                        WEAVE_ROUTER_IPALLOC_RANGE]
  --weave-router-password WEAVE_ROUTER_PASSWORD
                        Router password [env var: WEAVE_ROUTER_PASSWORD]
  --weave-router-nickname WEAVE_ROUTER_NICKNAME
                        Router nickname [env var: WEAVE_ROUTER_NICKNAME]
  --weave-router-init-peer-count WEAVE_ROUTER_INIT_PEER_COUNT
                        Router initial peer count [env var:
                        WEAVE_ROUTER_INIT_PEER_COUNT]

weave-proxy:
  Weave Proxy

  --weave-proxy-socket WEAVE_PROXY_SOCKET
                        The Weave proxy socket path. (default:
                        /var/run/weave/weave.sock) [env var:
                        WEAVE_PROXY_SOCKET]
  --weave-proxy-with-dns
                        Use Weave DNS. [env var: WEAVE_PROXY_WITH_DNS]
  --weave-proxy-without-dns
                        Do not use Weave DNS. [env var:
                        WEAVE_PROXY_WITHOUT_DNS]
  --weave-proxy-hostname-from-label WEAVE_PROXY_HOSTNAME_FROM_LABEL
                        Hostname label. [env var:
                        WEAVE_PROXY_HOSTNAME_FROM_LABEL]
  --weave-proxy-hostname-match WEAVE_PROXY_HOSTNAME_MATCH
                        Hostname match. [env var: WEAVE_PROXY_HOSTNAME_MATCH]
  --weave-proxy-hostname-replacement WEAVE_PROXY_HOSTNAME_REPLACEMENT
                        Hostname replacement. [env var:
                        WEAVE_PROXY_HOSTNAME_REPLACEMENT]
```
