#import numpy as np
#import matplotlib.pyplot as plt
#import numpy.linalg as npl
import copy
from recordtype import recordtype
import sys
import time

import structure_de_donnees4 as data_struct
import batching as ba
import test_gantt as gantt

time_max = 60 # 10min

Data = recordtype('Data', ['jobShop', 'currentBatches','bestObjective','bestJobShop', 'bestTime'])

successors_table = []

#Each machine register which batches it can execute + initialisations of the batches
def BatchAttribution(job_shop):
    for b in job_shop.tabBatches:
        b.machine = -1
        b.endingDate = -1
        b.processingDuration = -1
        b.startingDate = 0
        for m in job_shop.tabFamilies[b.family].dicProcessingDurations:
            if job_shop.tabMachines[m].capacity >= b.nmbOperations:
                job_shop.tabMachines[m].listFirstBatches.append(b.num)
                
#Check if the batch is a current batch
def IsItACurrentBatch(job_shop, batch):
    it_is = True
    for op in batch.tabOperations:
        it_is = job_shop.tabJobs[op.job].actualOperation == op.num
        if not it_is:
            break
    return it_is

#Initialise the tab current_batches and the release dates 
def CurrentBatchesInitialization(job_shop):
    current_batches = []
    for j in job_shop.tabJobs:
        b = j.tabOperations[0].batch
        job_shop.tabBatches[b].startingDate = max(job_shop.tabBatches[b].startingDate, j.releaseDate) #initialisation of the releaseDates
        if b not in current_batches and IsItACurrentBatch(job_shop, job_shop.tabBatches[b]):
            current_batches.append(b)
    return current_batches

