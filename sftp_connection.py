import shutil
from paramiko.client import SSHClient
from paramiko.hostkeys import HostKeyEntry
from paramiko.ssh_exception import AuthenticationException

############################################################################################################

def SftpConnection(keepass_db, keepass_entry, file_directory, file_extension, remote_path='remote_directory'):
    """
    After generating files, uploads files via SFTP and moves files to Uploaded folder
    :param keepass_db: keepass database with SFTP credentials
    :param keepass_entry: keepass entry title for TPA SFTP credentials
    :param file_directory: path for file exporting location
    :param file_extension: file extension for exported files
    :param log: dictionary for logging that updated in the generating files function
    :param remote_path: additional keepass attribute for sftp path defaulted to remote_directory
    :return: SUCCESS or which error occurred
    """
    keepass_entry = keepass_db.find_entries(title=keepass_entry, first=True)

    username = keepass_entry.username
    password = keepass_entry.password
    hostname = keepass_entry.url
    remote_directory = keepass_entry.custom_properties[remote_path]
    # search for known_hosts.txt attachment, decode, and grab first line available in case multiple lines
    # known_hosts.txt was created by opening Windows Command Prompt and running "ssh-keyscan hostname > known_hosts.txt"
    known_hosts = keepass_db.find_attachments(element=keepass_entry, filename='known_hosts.txt', first=True)
    public_keys = known_hosts.data.decode()
    public_key = public_keys.split('\n')[0]

    try:
        # create an ssh client / "console"
        ssh_client = SSHClient()
        # create a hostkey entry using public key and add to client
        hostkey_entry = HostKeyEntry.from_line(public_key)
        ssh_client._host_keys._entries.append(hostkey_entry)
        # connect to the remote server and open a sftp session
        ssh_client.connect(username=username, password=password, hostname=hostname)
        sftp_client = ssh_client.open_sftp()
        sftp_client.chdir(remote_directory)
        try:
            exported_files = file_directory.glob(file_extension)
            for file in exported_files:
                sftp_client.put(localpath=file,
                                remotepath=file.name)
                # log[file.name]['is_uploaded'] = True
                shutil.move(file, file_directory.joinpath('sent').joinpath(file.name))
            sftp_client.close()
        except PermissionError as err:
            failed_exported_files = file_directory.glob(file_extension)
            # for file in failed_exported_files:
            # log[file.name]['failure_step'] = f'SFTP Operation Failed: ({str(err)}) due to a permissions error on the remote server'
            return f'SFTP Operation Failed: ({str(err)}) due to a permissions error on the remote server'
        except Exception as err:
            failed_exported_files = file_directory.glob(file_extension)
            # for file in failed_exported_files:
            # log[file.name]['failure_step'] = f'SFTP failed due to other error ({str(err)})'
            return f'SFTP failed due to other error ({str(err)})'
        sftp_client.close()

    except AuthenticationException as err:
        failed_exported_files = file_directory.glob(file_extension)
        # for file in failed_exported_files:
        # log[file.name]['failure_step'] = f'Cannot connect due to authentication error ({str(err)})'
        return f'Cannot connect due to authentication error ({str(err)})'
    except Exception as err:
        failed_exported_files = file_directory.glob(file_extension)
        # for file in failed_exported_files:
        # log[file.name]['failure_step'] = f'Cannot connect due to other error ({str(err)})'
        return f'Cannot connect due to other error ({str(err)})'
    return 'SUCCESS'
