# -*- coding: utf-8 -*-
"""
Created on Sun Mar 17 17:43:32 2019

@author: Sandrine
"""

import structure_de_donnees4 as data
import numpy as np
import random

#return the operations that are available (all the predecessors are finished)
def find_operations(job_shop) : 
    available_operations = []
    for j in range(job_shop.nmbJobs) : 
        operation_found = False
        k=-1
        while not operation_found and k+1<job_shop.tabJobs[j].nmbOperations :
            k+=1 
            operation_found = job_shop.tabJobs[j].tabOperations[k].batch == -1
            
        if operation_found : 
            available_operations.append(job_shop.tabJobs[j].tabOperations[k])
    return available_operations
    
#return True if we can add an operation to the last batch of a machine
def machine_available_for_batch(machine, job_shop) : 
    lastBatch= job_shop.tabMachines[machine].tabBatches[-1]
    return lastBatch.nmbOperations < job_shop.tabMachines[machine].capacity 

#return True if the predecessors are finished before the start
def precedence_ok (job_shop, job, op, start):
    numero = op.num
    if numero == 0 :
        return True
    else :
        batch_predecessor = job_shop.tabJobs[job].tabOperations[numero-1].batch
        end_predecessor = job_shop.tabBatches[batch_predecessor].endingDate  
    return end_predecessor <= start

#return the indices of the machines sorted by their load.
def order_machines(job_shop) : 
    endingDates = []
    for m in job_shop.tabMachines :
        if len(m.tabBatches)> 0 :
            endingDates.append(m.tabBatches[-1].endingDate)
        else :
            endingDates.append(0)
    endingDates =np.asarray(endingDates)
    indices = np.argsort(endingDates)
    return indices

#return the best operation folowing a heuristic
def heuristic(job_shop, list_op,machine, rule ):
    #find the operation that can start the earlier
    if rule == "firstToStart" :
        startMin = 1000000 
        for op in list_op : 
            start = find_startingDate(op.job, op.num, job_shop, machine)
            if start < startMin : 
                startMin = start
                bestOp = op
        score = startMin
        
    #find the operation that can finish the earlier
    elif rule == "firstToFinish" :
        endMin = 10000000
        for op in list_op : 
            start = find_startingDate(op.job, op.num, job_shop, machine)
            duration = job_shop.tabFamilies[op.family].dicProcessingDurations[machine]
            end = start+duration
            if end < endMin : 
                endMin = end
                bestOp=op        
        score = endMin
        
    #Find the operation which has the largest number of successors
    elif rule == "nbSuccessors" :
        maxSuccessor = 0
        for op in list_op : 
            job = op.job 
            nbOperations = job_shop.tabJobs[job].nmbOperations
            nbSuccessors = nbOperations-op.num-1
            
            if nbSuccessors > maxSuccessor : 
                maxSuccessor = nbSuccessors
                bestOp = op
        if maxSuccessor == 0 : 
            bestOp = list_op[0]
        score = maxSuccessor    
        
    #Compute the maximum of the processingTime of all the successors. 
    #Find the operation with the biggest sum oh these proccessing times
    elif rule == "sumSuccessorTime":
        maxTime = 0
        for op in list_op : 
            job = op.job 
            nbOperations = job_shop.tabJobs[job].nmbOperations
            SumSuccessorTime=0
            for k in range(op.num,nbOperations):
                family = job_shop.tabJobs[job].tabOperations[k].family
                maxProcessingTime = 0
                #Find the worst processing time of an operation
                for m in job_shop.tabFamilies[family].dicProcessingDurations : 
                    processingTime = job_shop.tabFamilies[family].dicProcessingDurations[m] 
                    if processingTime>maxProcessingTime : 
                        maxProcessingTime = processingTime 
                         
                SumSuccessorTime+= maxProcessingTime
            
            if SumSuccessorTime > maxTime : 
                maxTime =SumSuccessorTime
                bestOp = op
        if SumSuccessorTime == 0 : 
            bestOp = list_op[0]
        score =   SumSuccessorTime 
        
    #Compute the time between the due date and the optimistic end of the job.
    elif rule == "minSlack" :
        minSlack = 1000000
        for op in list_op : 
            job = op.job     
            SumSuccessorTime=0
            nbOperations = job_shop.tabJobs[job].nmbOperations
            for k in range(op.num,nbOperations):
                family = job_shop.tabJobs[job].tabOperations[k].family
                maxProcessingTime = 0
                for m in job_shop.tabFamilies[family].dicProcessingDurations : 
                    processingTime = job_shop.tabFamilies[family].dicProcessingDurations[m] 
                    if processingTime>maxProcessingTime : 
                        maxProcessingTime = processingTime 
                SumSuccessorTime+= maxProcessingTime 
            start = find_startingDate(op.job, op.num, job_shop, machine)
            endJob = start+SumSuccessorTime
            dueDate = job_shop.tabJobs[job].dueDate
            slack =  (dueDate - endJob)
            if dueDate !=0 and slack <= minSlack :
                minSlack = slack 
                bestOp = op
        if minSlack ==  1000000 : 
            bestOp = list_op[0]
        score = minSlack
        
    #Find the operation with the shortest due date
    elif rule == "J_EDD" :
        minDueDate = 1000000
        for op in list_op : 
            job = op.job 
            dueDate = job_shop.tabJobs[job].dueDate/job_shop.tabJobs[job].weight
            if dueDate <= minDueDate and dueDate != 0: 
                minDueDate = dueDate 
                bestOp = op
        if minDueDate == 1000000 : 
            bestOp = list_op[0] 
        score = minDueDate  
        
    #select a random operation
    elif rule == "random" : 
        choosenOp = random.randint(0, len(list_op)-1)
        bestOp = list_op[choosenOp] 
        score =job_shop.tabFamilies[bestOp.family].dicProcessingDurations[machine] 
    return bestOp, score

