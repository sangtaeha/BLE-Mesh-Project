from subprocess import Popen, PIPE

p = Popen(["python3", "Script.py", "-d","/dev/ttyACM4"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
output, err = p.communicate()
print("###############################")
print(output)
print("###############################")
print(err)
print("###############################")
while b'SUCCESS' not in output:
    p = Popen(["python3", "Script.py", "-d","/dev/ttyACM4"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output, err = p.communicate()
    print("###############################")
    print(output)
    print("###############################")
    print(err)
    print("###############################")
