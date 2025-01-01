from string import Template
import subprocess

def get_commande(output="output.jpg", image_sorting="$(ls *.jpeg | gshuf)", back_ground="black", geometry=[-30, -30], size=[1024, 1024]):
    geometry = "".join(map(str, geometry))
    size = "x".join(map(str, size))
    command = Template("montage $image_sorting -auto-orient -background $back_ground +polaroid -shadow -geometry $geometry miff:- | convert miff:- -resize $size $output")
    return command.substitute(image_sorting=image_sorting, back_ground=back_ground, geometry=geometry, size=size, output=output)


def run_subprocess(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    process.wait()
    return process.returncode