#Find the best batch in a list_of_batch by heuristic method
def Heuristic(job_shop, list_of_batches, rule):
    
    if job_shop.objective == "Makespan":
        adjusted = 0
    else:
        adjusted = 1
    
    if rule == "FIFO":
        num_batch = list_of_batches[0]
        
    elif rule=="LPT":
        max_processing_time = 0
        num_batch = list_of_batches[0]
        for b in list_of_batches:
            batch = job_shop.tabBatches[b]
            if adjusted:
                weight=0
                for o in batch.tabOperations:
                    j=job_shop.tabJobs[o.job]
                    weight += j.weight
                d = job_shop.tabFamilies[batch.family].dicProcessingDurations
                processing_time = d[min(d, key=d.get)]*weight
            else:
                d = job_shop.tabFamilies[batch.family].dicProcessingDurations
                processing_time = d[min(d, key=d.get)]
            if processing_time > max_processing_time:
                max_processing_time = processing_time
                num_batch = b
                
    elif rule=="FirstToStart":
        min_starting_date = 1000000000
        num_batch = list_of_batches[0]
        for b in list_of_batches:
            batch = job_shop.tabBatches[b]
            starting_date = batch.startingDate
            if starting_date < min_starting_date:
                min_starting_date = starting_date
                num_batch = b
                
    elif rule=="FirstToFinish":
        min_ending_date = 1000000000
        num_batch = list_of_batches[0]
        for b in list_of_batches:
            batch = job_shop.tabBatches[b]
            starting_date = batch.startingDate
            d = job_shop.tabFamilies[batch.family].dicProcessingDurations
            processing_time = d[min(d, key=d.get)]
            if adjusted:
                weight = 0
                for o in batch.tabOperations:
                    j=job_shop.tabJobs[o.job]
                    weight += j.weight
                ending_date = (starting_date + processing_time)/weight
            else:
                ending_date = starting_date + processing_time
            if ending_date < min_ending_date:
                min_ending_date = ending_date
                num_batch = b
                
    elif rule=="nbSuccessors":
        max_nb_successors = 0
        num_batch = list_of_batches[0]
        if successors_table==[]: #first time we search a batch: we complete successors_table
            followers_table = []
            for i in range(job_shop.nmbBatches):
                followers_table.append([])
            for j in job_shop.tabJobs:
                for current_op in j.tabOperations[1:]:
                    for precedant_op in j.tabOperations[0:current_op.num]:
                        if current_op.batch not in followers_table[precedant_op.batch]:
                            followers_table[precedant_op.batch].append(current_op.batch)
            for b in range(job_shop.nmbBatches):
                successors_table.append(len(followers_table[b]))
        for b in list_of_batches:
            nb_successors = successors_table[b]
            if nb_successors > max_nb_successors:
                max_nb_successors = nb_successors
                num_batch = b
                
    elif rule=="WeightSum":
        max_weight = 0
        num_batch = list_of_batches[0]
        for b in list_of_batches:
            batch = job_shop.tabBatches[b]
            weight = 0
            for o in batch.tabOperations:
                j=job_shop.tabJobs[o.job]
                weight += j.weight
            if weight > max_weight:
                max_weight = weight
                num_batch = b
                
    elif rule=="DueDateMean":
        min_mean_due_date = 1000000000
        num_batch = list_of_batches[0]
        for b in list_of_batches:
            batch = job_shop.tabBatches[b]
            mean_due_date = 0
            nmb_due_date = 0
            for o in batch.tabOperations:
                j=job_shop.tabJobs[o.job]
                if j.dueDate>0:
                    nmb_due_date += j.weight
                    mean_due_date += j.dueDate*j.weight  
            if nmb_due_date != 0:
                mean_due_date = mean_due_date/nmb_due_date
                if mean_due_date/nmb_due_date < min_mean_due_date:
                    min_mean_due_date = mean_due_date
                    num_batch = b
        
    elif rule=="EDD":
        min_due_date = 1000000000
        num_batch = list_of_batches[0]
        for b in list_of_batches:
            batch = job_shop.tabBatches[b]
            min_batch_due_date = 1000000001
            for o in batch.tabOperations:
                j=job_shop.tabJobs[o.job]
                if j.dueDate>0:
                    min_batch_due_date = j.dueDate*(j.dueDate < min_batch_due_date)
            if min_batch_due_date < min_due_date:
                min_due_date = min_batch_due_date
                num_batch = b
        
    elif rule=="CostOverTime":
        max_cost = 0
        num_batch = list_of_batches[0]
        for b in list_of_batches:
            batch = job_shop.tabBatches[b]
            starting_date = batch.startingDate
            cost = 0
            for o in batch.tabOperations:
                j=job_shop.tabJobs[o.job]
                if j.dueDate>0:
                    cost += j.weight*max(0,starting_date - j.dueDate)
            if cost > max_cost:
                max_cost = cost
                num_batch = b
        
    elif rule=="Mix":
        min_due_date = 1000000000
        max_cost = 0
        num_batch = list_of_batches[0]
        over = False
        for b in list_of_batches:
            batch = job_shop.tabBatches[b]
            starting_date = batch.startingDate
            if not over:
                min_batch_due_date = 1000000000
                for o in batch.tabOperations:
                    j=job_shop.tabJobs[o.job]
                    if j.dueDate>0:
                        over = (starting_date - j.dueDate)>0
                        if over:
                            break;
                        else:
                            min_batch_due_date = j.dueDate*(j.dueDate < min_batch_due_date)
                if min_batch_due_date < min_due_date and not over:
                    min_due_date = min_batch_due_date
                    num_batch = b
            if over:
                cost = 0
                for o in batch.tabOperations:
                    j=job_shop.tabJobs[o.job]
                    if j.dueDate>0:
                        cost += j.weight*max(0,starting_date - j.dueDate)
                if cost > max_cost:
                    max_cost = cost
                    num_batch = b
        
    else:
        print("Regle bidon :",rule)
        sys.exit()
    
    return num_batch
        

#Find a cool current batch and its machine Return the num_batch and num_machine (this last is -1 if there is not)
def FindABatch(job_shop, current_batches, rule):
    num_batch = -1
    num_machine = -1
    potential_batch = copy.deepcopy(current_batches)
    #if m = -1 the batch have no family to be executed
    while num_machine == -1 and potential_batch != []:
        #find the best batch
        num_batch = Heuristic(job_shop, potential_batch, rule)
        potential_batch.remove(num_batch)
        batch = copy.deepcopy(job_shop.tabBatches[num_batch])
        #find the best machine for this batch
        batch.endingDate = 1000000000
        start = batch.startingDate
        for m in job_shop.tabFamilies[batch.family].dicProcessingDurations:
            machine = job_shop.tabMachines[m]
            if num_batch in machine.listFirstBatches:
                batch_processing_duration = job_shop.tabFamilies[batch.family].dicProcessingDurations[m]
                machine_start = 0
                if machine.nmbBatches != 0: #not the first batch on the machine
                    machine_start = machine.tabBatches[-1].endingDate + job_shop.tabSetup[machine.tabBatches[-1].family,batch.family] #we start after the last batch execution
                batch_start = max(machine_start,start)
                batch_ending = batch_start + batch_processing_duration
                if batch.endingDate > batch_ending:
                    num_machine = m
                    batch.startingDate = batch_start 
                    batch.processingDuration = batch_processing_duration 
                    batch.endingDate = batch_ending
                    batch.machine = num_machine
    return batch, num_machine

