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

def stdDev(data):
  meanOfSquares = mean([x * x for x in data])
  squareOfMeans = mean(data) * mean(data)
  return math.sqrt(meanOfSquares - squareOfMeans)

def stdDevAll(data):
  meanOfSquares = meanAll([[x * x for x in l] for l in data])
  squareOfMeans = [x * x for x in meanAll(data)]
  return map(lambda (x, y): math.sqrt(x - y), zip(meanOfSquares, squareOfMeans))

def difference(signal, base):
  return map(lambda (s, b): (s - b) / 2 + 32768, zip(signal, base))

def convolve(a, b):
  return map(lambda (x, y): ((x - 32768) * (y - 32768)) / 32768 + 32768, zip(a, b))

def adjustForStdDev(data, stdDev):
  #return map(lambda (d, s): ((d - 32768) / (int(s / 255) + 1)) + 32768, zip(data, stdDev))
  return map(lambda (d, s): math.copysign(max(abs(d - 32768) - s, 0), d - 32768) + 32768, zip(data, stdDev))

def normalize(l):
  scalar = 4096.0 / stdDev(l)
  return [(x - 32768) * scalar + 32768 for x in l]

POSES = ['_', 'a', 'b', 'c', 'd', 'e', 'f', 'i', 'o', 'u']

def main():
  dataIn = {}
  for c in POSES:
    dataIn[c] = [balance(l) for l in loadAllPPM("../training-data/raw/%c.*.ppm" % (c,))]
  base = meanAll([item for sublist in [dataIn[p] for p in POSES] for item in sublist])
  savePPM("data_base.ppm", base)
  saveC("../training-data/processed/data_base.c", "data_base", base)

  data = {}
  for c in POSES:
    not_c = filter(lambda x: x != c, POSES)
    data_not_c = [dataIn[p] for p in not_c]
    data_not_c = [item for sublist in data_not_c for item in sublist]
    data[c] = difference(meanAll(dataIn[c]), meanAll(data_not_c))
    
    average = mean(data[c]) 
    data[c] = [d - (average - 32768) for d in data[c]]
    data[c] = normalize(data[c])

  iterate(base, data)

  for c in POSES:
    savePPM("../training-data/processed/%c.ppm" % (c,), data[c])
    saveC("../training-data/processed/data_%c.c" % (c,), "data_%c" % (c,), data[c])
  
def iterate(base, data):
  for i in range(1):
    for c in POSES:
      imgs = [balance(l) for l in loadAllPPM("../training-data/raw/%c.*.ppm" % (c,))]
      total_our_score = 0
      total_top_score = 0
      for img in imgs:
        img = difference(img, base)
        our_score = mean(convolve(img, data[c])) - 32768
        top_score = 0
        delta = [0 for x in data[c]]
        for d in filter(lambda x: x != c, POSES):
          this_score = mean(convolve(img, data[d])) - 32768
          top_score = max(top_score, this_score)
          if this_score > 0:
            deltas = [(x - 32768) * 0.05 * this_score / our_score for x in difference(img, data[d])]
            data[d] = map(lambda (b, d): min(max(b - d, 0), 65535), zip(data[d], deltas))
            delta = map(lambda (b, d): b + d, zip(deltas, delta))
        total_our_score += our_score
        total_top_score += top_score
        data[c] = map(lambda (b, d): min(max(b + d, 0), 65535), zip(data[c], delta))
        average = mean(data[c]) 
        data[c] = [d - (average - 32768) for d in data[c]]
        data[c] = normalize(data[c])
      print c, (total_our_score / total_top_score)

#main()

for c in ['_', 'a', 'e', 'i', 'o', 'u']:
  img = loadPPM("../training-data/drawn/%c.ppm" % (c,))
  img = [x * 256 for x in img]
  saveC("../training-data/processed/data_%c.c" % (c,), "data_%c" % (c,), img)

