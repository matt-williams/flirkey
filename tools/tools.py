import array
import glob
import math

def loadPPM(filename):
  with open(filename, "r") as file:
    data = file.read().split()[4:]
    return [int(data[i]) for i in range(0, len(data), 3)]

def savePPM(filename, data):
  with open(filename, "w") as file:
    file.write("P3 80 60 65535\n")
    for y in range(0, len(data) / 80):
      for x in range(0, 80):
        file.write("%u %u %u " % (data[x + y * 80], data[x + y * 80], data[x + y * 80]))
      file.write("\n")

def saveC(filename, variable, data):
  with open(filename, "w") as file:
    file.write("short %s[] = {\n" % (variable,))
    for y in range(0, len(data) / 80):
      for x in range(0, 80):
        file.write("%u, " % (data[x + y * 80] - 32768,))
      file.write("\n")
    file.write("};\n")

def loadAllPPM(pathname):
  return [loadPPM(filename) for filename in sorted(glob.glob(pathname))]

def balance(data):
  offset = min(data)
  scale = 65535.0 / dataRange(data)
  return [(x - offset) * scale for x in data]

def dataRange(data):
  return max(data) - min(data)

def median(data):
  return max(data) + min(data) / 2

def mean(data):
  return sum(data) / len(data)

def meanAll(data):
  return map(mean, zip(*data))

def stdDevAll(data):
  meanOfSquares = meanAll([[x * x for x in l] for l in data])
  squareOfMeans = [x * x for x in meanAll(data)]
  return map(lambda (x, y): math.sqrt(x - y), zip(meanOfSquares, squareOfMeans))

def difference(signal, base):
  return map(lambda (s, b): (s - b) / 2 + 32768, zip(signal, base))

def convolve(a, b):
  return map(lambda (x, y): ((x - 32768) * (y - 32768)) / 32768 + 32768, zip(a, b))

def adjustForStdDev(data, stdDev):
  return map(lambda (s, d): math.copysign(max(abs(s - 32768), 0), s - 32768) + 32768, zip(data, stdDev))

def main():
  null = meanAll([balance(l) for l in loadAllPPM("../training-data/raw/_.*.ppm")])
  savePPM("../training-data/processed/_.ppm", null)
  saveC("../training-data/processed/data_null.c", "data_null", null)
  
  data = {}
  for c in ['a', 'b', 'c', 'd', 'e', 'f', 'i', 'o', 'u']:
    data[c] = [balance(l) for l in loadAllPPM("../training-data/raw/%c.*.ppm" % (c,))]
    data[c] = adjustForStdDev(difference(meanAll(data[c]), null), stdDevAll(data[c]))
    
    savePPM("../training-data/processed/%c.ppm" % (c,), data[c])
    saveC("../training-data/processed/data_%c.c" % (c,), "data_%c" % (c,), data[c])

  test(null, data)
  
def test(null, data):
  img = balance(loadPPM("../training-data/raw/u.00001.ppm"))
  diff = difference(img, null)
  for c in ['a', 'b', 'c', 'd', 'e', 'f', 'i', 'o', 'u']:
    print c, mean(convolve(diff, data[c])) - 32768

main()