#calculate the objective
def ObjectiveCalculator(job_shop):
    obj = 0
    if job_shop.objective == "Makespan":
        for j in job_shop.tabJobs:
            obj = max(obj,j.endingDate)
    elif job_shop.objective == "TWC":
        for j in job_shop.tabJobs:
            obj += j.weight*j.endingDate
    elif job_shop.objective == "TWT":
        for j in job_shop.tabJobs:
            obj += (j.dueDate != 0)* j.weight * max(0,j.endingDate-j.dueDate) 
    else:
        print("Objectif bidon :",job_shop.objective)
        sys.exit()
    return obj

#Bound of the branch&bound
#Respecte le batching et les contraintes de precedences et les release date
#Ignore les autres batches (plusieurs batches sur la meme machine) 
def ObjectiveEstimator(job_shop, current_batches):
    relaxed_current_batches = copy.deepcopy(current_batches)
    relaxed_job_shop = copy.deepcopy(job_shop) #this batch is executed
    while relaxed_current_batches != []:
        batch = relaxed_job_shop.tabBatches[relaxed_current_batches[0]]
        relaxed_current_batches.remove(relaxed_current_batches[0])
        #we choose the best processing duration
        best_ending = 1000000000
        start = batch.startingDate #the minimal start of the batch
        for m in relaxed_job_shop.tabFamilies[batch.family].dicProcessingDurations:
            machine = relaxed_job_shop.tabMachines[m]
            #we find the machine starting date
            machine_start = 0
            if machine.nmbBatches != 0: #not the first batch on the machine
                #we start after the last batch execution
                machine_start = machine.tabBatches[-1].endingDate 
            batch_start = max(machine_start,start) #the real starting date of the batch
            best_ending = min(batch_start + relaxed_job_shop.tabFamilies[batch.family].dicProcessingDurations[m], best_ending)
        batch.endingDate = best_ending
        #update of current_batches, of the jobs and of the startingDate of the next batches
        for op in batch.tabOperations:
            j = relaxed_job_shop.tabJobs[op.job]
            j.actualOperation += 1  #job actualisation
            if j.actualOperation< j.nmbOperations: #still operations to do
                num_new_batch = j.tabOperations[j.actualOperation].batch
                next_batch = relaxed_job_shop.tabBatches[num_new_batch]
                next_batch.startingDate = max(next_batch.startingDate, batch.endingDate) #propagation of the ending date 
                if IsItACurrentBatch(relaxed_job_shop, next_batch): #update of current_batches
                    relaxed_current_batches.append(num_new_batch)
            else: #end of the job
                j.endingDate = batch.endingDate #actualisation of the job
    return ObjectiveCalculator(relaxed_job_shop)

#We try to do this batch 
def LetsDoThisBatch(data, num_machine, batch, start_time, rule):
    job_shop = data.jobShop
    machine = job_shop.tabMachines[num_machine]
    job_shop.tabBatches[batch.num] = batch
    current_batches = data.currentBatches
    current_batches.remove(batch.num) #this batch is executed
    #update of current_batches, of the jobs and of the startingDate of the next batches
    for op in batch.tabOperations:
        j = job_shop.tabJobs[op.job]
        j.actualOperation += 1 #job actualisation
        if j.actualOperation< j.nmbOperations: #still operations to do
            num_new_batch = j.tabOperations[j.actualOperation].batch
            next_batch = job_shop.tabBatches[num_new_batch]
            next_batch.startingDate = max(next_batch.startingDate, batch.endingDate) #propagation of the ending date 
            if IsItACurrentBatch(job_shop, next_batch):
                current_batches.append(num_new_batch)
        else: #end of the job
            j.endingDate = batch.endingDate #actualisation of the job
    #update of the machine
    machine.nmbBatches += 1
    machine.tabBatches.append(batch)
    for b in machine.listSecondBatches: #Return to first batches
        machine.listFirstBatches.append(b)
    machine.listSecondBatches = []
    if ObjectiveEstimator(job_shop, current_batches) < data.bestObjective: #this way is potentialy better
        best_objective, best_job_shop, best_time = BAB(data, start_time, rule)
    else:
        best_objective = data.bestObjective
        best_job_shop = data.bestJobShop
        best_time = data.bestTime
    return best_objective, best_job_shop, best_time

