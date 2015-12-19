#!/usr/bin/env python

# System
import sys
from subprocess import call
import string
import os
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
        self.add_common_arguments()
        self.add_mesos_arguments()
        self.add_weave_arguments()

        # Parse arguments out of the command line
        self.args = self.parser.parse_args()


    def add_common_arguments(self):

        # Local temporary directory
        self.parser.add_argument(
            "--local-tmp-dir",
            dest="local_tmp_dir",
            env_var='LOCAL_TMP_DIR',
            default="/tmp",
            help="Path for a local temporary directory"
        )


    def add_mesos_arguments(self):

        mesos_group = self.parser.add_argument_group('mesos', 'Mesos')

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

        # Executor environment file
        mesos_group.add_argument(
            "--mesos-slave-executor-env-file",
            dest="mesos_slave_executor_env_file",
            env_var='MESOS_SLAVE_EXECUTOR_ENV_FILE',
            help="Path for the Mesos executor environment config file. (default: Determined by 'flavor')"
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
        # if self.args.mesos_slave_service_name_public is None:
        #     self.args.mesos_slave_service_name_public = "TBD"
        # if self.args.mesos_slave_service_name_private is None:
        #     self.args.mesos_slave_service_name_private = "TBD"
        # if self.args.mesos_slave_executor_env_file is None:
        #     self.args.mesos_slave_executor_env_file = "TBD"


    def default_arguments_dcos(self):
        if self.args.mesos_admin_username is None:
            self.args.mesos_admin_username = "core"
        if self.args.mesos_slave_service_name_public is None:
            self.args.mesos_slave_service_name_public = "dcos-mesos-slave-public.service"
        if self.args.mesos_slave_service_name_private is None:
            self.args.mesos_slave_service_name_private = "dcos-mesos-slave.service"
        if self.args.mesos_slave_executor_env_file is None:
            self.args.mesos_slave_executor_env_file = "/opt/mesosphere/etc/mesos-executor-environment.json"


    def process_arguments(self):

        # Build directory paths for use later
        self.weave_bin_dir = self.args.weave_install_dir + "/bin"
        self.weave_tmp_dir = self.args.weave_install_dir + "/tmp"

        # Let Weave installation directory default to the home directory of the Mesos admin user
        if self.args.weave_install_dir is None:
            self.args.weave_install_dir = "/home/" + self.args.mesos_admin_username

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
        self.execute_remotely(slave, "sudo install -d " + self.weave_tmp_dir)
        self.execute_remotely(slave, "sudo install -d " + self.weave_bin_dir)

        # Install Weave executable
        self.copy_file_local_to_remote(slave, "weave", self.weave_tmp_dir)
        self.execute_remotely(slave, "sudo install -g root -o root -m 0755 " + self.weave_tmp_dir + "/weave " + self.weave_bin_dir + "/")

        # Install Weave services
        self.copy_file_local_to_remote(slave, "weave.target", self.weave_tmp_dir)
        self.copy_file_local_to_remote(slave, "weave-router.service", self.weave_tmp_dir, substitutions=self.weave_router_substitutions)
        self.copy_file_local_to_remote(slave, "weave-proxy.service", self.weave_tmp_dir, substitutions=self.weave_proxy_substitutions)
        self.execute_remotely(slave, "sudo install -g root -o root -m 0644 " + self.weave_tmp_dir + "/weave.target /etc/systemd/system/")
        self.execute_remotely(slave, "sudo install -g root -o root -m 0644 " + self.weave_tmp_dir + "/weave-router.service /etc/systemd/system/")
        self.execute_remotely(slave, "sudo install -g root -o root -m 0644 " + self.weave_tmp_dir + "/weave-proxy.service /etc/systemd/system/")

        # Enable Weave services, so they'll start at boot
        self.execute_remotely(slave, "sudo systemctl enable weave-router.service")
        self.execute_remotely(slave, "sudo systemctl enable weave-proxy.service")

        # Start (or restart) Weave services
        self.execute_remotely(slave, "sudo systemctl stop weave-router.service")
        self.execute_remotely(slave, "sudo systemctl start weave-router.service")
        self.execute_remotely(slave, "sudo systemctl stop weave-proxy.service")
        self.execute_remotely(slave, "sudo systemctl start weave-proxy.service")

        # Install weave proxy socket into Mesos slave
        key = "DOCKER_HOST"
        value = "unix:///var/run/weave/weave.sock"
        self.add_property_to_remote_json_file(slave, self.args.mesos_slave_executor_env_file, key, value)

        # Restart the Mesos slave so it picks up the new configuration
        if is_public:
            service_name = self.args.mesos_slave_service_name_public
        else:
            service_name = self.args.mesos_slave_service_name_private
        self.execute_remotely(slave, "sudo systemctl daemon-reload")
        self.execute_remotely(slave, "sudo systemctl stop " + service_name)
        self.execute_remotely(slave, "sudo systemctl start " + service_name)


    # Helpers -----------------------------------------------

    def copy_file_local_to_remote(self, host, local_file_path, remote_dir_path, **kwargs):
        
        # Build remote file path
        file_name = os.path.basename(local_file_path)
        remote_file_path = remote_dir_path + "/" + file_name
        
        # Print description
        description = "Copying file local to remote: " + local_file_path + " ---> " + remote_file_path
        print description
        
        # Do substitutions, if specified
        do_substitute = 'substitutions' in kwargs
        substituted_file_path = self.args.local_tmp_dir + "/" + file_name
        if do_substitute:
            substitutions = kwargs['substitutions']
            local_file_path = self.substitute(local_file_path, substitutions, substituted_file_path)
        
        # Copy the file with "scp"
        user_at_host = self.args.mesos_admin_username + "@" + host + ":"
        result = call(["scp", local_file_path, user_at_host + remote_file_path])
        if result is not 0:
            raise Exception("Copying file to remote failed with code: " + str(result))
        
        # Clean up
        if do_substitute:
            os.remove(substituted_file_path)


    def copy_file_remote_to_local(self, host, remote_file_path, local_dir_path):
        
        # Build local file path
        file_name = os.path.basename(remote_file_path)
        local_file_path = local_dir_path + "/" + file_name

        # Print description
        description = "Copying file remote to local: " + remote_file_path + " ---> " + local_file_path
        print description

        # Copy the file with "scp"
        user_at_host = self.args.mesos_admin_username + "@" + host + ":"
        result = call(["scp", user_at_host + remote_file_path, local_file_path])
        if result is not 0:
            raise Exception("Copying file from remote failed with code: " + str(result))


    def substitute(self, file_path, substitutions, substituted_file_path):
        with open(file_path, "r") as source:
            content = source.read()
        for substitution in substitutions:
            pattern = substitution['pattern']
            replacement = substitution['replacement']
            content = string.replace(content, pattern, replacement)
        with open(substituted_file_path, "w") as sink:
            sink.write(content)
        return substituted_file_path


    def execute_remotely(self, host, command):

        # Print description
        description = "Executing remotely: " + command
        print description

        # Execute command with "ssh"
        admin_at_host = self.args.mesos_admin_username + "@" + host
        result = call(["ssh", admin_at_host, command])
        if result is not 0:
            raise Exception("Remote execution failed with code: " + str(result))


    def add_line_to_remote_file(self, host, line, file_path):
        self.execute_remotely(host, "sudo touch " + file_path)
        self.execute_remotely(host, "sudo chown root:root " + file_path)
        self.execute_remotely(host, "sudo chmod 644 " + file_path)
        self.execute_remotely(host, "sudo grep -q -F '{0}' {1} || printf '{0}\n' | sudo tee -a {1}".format(line, file_path))


    def add_property_to_remote_json_file(self, host, remote_file_path, key, value):

        # Get a local copy of the remote JSON file
        file_name = os.path.basename(remote_file_path)
        local_file_path = self.args.local_tmp_dir + "/" + file_name
        self.copy_file_remote_to_local(host, remote_file_path, self.args.local_tmp_dir)

        # Load JSON from local file
        with open(local_file_path, "r") as source:
            properties = json.load(source)

        # Add the given property to the JSON, if it's not already there
        if not hasattr(properties, key):
            setattr(properties, key, value)

        # Save JSON back to local file
        with open(local_file_path, "w") as sink:
            json.dump(properties, sink)

        # Replace the remote JSON file with the local one
        remote_dir_path = os.path.dirname(remote_file_path)
        self.copy_file_local_to_remote(host, local_file_path, remote_dir_path)

        # Clean up
        os.remove(local_file_path)


# Main entry point
if __name__ == "__main__":
    installer = Installer()
    installer.main()
