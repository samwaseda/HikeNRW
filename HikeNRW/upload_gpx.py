import paramiko
import os
import tempfile


def upload(file_content, file_name):
    remote_file_path = f"public_html/HIKING/{file_name}"  # Path where you want to place the file on the remote server
    # Initialize the SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        # Connect to the server
        ssh.connect(
            hostname=os.environ["WEB_HOST"],
            username=os.environ["WEB_USER"],
            key_filename=os.path.expanduser('~/.ssh/id_rsa')
        )

        # Use SFTP to transfer the file
        sftp = ssh.open_sftp()

        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=True) as temp_file:
            temp_file.write(file_content)
            temp_file.flush()  # Ensure content is written to disk
            sftp.put(temp_file.name, remote_file_path)

        print(f"File '{local_file_path}' successfully uploaded to '{remote_file_path}'")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the SFTP session and SSH connection
        sftp.close()
        ssh.close()
    return "https://www.{}/HIKING/{}".format(os.environ["WEB_HOST"], file_name)