#Find the earliest time when an operation can start on a machine
def find_startingDate(job, op, job_shop, machine) :
    jobready = job_shop.tabJobs[job].releaseDate 
    currentFamily =job_shop.tabJobs[job].tabOperations[op].family 
    if len(job_shop.tabJobs[job].tabOperations) >1 and op >0: 
        batch_predecessor = job_shop.tabJobs[job].tabOperations[op-1].batch                                                                  
        endPredecessor = job_shop.tabBatches[batch_predecessor].endingDate
    else : 
        endPredecessor = 0
    if len(job_shop.tabMachines[machine].tabBatches) >0 :
        endMachine =job_shop.tabMachines[machine].tabBatches[-1].endingDate
        lastFamily =job_shop.tabMachines[machine].tabBatches[-1].family
        setupTime = job_shop.tabSetup[lastFamily,currentFamily]
    else : 
        endMachine = 0
        lastFamily = currentFamily
        setupTime = 0
    start = max(endPredecessor, endMachine,  jobready)

    if start < (endMachine + setupTime) : 
        start+= setupTime
    return start

def batching(job_shop, rule= "firstToStart", batchVersion=1) : 
 
    available_operations = find_operations(job_shop)
    
    while len(available_operations) >0 :
        found = True
        #Try to fill existing batches as much as possible
        while found : 
            job_shop, found = addOperationToBatch(job_shop, available_operations)
            available_operations = find_operations(job_shop)
            
        #Creation of a new batch (two versions of the algorithm)
        if len(available_operations)> 0 : 
            if batchVersion == 1 : 
                newBatch(job_shop, available_operations, rule)
            else : 
                newBatch2(job_shop, available_operations, rule)
            available_operations = find_operations(job_shop)                                                  
    
    job_shop.nmbBatches = len(job_shop.tabBatches)

#Add an operation to existing batches and check the precedence contraints
def addOperationToBatch(job_shop, available_operations) :
    m=0
    found = False
    sameFam = False
    while m < job_shop.nmbMachines and not found : 
        if len(job_shop.tabMachines[m].tabBatches)>0 :
            if machine_available_for_batch(m, job_shop) : 
                k=0
                while k < len(available_operations) and not found: 
                    currentOperation = available_operations[k]
                    sameFam =currentOperation.family == job_shop.tabMachines[m].tabBatches[-1].family 
                    job = available_operations[k].job
                    op =available_operations[k].num 
                    start = job_shop.tabMachines[m].tabBatches[-1].startingDate
                    job_ready = job_shop.tabJobs[job].releaseDate <= start
                    
                    if sameFam and precedence_ok(job_shop, job,currentOperation, start) and job_ready  :
                        #add the operation found in the batch structure
                        found = True
                        currentbatch = job_shop.tabMachines[m].tabBatches[-1]
                        currentOperation.batch = currentbatch.num
                        numBatch = currentbatch.num
                        famBatch =  currentbatch.family
                        nbOpBatch = currentbatch.nmbOperations
                        listOp =  currentbatch.tabOperations
                        listOp.append(currentOperation)
                        machineBatch = currentbatch.machine
                        processDuration = currentbatch.processingDuration
                        start = currentbatch.startingDate
                        end =  currentbatch.endingDate
                        del job_shop.tabBatches[-1]
                        del job_shop.tabMachines[m].tabBatches[-1]
                   
                        job_shop.tabBatches.append(data.Batch(numBatch,famBatch, nbOpBatch+1, listOp, machineBatch, processDuration,start,end)) 
                        job_shop.tabMachines[machineBatch].tabBatches.append(data.Batch(numBatch,famBatch, nbOpBatch+1, listOp, machineBatch, processDuration,start,end)) 
                        
                        if job_shop.tabJobs[job].nmbOperations == op+1 :
                            job_shop.tabJobs[job].endingDate = end
                    k+=1
        m+=1
    return job_shop, found

