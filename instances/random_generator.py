# -*- coding: utf-8 -*-
"""
Created on Tue Jan 29 13:38:41 2019

@author: Sandrine
"""
#Ce code n'est pas le mien. Il est importé du github https://github.com/sebastian-knopp/cjs-instances 

from random import randint

def generate():
    jobCount = [4,8,120 ]
    capacities = [ 2, 4, 6 ]

    for i in range(3):
        g = Generator();

        g.setNmbJobs(jobCount[i])
        g.setNmbMachines(g.nmbJobs / 6, g.nmbJobs / 6)
        g.setNmbFamilies(g.nmbJobs / 4, g.nmbJobs / 4)

        g.setBatchCapacity(capacities[i])

        g.generate("newRandom" + ("%02d" % (i+1)) + ".cjs.input")


class Job:
    def __init__(self):
        self.releaseDate = 0
        self.dueDate = 0
        self.weight = 1
        self.operations = [] # list of family indices
    def write(self, f):
        f.write(str(self.releaseDate) + " " + str(self.dueDate) + " " + str(self.weight) + " " + str(len(self.operations)))
        f.write(" " + " ".join(str(i) for i in self.operations))
        f.write("\n")

class Machine:
    def __init__(self):
        self.capacity = 1
    def write(self, f):
        f.write(str(self.capacity) + "\n")

class Recipe:
    def __init__(self):
        self.machineIndex = 0
        self.processingDuration = 1
    def __str__(self):
        return str(self.machineIndex) + " " + str(self.processingDuration)

class Family:
    def __init__(self):
        self.recipes = []
    def write(self, f):
        f.write(str(len(self.recipes)) + " " + " ".join(str(q) for q in self.recipes))
        f.write("\n")

class Instance:
    def __init__(self):
        self.jobs = []
        self.machines = []
        self.families = []
        self.setupMatrix = []
    def write(self, filename):
        fileHandle = open(filename, 'w')
        fileHandle.write(str(len(self.jobs)) + " " + str(len(self.machines)) + " " + str(len(self.families)) + "\n")
        fileHandle.write("TWT\n")
        for j in self.jobs:
            j.write(fileHandle)
        for m in self.machines:
            m.write(fileHandle)
        for f in self.families:
            f.write(fileHandle)
        for r in self.setupMatrix:
            fileHandle.write(" ".join(str(c) for c in r) + "\n")

class RandomRange:
    def __init__(self, min, max):
        self.min = min
        self.max = max
    def get(self):
        return randint(self.min, self.max)

class UniqueRandomRange:
    def __init__(self, min, max):
        self.min = min
        self.max = max
        self.usedNumbers = set()
    def remaining(self):
        return self.size() - len(self.usedNumbers)
    def size(self):
        return self.max - self.min + 1
    def reset(self):
        self.usedNumbers = set()
    def get(self):
        if self.remaining() <= 0:
            raise AttributeError("No unused numbers left in unique random range [" + str(self.min) + ", " + str(self.max) + "] (" + str(len(self.usedNumbers)) + " already used).");
        result = randint(self.min, self.max)
        if result in self.usedNumbers:
            return self.get()
        self.usedNumbers.add(result)
        return result

class Generator:
    def __init__(self):
        self.operationsPerJobRange = RandomRange(1, 7)
        self.jobWeightRange = RandomRange(1, 10)
        self.regularProcessingDurationRange = RandomRange(10, 20)
        self.setupDurationRange = RandomRange(1, 10)
        self.recipesPerBatchFamilyRange = RandomRange(1, 5)
        self.recipesPerRegularFamilyRange = RandomRange(1, 5)
        self.dueDateFactorRange = RandomRange(100, 150)
    def setNmbJobs(self, nmbJobs):
        self.nmbJobs = nmbJobs
        self.releaseDateRange = RandomRange(0, 2 * self.nmbJobs)
    def setBatchCapacity(self, capacity):
        self.batchCapacity = capacity
        self.batchProcessingDurationRange = RandomRange(10 * capacity, 20 * capacity)
    def setNmbMachines(self, nmbBatch, nmbregular):
        self.nmbBatchMachines = max(1, int(nmbBatch))
        self.nmbRegularMachines = max(1, int(nmbregular))
        self.nmbMachines = self.nmbBatchMachines + self.nmbRegularMachines
    def setNmbFamilies(self, nmbBatch, nmbregular):
        self.nmbBatchFamilies = max(1, int(nmbBatch))
        self.nmbRegularFamilies = max(1, int(nmbregular))
        self.nmbFamilies = self.nmbBatchFamilies + self.nmbRegularFamilies
    def generateFamilies(self, inst, nmbFamilies, machineIndexRange, recipesPerBatchRange, processingDurationRange):
        for i in range(nmbFamilies):
            f = Family()
            machineIndexRange.reset()
            for j in range(recipesPerBatchRange.get()):
                r = Recipe()
                r.machineIndex = machineIndexRange.get()
                r.processingDuration = processingDurationRange.get()
                f.recipes.append(r)
                if machineIndexRange.remaining() <= 0:
                    break
            inst.families.append(f)
    def generate(self, filename):
        inst = Instance()

        for i in range(self.nmbJobs):
            j = Job()
            j.weight = self.jobWeightRange.get()
            familyIndexRange = RandomRange(0, self.nmbFamilies - 1)
            sumMaxProcessingDuration = 0
            for n in range(self.operationsPerJobRange.get()):
                familyIndex = familyIndexRange.get()
                j.operations.append(familyIndex)
                if (familyIndex < self.nmbBatchMachines):
                    sumMaxProcessingDuration += self.batchProcessingDurationRange.max
                else:
                    sumMaxProcessingDuration += self.regularProcessingDurationRange.max
            j.releaseDate = self.releaseDateRange.get()
            j.dueDate = j.releaseDate + int(self.dueDateFactorRange.get() * sumMaxProcessingDuration / 100)
            inst.jobs.append(j)

        for i in range(self.nmbBatchMachines):
            m = Machine()
            m.capacity = self.batchCapacity
            inst.machines.append(m)
        for i in range(self.nmbRegularMachines):
            inst.machines.append(Machine())

        self.generateFamilies(inst,
                              self.nmbBatchFamilies,
                              UniqueRandomRange(0, self.nmbBatchMachines - 1),
                              self.recipesPerBatchFamilyRange,
                              self.batchProcessingDurationRange)
        self.generateFamilies(inst,
                              self.nmbRegularFamilies,
                              UniqueRandomRange(self.nmbBatchMachines, self.nmbMachines - 1),
                              self.recipesPerRegularFamilyRange,
                              self.regularProcessingDurationRange)

        inst.setupMatrix = [[0 for x in range(self.nmbFamilies)] for x in range(self.nmbFamilies)] 
        for x in range(self.nmbFamilies):
            for y in range(self.nmbFamilies):
                if x != y and x >= self.nmbBatchFamilies and y >= self.nmbBatchFamilies:
                    inst.setupMatrix[x][y] = self.setupDurationRange.get()

        inst.write(filename);


generate()
