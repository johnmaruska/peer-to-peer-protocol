import subprocess, os
#Total command would be "split -n [number_of_file] input.pdf ./temp/

#def split_file(self, filename, number_of_file):
command = "split -n"
number_of_file = 10
command += " " + str(number_of_file)
filename = "input.pdf"
suffix = "./temp/"
command += " " + filename + " " + suffix
p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
file = os.listdir('./temp')
os.chdir("./temp")
p = subprocess.Popen("cat * >> input.pdf", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
print (file)
