import paramiko
import os
import tempfile


def upload(file_content, file_name):
    remote_file_path = f"public_html/HIKING/{file_name}.gpx"  # Path where you want to place the file on the remote server
    # Initialize the SSH client
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # Connect to the server
        folder = '~/.ssh/id_rsa'
        # check folder exists and if not, use ~/.ssh/id_ed25519
        if not os.path.exists(os.path.expanduser(folder)):
            folder = '~/.ssh/id_ed22519'
        ssh.connect(
            hostname=os.environ["WEB_HOST"],
            username=os.environ["WEB_USER"],
            key_filename=os.path.expanduser(folder),
            port=222
        )

        # Use SFTP to transfer the file
        sftp = ssh.open_sftp()

        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=True) as temp_file:
            temp_file.write(file_content)
            temp_file.flush()  # Ensure content is written to disk
            sftp.put(temp_file.name, remote_file_path)

    except Exception as e:
        print(f"An error occurred: {e}")


    finally:
        # Close the SFTP session and SSH connection
        sftp.close()
        ssh.close()
    return "https://www.{}/HIKING/{}.gpx".format(os.environ["WEB_HOST"], file_name)
