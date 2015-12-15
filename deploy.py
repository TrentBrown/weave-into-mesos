#!/usr/bin/env python

# System
import sys
import subprocess
import string
import os
import time

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


class Deployer:

    def main(self):

        # Handle arguments
        self.parse_arguments()
        self.validate_arguments()
        self.process_arguments()

        # Do the deed
        self.deploy()


    def parse_arguments(self):

        # Create an argument parser
        self.parser = configargparse.ArgumentParser(description='Deploy Weave to a Mesos cluster on CentOS 7')

        # Add arguments to the parser
        self.add_mesos_arguments()
        self.add_weave_arguments()

        # Parse arguments out of the command line
        self.args = self.parser.parse_args()


    def add_mesos_arguments(self):

        mesos_group = self.parser.add_argument_group('mesos', 'Mesos')

        # Mesos public slaves
        mesos_group.add_argument(
            "--mesos-public-slaves",
            dest="mesos_public_slaves",
            env_var='MESOS_PUBLIC_SLAVES',
            nargs='*',
            type=str,
            help="Space-separated list of public Mesos slave nodes names"
        )

        # Mesos private slaves
        mesos_group.add_argument(
            "--mesos-private-slaves",
            dest="mesos_private_slaves",
            env_var='MESOS_PRIVATE_SLAVES',
            nargs='*',
            type=str,
            help="Space-separated list of private Mesos slave nodes names"
        )

        # Mesos slave admin username
        mesos_group.add_argument(
            "--mesos_admin",
            dest="mesos_admin",
            env_var='MESOS_ADMIN',
            default="core",
            help="Admin username for Mesos nodes. (default: '%(default)s')"
        )

        # Mesos slave configuration file
        mesos_group.add_argument(
            "--mesos_slave_config_file",
            dest="mesos_slave_config_file",
            env_var='MESOS_SLAVE_CONFIG_FILE',
            default="/etc/default/mesos-slave",
            help="Configuration file for Mesos slaves. (default: %(default)s)"
        )

        # Mesos public slave service name
        mesos_group.add_argument(
            "--mesos_public_slave_service_name",
            dest="mesos_public_slave_service_name",
            env_var='MESOS_PUBLIC_SLAVE_SERVICE_NAME',
            default="????",  # TODO: Find what a vanilla Mesos install uses
            help="Name of Mesos public slave service. TODO: Determine default. (default: %(default)s)"
        )

        # Mesos private slave service name
        mesos_group.add_argument(
            "--mesos_private_slave_service_name",
            dest="mesos_private_slave_service_name",
            env_var='MESOS_PRIVATE_SLAVE_SERVICE_NAME',
            default="????",  # TODO: Find what a vanilla Mesos install uses
            help="Name of Mesos private slave service. TODO: Determine default. (default: %(default)s)"
        )


    def add_weave_arguments(self):

        weave_group = self.parser.add_argument_group('weave', 'Weave')

        # Weave installation directory
        weave_group.add_argument(
            "--weave-install-dir",
            dest="weave_install_dir",
            env_var='WEAVE_INSTALL_DIR',
            default=None,
            help="The directory in which to install Weave. Must be on a writable volume. (default: /home/<mesos_admin>)"
        )

        # Weave components
        self.add_weave_router_arguments()
        self.add_weave_proxy_arguments()


    def add_weave_router_arguments(self):

        weave_router_group = self.parser.add_argument_group('weave-router', 'Weave Router')

        # Weave router IP number allocation range
        weave_router_group.add_argument(
            "--weave-router-ipalloc-range",
            dest="weave_router_ipalloc_range",
            env_var='WEAVE_ROUTER_IPALLOC_RANGE',
            default="10.20.0.0/16",
            help="The range of IP numbers for Weave network nodes in CIDR form. (default: %(default)s)"
        )

        # TODO: Figure out how to specify this
        # Weave DNS domain
        # weave_router_group.add_argument(
        #     "--weave-dns-domain",
        #     dest="weave_dns_domain",
        #     env_var='WEAVE_DNS_DOMAIN',
        #     default="weave",
        #     help="The name to use for DNS names assigned to containers. This becomes: <hostname>.<weave-dns-domain>.local. (default: %(default)s)"
        # )


    def add_weave_proxy_arguments(self):

        weave_proxy_group = self.parser.add_argument_group('weave-proxy', 'Weave Proxy')

        # Weave proxy socket path
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


    def process_arguments(self):

        # Let Weave installation directory default to the home directory of the Mesos admin user
        if self.args.weave_install_dir is None:
            self.args.weave_install_dir = "/home/" + self.args.mesos_admin

        self.weave_bin_dir = self.args.weave_install_dir + "/bin"
        self.weave_tmp_dir = self.args.weave_install_dir + "/tmp"

        weave_router_peers = ' '.join(self.args.mesos_private_slaves + self.args.mesos_public_slaves)

        self.weave_router_substitutions = [
            {'pattern': '{{BIN_DIR}}', 'replacement': self.weave_bin_dir},
            {'pattern': '{{PEERS}}', 'replacement': weave_router_peers},
            {'pattern': '{{IPALLOC_RANGE}}', 'replacement': self.args.weave_router_ipalloc_range}
        ]

        self.weave_proxy_substitutions = [
            {'pattern': '{{BIN_DIR}}', 'replacement': self.weave_bin_dir}
        ]


    def deploy(self):

        # Deploy to public Mesos slaves
        for slave in self.args.mesos_public_slaves:
            self.deploy_slave(slave, is_public=True)

        # Deploy to private Mesos slaves
        for slave in self.args.mesos_private_slaves:
            self.deploy_slave(slave, is_public=False)


    def deploy_slave(self, slave, is_public=False):

        print "------------------------------------------------------------------"
        print "Installing Weave onto Mesos slave: " + slave

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

        # Change the Mesos slave configuration to use the Weave Docker Engine socket proxy
        # TODO: Nothing attempted below has worked. Need help with this.
        # line = "MESOS_DOCKER_SOCKET=" + self.args.weave_proxy_socket
        # file = self.args.mesos_slave_config_file
        # self.add_line_to_file(slave, line, file)
        # self.add_line_to_file(slave, line, "/opt/mesosphere/etc/mesos-slave-common")
        # self.add_line_to_file(slave, line, "/opt/mesosphere/etc/mesos-slave")
        # self.add_line_to_file(slave, line, "/opt/mesosphere/etc/mesos-slave-public")
        # self.add_line_to_file(slave, line, "/etc/default/mesos-slave")

        # self.execute(slave, "sudo install -d " + "/etc/systemd/system/mesos-slave.service.d")
        # self.add_line_to_file(slave, line, "[Service]")
        # self.add_line_to_file(slave, line, "/etc/systemd/system/mesos-slave.service.d/mesos-slave-containerizers.conf")

        # Restart the Mesos slave so it picks up the new configuration
        # if is_public:
        #     service_name = self.args.mesos_public_slave_service_name
        # else:
        #     service_name = self.args.mesos_private_slave_service_name
        # self.execute(slave, "sudo systemctl daemon-reload")
        # self.execute(slave, "sudo systemctl stop " + service_name)
        # time.sleep(5)
        # self.execute(slave, "sudo systemctl start " + service_name)


    # Helpers -----------------------------------------------

    def copy(self, host, src_file, dst_dir, **kwargs):
        filename = os.path.basename(src_file)
        dst_file = self.args.mesos_admin + "@" + host + ":" + dst_dir + "/" + filename
        print "scp " + src_file + " " + dst_file
        do_substitute = 'substitutions' in kwargs
        substituted_file = "/tmp/" + filename
        if do_substitute:
            substitutions = kwargs['substitutions']
            src_file = self.substitute(src_file, substitutions, substituted_file)
        subprocess.call(["scp", src_file, dst_file])
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
        admin_at_host = self.args.mesos_admin + "@" + host
        print "ssh " + admin_at_host + " " + command
        subprocess.call(["ssh", admin_at_host, command])

    def add_line_to_file(self, host, line, file):
        self.execute(host, "sudo touch " + file)
        self.execute(host, "sudo chown root:root " + file)
        self.execute(host, "sudo chmod 644 " + file)
        self.execute(host, "sudo grep -q -F '{0}' {1} || printf '{0}\n' | sudo tee -a {1}".format(line, file))


# Main entry point
if __name__ == "__main__":
    deployer = Deployer()
    deployer.main()