#Select a couple machine-operation that will composed the new batch (1st version) and create it
def newBatch(job_shop, available_operations, rule) : 
    #Looking for the less loaded machines
    machines = order_machines(job_shop)
    m=0
    found = False
    while not found and m < job_shop.nmbMachines: 
        machine = machines[m]
        list_op = availableOpOnMachine( job_shop,machine,available_operations)
        if len(list_op)>0 : 
            found = True
            op, score = heuristic(job_shop, list_op,machine, rule )
        m+=1
    createBatch(job_shop, op, machine)

#Add the new batch to the structure
def createBatch(job_shop, op, machine) :
    b = len(job_shop.tabBatches)
    num_op = op.num
    job_op = op.job
    job_shop.tabJobs[job_op].tabOperations[num_op].batch = b 
    currentFamily = op.family
    startingDate = find_startingDate(job_op, num_op, job_shop, machine)
    processingDuration = job_shop.tabFamilies[currentFamily].dicProcessingDurations[machine]
    endingDate = startingDate + processingDuration
    list_op = []
    operation = data.Operation(num_op, job_op, currentFamily, b)
    list_op.append(operation)
    job_shop.tabBatches.append(data.Batch(b,currentFamily, 1, list_op, machine, processingDuration,startingDate,endingDate)) 
    job_shop.tabMachines[machine].tabBatches.append(data.Batch(b,currentFamily, 1, list_op, machine, processingDuration,startingDate,endingDate)) 
    if job_shop.tabJobs[job_op].nmbOperations == num_op +1:
        job_shop.tabJobs[job_op].endingDate = endingDate

#return the list of the operations that can be proceeded on a given machine
def availableOpOnMachine( job_shop,machine,available_operations) : 
    list_op =[]
    for op in available_operations :
        family = op.family 

        for m in job_shop.tabFamilies[family].dicProcessingDurations :  
            if m == machine :
                list_op.append(op)
    return list_op

#return the machine that can start an operation the earlier
def findBestMachine(job_shop, bestOp) : 
    family = bestOp.family 
    job = bestOp.job
    bestStartingDate = 10000000
    for m in job_shop.tabFamilies[family].dicProcessingDurations :  
        start = find_startingDate(job, bestOp.num, job_shop, m) 
        if bestStartingDate > start:
            bestStartingDate = start
            bestMachine = m
    return bestMachine

#return the next operation we select depending on the heuristic rule
def findNextOperation(job_shop, available_operations, rule) : 
    scoreMin = 1000000000
    scoreMax = 0 
    bestMachine = 0
    bestOp = available_operations[0]
    for machine in range(0,job_shop.nmbMachines) : 
        list_op = availableOpOnMachine( job_shop,machine,available_operations)
        if len(list_op) > 0 : 
            op, score = heuristic(job_shop, list_op, machine, rule)

            if rule == "firstToStart" or rule =="firstToFinish" :
                if score <= scoreMin : 
                    scoreMin = score
                    bestOp = op
                    bestMachine = machine
                    
            if rule =="J_EDD" or rule =="minSlack" or rule =="random" : 
                 if score <= scoreMin : 
                    scoreMin = score
                    bestOp = op
                    bestMachine = findBestMachine(job_shop, bestOp)
                     
            
            elif  rule == "nbSuccessors" or rule== "sumSuccessorTime":
                
                if score >= scoreMax : 
                    scoreMax = score
                    bestOp = op
                    bestMachine =findBestMachine(job_shop, bestOp)
                
    return bestOp, bestMachine 


#Select a couple machine-operation that will composed the new batch (2nd version) 
#and create it
def newBatch2(job_shop, available_operations, rule) : 
    #Select the best operation following an heuristic
    op, machine= findNextOperation(job_shop, available_operations, rule) 
    #create a ew batch with the couple operation-machine 
    createBatch(job_shop, op, machine)
        
#compute the objective score of a job-shop
def findScore(job_shop) : 
    #Makespan (completion time of the whole scheduling),
    #TWC (weighted sum of the end of the jobs) 
    #TWT (weighted sum of the tardiness of the jobs).
    makespan =0 
    TWC=0
    TWT =0
    for job in job_shop.tabJobs : 
        tardiness = 0 
        end = job.endingDate
        TWC += end*job.weight
        if job.dueDate != 0 :
            tardiness = ((job.dueDate - end)<0) * (job.dueDate - end)
            TWT+= abs(tardiness) *job.weight 
        if end > makespan : 
            makespan = end
    
    return makespan, TWT, TWC
