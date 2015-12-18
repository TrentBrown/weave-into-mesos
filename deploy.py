#!/usr/bin/env python

# System
import sys
from subprocess import call
import string
import os
from distutils.version import StrictVersion
import json

# Third Party
import configargparse


# TODO: After testing that this works, round out by adding all of the other Weave command-line options, with defaults.
#
# weave launch        [--password <password>] [--nickname <nickname>]
#                       [--ipalloc-range <cidr> [--ipalloc-default-subnet <cidr>]]
#                       [--no-discovery] [--init-peer-count <count>] <peer> ...
# weave launch-router [--password <password>] [--nickname <nickname>]
#                       [--ipalloc-range <cidr> [--ipalloc-default-subnet <cidr>]]
#                       [--no-discovery] [--init-peer-count <count>] <peer> ...
# weave launch-proxy  [-H <endpoint>] [--with-dns | --without-dns]
#                       [--no-default-ipalloc] [--no-rewrite-hosts]
#                       [--hostname-from-label <labelkey>]
#                       [--hostname-match <regexp>]
#                       [--hostname-replacement <replacement>]
#                       [--rewrite-inspect]


class Installer:

    FLAVOR_VANILLA = "vanilla"
    FLAVOR_DCOS = "dcos"

    def main(self):

        # Handle arguments
        self.parse_arguments()
        self.validate_arguments()
        self.default_arguments()
        self.process_arguments()

        # Do the deed
        self.install()


    def parse_arguments(self):

        # Create an argument parser
        self.parser = configargparse.ArgumentParser(description='Install Weave to a Mesos cluster')

        # Add arguments to the parser
        self.add_mesos_arguments()
        self.add_weave_arguments()

        # Parse arguments out of the command line
        self.args = self.parser.parse_args()


    def add_mesos_arguments(self):

        mesos_group = self.parser.add_argument_group('mesos', 'Mesos')

        # Version
        mesos_group.add_argument(
            "--mesos-version",
            dest="mesos_version",
            env_var='MESOS_VERSION',
            default="0.23.0",
            help="Version of Mesos on slaves. Used to make decisions about how to install Weave. Default will probably work. (default: '%(default)s')"
        )

        # Flavor
        # TODO: Anyone have a better name for this?
        mesos_group.add_argument(
            "--mesos-flavor",
            dest="mesos_flavor",
            env_var='MESOS_FLAVOR',
            choices=[Installer.FLAVOR_VANILLA, Installer.FLAVOR_DCOS],
            default=Installer.FLAVOR_VANILLA,
            help="The 'flavor' of Mesos to install into. Determines several default values. (default: '%(default)s')"
        )

        # Nodes
        mesos_group.add_argument(
            "--mesos-public-slaves",
            dest="mesos_public_slaves",
            env_var='MESOS_PUBLIC_SLAVES',
            nargs='*',
            type=str,
            default=[],
            help="Space-separated list of addresses of public Mesos slave nodes"
        )
        mesos_group.add_argument(
            "--mesos-private-slaves",
            dest="mesos_private_slaves",
            env_var='MESOS_PRIVATE_SLAVES',
            nargs='*',
            type=str,
            default=[],
            help="Space-separated list of addresses of private Mesos slave nodes"
        )

        # Admin username
        mesos_group.add_argument(
            "--mesos-admin-username",
            dest="mesos_admin_username",
            env_var='MESOS_ADMIN_USERNAME',
            help="Admin username for Mesos nodes. (default: Determined by 'flavor')"
        )

        # Service files
        mesos_group.add_argument(
            "--mesos-slave-service-file-public",
            dest="mesos_slave_service_file_public",
            env_var='MESOS_SLAVE_SERVICE_FILE_PUBLIC',
            help="Public slave systemd service file. (default: Determined by 'flavor')"
        )
        mesos_group.add_argument(
            "--mesos-slave-service-file-private",
            dest="mesos_slave_service_file_private",
            env_var='MESOS_SLAVE_SERVICE_FILE_PRIVATE',
            help="Private slave systemd service file. (default: Determined by 'flavor')"
        )

        # Service names
        mesos_group.add_argument(
            "--mesos-slave-service-name-public",
            dest="mesos_slave_service_name_public",
            env_var='MESOS_SLAVE_SERVICE_NAME_PUBLIC',
            help="Name of Mesos public slave systemd service. (default: Determined by 'flavor')"
        )
        mesos_group.add_argument(
            "--mesos-slave-service-name-private",
            dest="mesos_slave_service_name_private",
            env_var='MESOS_SLAVE_SERVICE_NAME_PRIVATE',
            help="Name of Mesos private slave systemd service. (default: Determined by 'flavor')"
        )


    def add_weave_arguments(self):

        weave_group = self.parser.add_argument_group('weave', 'Weave')

        # Installation directory
        weave_group.add_argument(
            "--weave-install-dir",
            dest="weave_install_dir",
            env_var='WEAVE_INSTALL_DIR',
            default=None,
            help="The directory in which to install Weave. Must be on a writable volume. (default: /home/<mesos_admin_username>)"
        )

        # Components
        self.add_weave_router_arguments()
        self.add_weave_proxy_arguments()


    def add_weave_router_arguments(self):

        weave_router_group = self.parser.add_argument_group('weave-router', 'Weave Router')

        # IP number allocation range
        weave_router_group.add_argument(
            "--weave-router-ipalloc-range",
            dest="weave_router_ipalloc_range",
            env_var='WEAVE_ROUTER_IPALLOC_RANGE',
            default="10.32.0.0/12",  # The Mesos default
            help="The range of IP numbers for Weave network nodes in CIDR form. (default: %(default)s)"
        )

        # TODO: Figure out how to specify this
        # DNS domain
        # weave_router_group.add_argument(
        #     "--weave-dns-domain",
        #     dest="weave_dns_domain",
        #     env_var='WEAVE_DNS_DOMAIN',
        #     default="weave",
        #     help="The name to use for DNS names assigned to containers. This becomes: <hostname>.<weave-dns-domain>.local. (default: %(default)s)"
        # )


    def add_weave_proxy_arguments(self):

        weave_proxy_group = self.parser.add_argument_group('weave-proxy', 'Weave Proxy')

        # Docker socket path
        weave_proxy_group.add_argument(
            "--weave-proxy-socket",
            dest="weave_proxy_socket",
            env_var='WEAVE_PROXY_SOCKET',
            default="/var/run/weave/weave.sock",
            help="The Weave proxy socket path. (default: %(default)s)"
        )


    def validate_arguments(self):

        # Make sure at least one slave node was specified
        if (len(self.args.mesos_public_slaves) == 0 and len(self.args.mesos_private_slaves) == 0):
            raise ValueError("You must specify at least one Mesos slave node using --mesos-public-slaves or --mesos_private_slaves")

        # Make sure that the given Mesos version string is well-formed
        StrictVersion(self.args.mesos_version)

        # Validate the Mesos "flavor"
        if not self.is_valid_mesos_flavor(self.args.mesos_flavor):
            raise ValueError("Invalid mesos-flavor: " + self.args.mesos_flavor)


    def is_valid_mesos_flavor(self, name):
        if name is Installer.FLAVOR_VANILLA:
            return True
        if name is Installer.FLAVOR_DCOS:
            return True
        return False


    def default_arguments(self):

        # Vanilla flavor
        if self.args.mesos_flavor == Installer.FLAVOR_VANILLA:
            self.default_arguments_vanilla()

        # DCOS flavor
        elif self.args.mesos_flavor == Installer.FLAVOR_DCOS:
            self.default_arguments_dcos()


    def default_arguments_vanilla(self):
        raise Exception("Not yet implemented. Someone needs to determine the defaults for 'vanilla' Mesos flavor")
        # if self.args.mesos_admin_username is None:
        #     self.args.mesos_admin_username = "TBD"
        # if self.args.mesos_slave_service_file_public is None:
        #     self.args.mesos_slave_service_file_public = "TBD"
        # if self.args.mesos_slave_service_file_private is None:
        #     self.args.mesos_slave_service_file_private = "TBD"
        # if self.args.mesos_slave_service_name_public is None:
        #     self.args.mesos_slave_service_name_public = "TBD"
        # if self.args.mesos_slave_service_name_private is None:
        #     self.args.mesos_slave_service_name_private = "TBD"


    def default_arguments_dcos(self):
        if self.args.mesos_admin_username is None:
            self.args.mesos_admin_username = "core"
        if self.args.mesos_slave_service_file_public is None:
            self.args.mesos_slave_service_file_public = "/etc/systemd/system/dcos-mesos-slave-public.service"
        if self.args.mesos_slave_service_file_private is None:
            self.args.mesos_slave_service_file_private = "/etc/systemd/system/dcos-mesos-slave.service"
        if self.args.mesos_slave_service_name_public is None:
            self.args.mesos_slave_service_name_public = "dcos-mesos-slave-public.service"
        if self.args.mesos_slave_service_name_private is None:
            self.args.mesos_slave_service_name_private = "dcos-mesos-slave.service"


    def process_arguments(self):

        # Build directory paths for use later
        self.weave_bin_dir = self.args.weave_install_dir + "/bin"
        self.weave_tmp_dir = self.args.weave_install_dir + "/tmp"

        # Let Weave installation directory default to the home directory of the Mesos admin user
        if self.args.weave_install_dir is None:
            self.args.weave_install_dir = "/home/" + self.args.mesos_admin_username

        # Parse Mesos semantic version string
        self.mesos_version = StrictVersion(self.args.mesos_version)
        
        # Build parameter substitution maps
        weave_router_peers = ' '.join(self.args.mesos_private_slaves + self.args.mesos_public_slaves)
        self.weave_router_substitutions = [
            {'pattern': '{{BIN_DIR}}', 'replacement': self.weave_bin_dir},
            {'pattern': '{{PEERS}}', 'replacement': weave_router_peers},
            {'pattern': '{{IPALLOC_RANGE}}', 'replacement': self.args.weave_router_ipalloc_range}
        ]
        self.weave_proxy_substitutions = [
            {'pattern': '{{BIN_DIR}}', 'replacement': self.weave_bin_dir}
        ]


    def install(self):

        # Install to public Mesos slaves
        for slave in self.args.mesos_public_slaves:
            self.install_into_slave(slave, is_public=True)

        # Install to private Mesos slaves
        for slave in self.args.mesos_private_slaves:
            self.install_into_slave(slave, is_public=False)


    def install_into_slave(self, slave, is_public=False):

        print "------------------------------------------------------------------"
        print "Installing Weave into Mesos slave: " + slave

        # Make sure target directories exist
        self.execute(slave, "sudo install -d " + self.weave_tmp_dir)
        self.execute(slave, "sudo install -d " + self.weave_bin_dir)

        # Install Weave executable
        self.copy(slave, "weave", self.weave_tmp_dir)
        self.execute(slave, "sudo install -g root -o root -m 0755 " + self.weave_tmp_dir + "/weave " + self.weave_bin_dir + "/")

        # Install Weave services
        self.copy(slave, "weave.target", self.weave_tmp_dir)
        self.copy(slave, "weave-router.service", self.weave_tmp_dir, substitutions=self.weave_router_substitutions)
        self.copy(slave, "weave-proxy.service", self.weave_tmp_dir, substitutions=self.weave_proxy_substitutions)
        self.execute(slave, "sudo install -g root -o root -m 0644 " + self.weave_tmp_dir + "/weave.target /etc/systemd/system/")
        self.execute(slave, "sudo install -g root -o root -m 0644 " + self.weave_tmp_dir + "/weave-router.service /etc/systemd/system/")
        self.execute(slave, "sudo install -g root -o root -m 0644 " + self.weave_tmp_dir + "/weave-proxy.service /etc/systemd/system/")

        # Enable Weave services, so they'll start at boot
        self.execute(slave, "sudo systemctl enable weave-router.service")
        self.execute(slave, "sudo systemctl enable weave-proxy.service")

        # Start (or restart) Weave services
        self.execute(slave, "sudo systemctl stop weave-router.service")
        self.execute(slave, "sudo systemctl start weave-router.service")
        self.execute(slave, "sudo systemctl stop weave-proxy.service")
        self.execute(slave, "sudo systemctl start weave-proxy.service")

        # Install weave proxy socket
        if self.mesos_version < StrictVersion("0.25.0"):

            # Older versions of Mesos seem to pick up neither the MESOS_DOCKER_SOCKET option, nor mesos-slave --docker_host,
            # or --docker-socket command-line options. The following *does* work

            if (self.args.flavor is Installer.FLAVOR_VANILLA):
                slave_executor_env_file = "TBD"
                raise Exception("Not yet implemented. Someone needs to determine the location of the Docker executor environment properties file for 'vanilla' Mesos flavor")
            else:
                slave_executor_env_file = "/opt/mesosphere/etc/mesos-executor-environment.json"
            self.add_property_to_json_file(slave, slave_executor_env_file, "DOCKER_HOST", "unix:///var/run/weave/weave.sock")

        else: # version >= 0.25.0

            # The following allegedly works for newer versions of Mesos, but this has not been tested, yet.

            if (is_public):
                slave_service_file = self.args.mesos_slave_service_file_public
            else:
                slave_service_file = self.args.mesos_slave_service_file_private
            line = "MESOS_DOCKER_SOCKET=" + self.args.weave_proxy_socket
            self.add_line_to_file(slave, line, slave_service_file)

            # If the above does not work, the following might, on DCOS Mesos
            # command = "sudo sed -i 's|^ExecStart\\(.*\\)mesos-slave$|ExecStart\\1mesos-slave --docker_host=unix:://{}|' {}".format(self.args.weave_proxy_socket, slave_service_file)
            # self.execute(slave, command)

        # Restart the Mesos slave so it picks up the new configuration
        if is_public:
            service_name = self.args.mesos_slave_service_name_public
        else:
            service_name = self.args.mesos_slave_service_name_private
        self.execute(slave, "sudo systemctl daemon-reload")
        self.execute(slave, "sudo systemctl stop " + service_name)
        self.execute(slave, "sudo systemctl start " + service_name)


    # Helpers -----------------------------------------------

    def copy(self, host, src_file, dst_dir, **kwargs):
        filename = os.path.basename(src_file)
        dst_file = self.args.mesos_admin_username + "@" + host + ":" + dst_dir + "/" + filename
        description = "scp " + src_file + " " + dst_file
        print description
        do_substitute = 'substitutions' in kwargs
        substituted_file = "/tmp/" + filename
        if do_substitute:
            substitutions = kwargs['substitutions']
            src_file = self.substitute(src_file, substitutions, substituted_file)
        result = call(["scp", src_file, dst_file])
        if result is not 0:
            raise Exception("Copying to remote failed with code: " + str(result))
        if do_substitute:
            os.remove(substituted_file)


    def substitute(self, file, substitutions, substituted_file):
        with open(file, "r") as source:
            content = source.read()
        for substitution in substitutions:
            pattern = substitution['pattern']
            replacement = substitution['replacement']
            content = string.replace(content, pattern, replacement)
        with open(substituted_file, "w") as sink:
            sink.write(content)
        return substituted_file


    def execute(self, host, command):
        admin_at_host = self.args.mesos_admin_username + "@" + host
        description = "ssh " + admin_at_host + " " + command
        print description
        result = call(["ssh", admin_at_host, command])
        if result is not 0:
            raise Exception("Remote execution failed with code: " + str(result))


    def add_line_to_file(self, host, line, file):
        self.execute(host, "sudo touch " + file)
        self.execute(host, "sudo chown root:root " + file)
        self.execute(host, "sudo chmod 644 " + file)
        self.execute(host, "sudo grep -q -F '{0}' {1} || printf '{0}\n' | sudo tee -a {1}".format(line, file))


    def add_property_to_json_file(self, host, file, key, value):
        if not os.path.exists(file):
            raise Exception("Could not find file: " + file)
        with open(file, "r") as source:
            properties = json.load(source)

        properties = json.loads(file)
        if not properties.contains("kkk"):
            pass


# Main entry point
if __name__ == "__main__":
    installer = Installer()
    installer.main()
