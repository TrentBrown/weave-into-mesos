#!/usr/bin/env python

# System
import sys
from subprocess import call
import string
import os
import pwd
import grp
import json
from distutils.util import strtobool
import re


# Third Party
import configargparse


class Installer:

    FLAVOR_VANILLA = "vanilla"
    FLAVOR_DCOS = "dcos"

    def main(self):

        # Handle arguments
        self.parse_arguments()
        self.default_arguments()
        self.process_arguments()

        # Make sure the Weave executable was downloaded
        if not os.path.exists("weave"):
            raise ValueError("Weave executable has not been downloaded yet. Use 'make setup' to get it.")

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
            env_var='WIM_TMP_DIR',
            default="/tmp",
            help="Path for a local temporary directory. (default: '%(default)s')"
        )

        # Skip warnings?
        self.parser.add_argument(
            "--skip-warnings",
            dest="skip_warnings",
            env_var='WIM_SKIP_WARNINGS',
            type=str,
            default="False",
            help="Skip warnings about proceeding with installation at various points. (default: '%(default)s')"
        )


    def add_mesos_arguments(self):

        mesos_group = self.parser.add_argument_group('mesos', 'Mesos')

        # Flavor
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
            type=str,
            help="List of addresses of public Mesos slave nodes. Delimited by commas, colons, semicolons, pipes, or whitespace."
        )
        mesos_group.add_argument(
            "--mesos-private-slaves",
            dest="mesos_private_slaves",
            env_var='MESOS_PRIVATE_SLAVES',
            type=str,
            help="List of addresses of private Mesos slave nodes. Delimited by commas, colons, semicolons, pipes, or whitespace."
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

        # ipalloc-range
        weave_router_group.add_argument(
            "--weave-router-ipalloc-range",
            dest="weave_router_ipalloc_range",
            env_var='WEAVE_ROUTER_IPALLOC_RANGE',
            help="The range of IP numbers for Weave network nodes in CIDR form. (Weave default: 10.32.0.0/12)"
        )

        # dns-domain
        weave_router_group.add_argument(
            "--weave-router-dns-domain",
            dest="weave_router_dns_domain",
            env_var='WEAVE_ROUTER_DNS_DOMAIN',
            help="The name to use for DNS names assigned to containers. If you override the default, be sure to set your container hostnames to match. (Weave default: weave.local)"
        )

        # password
        weave_router_group.add_argument(
            "--weave-router-password",
            dest="weave_router_password",
            env_var='WEAVE_ROUTER_PASSWORD',
            help="Router password"
        )

        # nickname
        weave_router_group.add_argument(
            "--weave-router-nickname",
            dest="weave_router_nickname",
            env_var='WEAVE_ROUTER_NICKNAME',
            help="Router nickname"
        )

        # init-peer-count
        weave_router_group.add_argument(
            "--weave-router-init-peer-count",
            dest="weave_router_init_peer_count",
            env_var='WEAVE_ROUTER_INIT_PEER_COUNT',
            help="Router initial peer count"
        )


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

        # with-dns/without-dns
        with_dns_parser = weave_proxy_group.add_mutually_exclusive_group(required=False)
        with_dns_parser.add_argument(
            '--weave-proxy-with-dns',
            dest='weave_proxy_dns',
            env_var='WEAVE_PROXY_WITH_DNS',
            action='store_true',
            help="Use Weave DNS."
        )
        with_dns_parser.add_argument(
            '--weave-proxy-without-dns',
            dest='weave_proxy_dns',
            env_var='WEAVE_PROXY_WITHOUT_DNS',
            action='store_false',
            help="Do not use Weave DNS."
        )
        weave_proxy_group.set_defaults(weave_proxy_dns=True)

        # hostname-from-label
        weave_proxy_group.add_argument(
            "--weave-proxy-hostname-from-label",
            dest="weave_proxy_hostname_from_label",
            env_var='WEAVE_PROXY_HOSTNAME_FROM_LABEL',
            help="Hostname label."
        )

        # hostname-match
        weave_proxy_group.add_argument(
            "--weave-proxy-hostname-match",
            dest="weave_proxy_hostname_match",
            env_var='WEAVE_PROXY_HOSTNAME_MATCH',
            help="Hostname match."
        )

        # hostname-replacement
        weave_proxy_group.add_argument(
            "--weave-proxy-hostname-replacement",
            dest="weave_proxy_hostname_replacement",
            env_var='WEAVE_PROXY_HOSTNAME_REPLACEMENT',
            help="Hostname replacement."
        )


    def is_valid_mesos_flavor(self, name):
        if name == Installer.FLAVOR_VANILLA:
            return True
        if name == Installer.FLAVOR_DCOS:
            return True
        return False


    def default_arguments(self):

        # Vanilla flavor
        if self.args.mesos_flavor == Installer.FLAVOR_VANILLA:
            self.default_arguments_vanilla()

        # DCOS flavor
        elif self.args.mesos_flavor == Installer.FLAVOR_DCOS:
            self.default_arguments_dcos()

        # Let Weave installation directory default to the home directory of the Mesos admin user
        if self.args.weave_install_dir is None:
            self.args.weave_install_dir = "/home/" + self.args.mesos_admin_username


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

        # Parse slave node lists
        self.mesos_public_slaves = parse_delimited_list(self.args.mesos_public_slaves)
        self.mesos_private_slaves = parse_delimited_list(self.args.mesos_private_slaves)

        # Make sure at least one slave node was specified
        if (len(self.mesos_public_slaves) == 0 and len(self.mesos_private_slaves) == 0):
            raise ValueError("You must specify at least one Mesos slave node using --mesos-public-slaves or --mesos_private_slaves")

        # If either weave-proxy-hostname-match or weave-proxy-hostname-replacement were specified, make sure that both were
        weave_proxy_hostname_match_specified = (not self.args.weave_proxy_hostname_match is None)
        weave_proxy_hostname_replacement_specified = (not self.args.weave_proxy_hostname_replacement is None)
        one_specified = (weave_proxy_hostname_match_specified or weave_proxy_hostname_replacement_specified)
        both_specified = (weave_proxy_hostname_match_specified and weave_proxy_hostname_replacement_specified)
        if one_specified and not both_specified:
            raise ValueError("You must specify both --weave-proxy-hostname-match and --weave-proxy-hostname-replacement (or neither)")

        # Validate the Mesos "flavor"
        if not self.is_valid_mesos_flavor(self.args.mesos_flavor):
            raise ValueError("Invalid mesos-flavor: " + self.args.mesos_flavor)

        # Build directory paths for use later
        self.weave_bin_dir = self.args.weave_install_dir + "/bin"
        self.weave_tmp_dir = self.args.weave_install_dir + "/tmp"

        # Append "." to DNS domain, if it's not already there
        if not self.args.weave_router_dns_domain is None and not self.args.weave_router_dns_domain.endswith("."):
            self.args.weave_router_dns_domain += "."

        # Map skip-warnings string to boolean
        self.skip_warnings = is_truthy(self.args.skip_warnings)

        # Build the Weave systemd service file substitution maps
        self.build_weave_router_substitutions()
        self.build_weave_proxy_substitutions()


    def build_weave_router_substitutions(self):

        substitutions = []

        self.append_substitution(substitutions, "{{BIN_DIR}}", self.weave_bin_dir)
        weave_router_peers = ' '.join(self.mesos_private_slaves + self.mesos_public_slaves)
        self.append_substitution(substitutions, "{{PEERS}}", weave_router_peers)
        self.append_substitution(substitutions, "{{IPALLOC_RANGE}}", self.args.weave_router_ipalloc_range, option="--ipalloc-range")
        self.append_substitution(substitutions, "{{DNS_DOMAIN}}", self.args.weave_router_dns_domain, option="--dns-domain")
        self.append_substitution(substitutions, "{{PASSWORD}}", self.args.weave_router_password, option="--password")
        self.append_substitution(substitutions, "{{NICKNAME}}", self.args.weave_router_nickname, option="--nickname")
        self.append_substitution(substitutions, "{{INIT_PEER_COUNT}}", self.args.weave_router_init_peer_count, option="--init-peer-count")

        self.weave_router_substitutions = substitutions


    def build_weave_proxy_substitutions(self):

        substitutions = []

        self.append_substitution(substitutions, "{{BIN_DIR}}", self.weave_bin_dir)
        if self.args.weave_proxy_dns:
            value = "--with-dns"
        else:
            value = "--without-dns"
        self.append_substitution(substitutions, "{{WITH_DNS}}", value)
        self.append_substitution(substitutions, "{{HOSTNAME_FROM_LABEL}}", self.args.weave_proxy_hostname_from_label, option="--hostname-from-label")
        self.append_substitution(substitutions, "{{HOSTNAME_MATCH}}", self.args.weave_proxy_hostname_match, option="--hostname-match")
        self.append_substitution(substitutions, "{{HOSTNAME_REPLACEMENT}}", self.args.weave_proxy_hostname_replacement, option="--hostname-replacement")

        self.weave_proxy_substitutions = substitutions


    def append_substitution(self, substutitions, pattern, value, **kwargs):
        if value is None:
            replacement = ""
        elif 'option' in kwargs:
            replacement = kwargs['option'] + " " + value
        else:
            replacement = value
        substutitions.append({'pattern': pattern, 'replacement': replacement})


    def install(self):

        # Install to public Mesos slaves
        for slave in self.mesos_public_slaves:
            self.install_into_slave(slave, is_public=True)

        # Install to private Mesos slaves
        for slave in self.mesos_private_slaves:
            self.install_into_slave(slave, is_public=False)


    def install_into_slave(self, slave, is_public=False):

        print "------------------------------------------------------------------"
        print "Installing Weave into Mesos slave: " + slave

        # Make sure target directories exist
        self.execute_remotely(slave, "sudo install -d " + self.weave_tmp_dir)
        self.execute_remotely(slave, "sudo install -d " + self.weave_bin_dir)

        # Install Weave executable
        self.copy_file_local_to_remote(
            slave,
            "./weave",
            self.weave_bin_dir + "/",
            mode=0755,
            user="root", group="root"
        )

        # Install Weave services
        self.copy_file_local_to_remote(
            slave,
            "./weave.target",
            "/etc/systemd/system/",
            mode=0644,
            user="root", group="root"
        )
        self.copy_file_local_to_remote(
            slave,
            "./weave-router.service",
            "/etc/systemd/system/",
            mode=0644,
            user="root", group="root",
            substitutions=self.weave_router_substitutions
        )
        self.copy_file_local_to_remote(
            slave,
            "./weave-proxy.service",
            "/etc/systemd/system/",
            mode=0644,
            user="root", group="root",
            substitutions=self.weave_proxy_substitutions
        )

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
        value = "unix://" + self.args.weave_proxy_socket
        self.add_property_to_remote_json_file(
            slave,
            self.args.mesos_slave_executor_env_file,
            key, value,
            mode=0644,
            user="root", group="root"
        )

        # Restart the Mesos slave so it picks up the new configuration
        # TODO: Is there a more graceful way to do this? Currently orphans containers running under Marathon (eg. Chronos).
        # TODO: This looks relevant: https://issues.apache.org/jira/browse/MESOS-1474
        if not self.proceed("Are you sure you want to restart Mesos slave " + slave + "?"):
            exit(0)
        if is_public:
            service_name = self.args.mesos_slave_service_name_public
        else:
            service_name = self.args.mesos_slave_service_name_private
        self.execute_remotely(slave, "sudo systemctl daemon-reload")
        self.execute_remotely(slave, "sudo systemctl stop " + service_name)
        self.execute_remotely(slave, "sudo systemctl start " + service_name)


    # Helpers -----------------------------------------------

    def execute_remotely(self, host, command):

        # Print description
        description = "Executing remotely: " + command
        print description

        # Execute command with "ssh"
        admin_at_host = self.args.mesos_admin_username + "@" + host
        result = call(["ssh", admin_at_host, command])
        if result is not 0:
            raise Exception("Remote execution failed with code: " + str(result))


    def copy_file_remote_to_local(self, host, remote_file_path, local_path, **kwargs):

        # Build local file path
        file_name = os.path.basename(remote_file_path)
        if local_path.endswith("/"):
            local_file_path = local_path + file_name
        else:
            local_file_path = local_path

        # Print description
        description = "Copying remote file to local: " + remote_file_path + " ---> " + local_file_path
        print description

        # Make a copy of the remote file on the remote machine (because scp alone can't get sudoer access to it)
        remote_tmp_file_path = self.weave_tmp_dir + "/" + file_name
        self.execute_remotely(host, "sudo cp -f " + remote_file_path + " " + remote_tmp_file_path)

        # Copy the file with "scp"
        user_at_host = self.args.mesos_admin_username + "@" + host + ":"
        result = call(["scp", user_at_host + remote_tmp_file_path, local_file_path])
        if result is not 0:
            raise Exception("Copying file from remote failed with code: " + str(result))

        # Set mode of local file, if provided
        if 'mode' in kwargs:
            mode = kwargs['mode']
            os.chmod(local_file_path, mode)

        # Set ownership of local file, if provided
        uid = -1
        gid = -1
        if 'user' in kwargs:
            user = kwargs['user']
            uid = pwd.getpwnam(user).pw_uid
        if 'group' in kwargs:
            group = kwargs['group']
            gid = grp.getgrnam(group).gr_gid
        if uid != -1 or gid != -1:
            os.chown(local_file_path, uid, gid)

        # Clean up
        self.execute_remotely(host, "rm -f " + remote_tmp_file_path)


    def copy_file_local_to_remote(self, host, local_file_path, remote_path, **kwargs):
        
        # Build remote file path
        file_name = os.path.basename(local_file_path)
        if remote_path.endswith("/"):
            remote_file_path = remote_path + file_name
        else:
            remote_file_path = remote_path

        # Print description
        description = "Copying local file to remote: " + local_file_path + " ---> " + remote_file_path
        print description
        
        # Do substitutions, if specified, in a local copy of the file
        do_substitute = 'substitutions' in kwargs
        substituted_file_path = self.args.local_tmp_dir + "/" + file_name
        if do_substitute:
            substitutions = kwargs['substitutions']
            local_file_path = substitute(local_file_path, substitutions, substituted_file_path)

        # Copy the file with "scp" to a remote temporary file (because scp alone can't get sudoer access)
        remote_tmp_file_path = self.weave_tmp_dir + "/" + file_name
        user_at_host = self.args.mesos_admin_username + "@" + host + ":"
        result = call(["scp", local_file_path, user_at_host + remote_tmp_file_path])
        if result is not 0:
            raise Exception("Copying file to remote failed with code: " + str(result))

        # Copy the remote temporary file into place with sudoer access
        self.execute_remotely(host, "sudo cp -f " + remote_tmp_file_path + " " + remote_file_path)

        # Set mode of remote file, if provided
        if 'mode' in kwargs:
            mode = kwargs['mode']
            self.execute_remotely(host, "sudo chmod " + oct(mode) + " " + remote_file_path)

        # Set ownership of remote file, if provided
        ownership = ""
        if 'user' in kwargs:
            user = kwargs['user']
            ownership += user
        if 'group' in kwargs:
            group = kwargs['group']
            ownership += ":" + group
        if ownership != "":
            self.execute_remotely(host, "sudo chown " + ownership + " " + remote_file_path)

        # Clean up
        self.execute_remotely(host, "rm -f " + remote_tmp_file_path)
        if do_substitute:
            os.remove(substituted_file_path)


    def add_property_to_remote_json_file(self, host, remote_file_path, key, value, **kwargs):

        # Get a local copy of the remote JSON file
        file_name = os.path.basename(remote_file_path)
        local_file_path = self.args.local_tmp_dir + "/" + file_name
        self.copy_file_remote_to_local(host, remote_file_path, local_file_path)

        # Load JSON from local file
        with open(local_file_path, "r") as source:
            properties = json.load(source)

        # Add the given property to the JSON, if it's not already there
        if not key in properties:
            properties[key] = value

        # Save JSON back to local file
        with open(local_file_path, "w") as sink:
            json.dump(properties, sink)

        # Replace the remote JSON file with the local one
        self.copy_file_local_to_remote(host, local_file_path, remote_file_path, **kwargs)

        # Clean up
        os.remove(local_file_path)


    def proceed(self, warning):

        if self.skip_warnings:
            return True

        sys.stdout.write('%s [y/n]\n' % warning)
        while True:
            try:
                return strtobool(raw_input().lower())
            except ValueError:
                sys.stdout.write('Please respond with \'y\' or \'n\'.\n')


def substitute(file_path, substitutions, substituted_file_path):
    with open(file_path, "r") as source:
        content = source.read()
    for substitution in substitutions:
        pattern = substitution['pattern']
        replacement = substitution['replacement']
        content = string.replace(content, pattern, replacement)
    with open(substituted_file_path, "w") as sink:
        sink.write(content)
    return substituted_file_path


def parse_delimited_list(string):

    if string is None:
        return []

    # Trim leading and trailing whitespace
    string = string.strip()

    if string == "":
        return []

    # Split on delimiters
    pattern = re.compile(r'\s*,\s*|\s*:\s*|\s*;\s*|\s*')  # Comma, pipe, colon, semicolon, or whitespace
    list = re.split(pattern, string)

    return list


def is_truthy(string):
    return string.lower() in ['true', 'yes', '1', 't', 'y']


# Main entry point
if __name__ == "__main__":
    installer = Installer()
    installer.main()
