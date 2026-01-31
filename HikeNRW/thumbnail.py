from string import Template
import subprocess


def get_command(
    images,
    output="output.jpg",
    back_ground="black",
    geometry=[-30, -30],
    size=[1024, 1024],
):
    geometry = "".join(map(str, geometry))
    size = "x".join(map(str, size))
    img = " ".join(images)
    command = Template(
        "montage $img -auto-orient -background $back_ground +polaroid -shadow -geometry $geometry miff:- | convert miff:- -resize $size $output"
    )
    return command.substitute(
        img=img, back_ground=back_ground, geometry=geometry, size=size, output=output
    )


def run_subprocess(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    process.wait()
    return process.returncode
