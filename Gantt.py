
import matplotlib.pyplot as plt
import numpy as np
#import random

from collections import OrderedDict
    
#Find the end of the jobshop
def findEndingDate(jobshop) : 
    maxi =0 
    for job in jobshop.tabJobs : 
        end = job.endingDate
        if end > maxi : 
            maxi = end
    return maxi

def ganttDiagram(job_shop, rule= None, dataset=None, color_jobs = None) : 
    weigth = findEndingDate(job_shop)
    bjs =job_shop
    ylabels = []
    NbMachines = bjs.nmbMachines
    
    #Define colors
    if color_jobs == None : 
        color_jobs = [0] * bjs.nmbJobs
        for i in range(bjs.nmbJobs) : 
            color_jobs[i] = [1/bjs.nmbJobs *i,1/bjs.nmbJobs *i,1/bjs.nmbJobs *i]
            #Can change to random colors
            #color_jobs[i] = [random.uniform(0,1),random.uniform(0,1),random.uniform(0,1)]
    #define the largest capacity of the machines in this job shop
    KMax = 0 
    for i in range(NbMachines):
        ylabels.append('Machine '+str(i))
        capacity = bjs.tabMachines[i].capacity
        if KMax<capacity : 
            KMax = capacity 
     
    # Initialise plot
    fig = plt.figure(figsize=(5,5))
    if dataset != None : 
        if rule ==None: 
            plt.title("Gantt Diagramm from the data set "+ dataset)
        else : 
            plt.title("Gantt Diagramm from the data set "+ dataset+ " with the "+rule+" rule.")
    ax = fig.add_subplot(111)
    
    # Plot the data
    i =0
    height_hbar = 0.2
    for machine in bjs.tabMachines : 
        K = machine.capacity
        c=-K/4 +K/(2*(K+1))

        firstBatch=True
        for batch in machine.tabBatches : 
            setup = 0
            if firstBatch : #1st batch of a machine
                lastFam = batch.family
                firstBatch=False
                        
            else : 
                currentFam = batch.family 
                setup = job_shop.tabSetup[lastFam, currentFam]
                lastFam = currentFam 
            #display setup
            if setup > 0 :                                                                   
                ax.barh(i, setup, left=batch.startingDate-setup, height=K/2, align='center', color='green', alpha = 1)    
            #Add a bar when the machine is occupied. The broader is the bar, the larger is the capacity of the machine
            ax.barh(i, batch.processingDuration, left=batch.startingDate, height=K/2, align='center', color=[0.2,0.2,0.5], alpha = 1, edgecolor = [0,0,0])
            
            k =-1
            #add a bar wich represents the operation executing
            for op in batch.tabOperations : 
                k+=1
                ax.barh(c+i+k *K/(2*(K+1)) , batch.processingDuration, left=batch.startingDate, height=height_hbar, align='center', color=color_jobs[op.job], alpha = 1, label = "job "+str(op.job))
        i+=KMax/2+0.1

    # Format the y-axis
    locsy, labelsy = plt.yticks(np.arange(0, NbMachines*(KMax/2+0.1)+1, step=KMax/2+0.1),ylabels)
    plt.setp(labelsy, fontsize = 14)
     
    # Format the x-axis
    ax.axis('tight')
    ax.grid(color = 'g', linestyle = ':')
    plt.xticks(np.arange(0, weigth+1, step=weigth/5))
     
    # Format the legend
    if bjs.nmbJobs < 10 : 
        handles, labels = ax.get_legend_handles_labels()
        by_label = OrderedDict(zip(labels, handles))
        
        # Shrink current axis by 20%
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

        # Put a legend to the right of the current axis
        ax.legend(by_label.values(), by_label.keys(),loc='center left', bbox_to_anchor=(1, 0.5))
     
    # Finish up
    ax.invert_yaxis()
    #plt.savefig('gantt.svg')
    plt.show()