#We will do this batch later !
def LetsDoItLater(data, num_machine, num_batch, start_time, rule):
    machine = data.jobShop.tabMachines[num_machine]
    #report of the batch
    machine.listFirstBatches.remove(num_batch)
    machine.listSecondBatches.append(num_batch)
    #Iterate 
    best_objective, best_job_shop, best_time = BAB(data, start_time, rule)
    return best_objective, best_job_shop, best_time

#The Branch and Bound
def BAB(data, start_time, rule):
    if data.currentBatches == []: #the end of a way
        objective = ObjectiveCalculator(data.jobShop)
        if objective<data.bestObjective:
            data.bestObjective = objective
            data.bestJobShop = copy.deepcopy(data.jobShop)
            data.bestTime = copy.deepcopy(time.time()-start_time)
    else:
        batch, m = FindABatch(data.jobShop, data.currentBatches, rule)
        if m != -1 and time.time() <= start_time + time_max: #there is a batch in current batch that could be executed and the time is not over
            saved_data = copy.deepcopy(data) #save of data for an utilisation in the second way
            #first way (execution of the batch)
            saved_data.bestObjective, saved_data.bestJobShop, saved_data.bestTime = LetsDoThisBatch(data, m, batch, start_time, rule)
            data = copy.deepcopy(saved_data)
            #second way (report of the batch)  
            if time.time() <= start_time + time_max:
                data.bestObjective, data.bestJobShop, data.bestTime = LetsDoItLater(data, m, batch.num, start_time, rule)
    #if no machine is found nothing happen
    return data.bestObjective, data.bestJobShop, data.bestTime
   
#Use all the fonctions to execute the branch and bound algorithm
def Script(job_shop, rule_bab="FIFO", rule_batch = "firstToStart"):
    start_time = time.time()
    best_job_shop = copy.deepcopy(job_shop) 
    ba.batching(best_job_shop, rule_batch)
    best_objective = ObjectiveCalculator(best_job_shop) 
    job_shop.tabBatches = copy.deepcopy(best_job_shop.tabBatches)
    job_shop.nmbBatches = best_job_shop.nmbBatches
    for j in job_shop.tabJobs:
        j.tabOperations = copy.deepcopy(best_job_shop.tabJobs[j.num].tabOperations)
    BatchAttribution(job_shop)
    current_batches = CurrentBatchesInitialization(job_shop)
    data = Data(job_shop,current_batches,best_objective,best_job_shop, 0)
#    start_time = time.time()
    print("Branch and Bound starts")
    best_objective, best_job_shop, best_time = BAB(data, start_time, rule_bab)  
    return best_objective, best_job_shop, best_time, min(time_max,time.time()-start_time)
    
#dataset = open("MediumInstance.txt",'r')
#print("MediumInstance")
#dataset = open("IndustryInstance1.txt",'r')
#print("IndustrytInstance1")
#dataset = open("IndustryInstance2.txt",'r')
#print("IndustrytInstance2")
#dataset = open("knoppRandom2.txt",'r')
#print("knoppRandom2")
#dataset = open("newRandom.txt",'r')
#print("newRandom")
    
#dataset = open("ShortInstance.txt",'r')
#dataset = open("CuriousInstance.txt",'r')
dataset = open("MediumInstance.txt",'r')

job_shop = data_struct.DataGenerator(dataset)

#job_shop.objective = "Makespan"
#job_shop.objective = "TWC"
#job_shop.objective = "TWT"

# "FIFO", "LPT", "FirstToStart", "FirstToFinish", "nbSuccessors"
# "WeightSum", "DueDateMean", "EDD", "CostOverTime", "Mix"
rule = "FIFO"
#rule = "FirstToStart"
#rule = "FirstToFinish"
#rule = "Mix"
rule2 = "firstToStart"
#rule2 = "firstToFinish"

best_objective, best_job_shop, best_time, total_time =  Script(job_shop, rule) 
#print("Objectif :", job_shop.objective, "with", rule)
#print("Objectif atteint :",best_objective, "in", best_time,"seconds - Total time :", total_time)

gantt.ganttDiagram(best_job_shop)
print(best_objective, "in", total_time)
