import os

file = open("sample.txt", "rb")
size = file.tell()
length = size / 10
for i in xrange(0,10):
    file.seek(i * length, 0)
    stri = file.read(size)
    print len(stri)