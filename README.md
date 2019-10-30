# Applying a Branch and Bound algorithm and heuristics to the complex job shop scheduling problem in the semi-conductor industry.
4th year project supervised by M. Artigues and M. Lopez from LAAS, CNRS Toulouse. 

In this git repository, you will find our code for the optimization of the scheduling of the production in the semi-conductor industry. We also provide an algorithm to visualize our solution with Gantt's Diagram. For further details on our methods and results, you can refer to our article.

Abstract :

The production of semi-conductors is a complex process, which requires many steps on different machines. The scheduling optimization of this production can be modelled by the complex job shop model with batch. Job shop is one of the most common scheduling problems. Usual job shops include jobs which are carryingout multiple operations in a set of machines, with specific scheduling constraints. 
We study a semiconductormanufacturing model including batching, setup times and release dates. This case is currently one of the most complex job shops. The optimization of this model is an NP-hard problem, which cannot be solved inpolynomial time. Our objective is to develop an algorithm to find an approximate solution in a reasonabletime.  
We separate this problem in two sub-problems: batching and scheduling. We create a new algorithm based on the branch and bound model to solve the scheduling problem. We use heuristics to optimize thebatching and the scheduling. We test our algorithms, prove the efficiency of their features and find adequateheuristics. More sophisticated methods could be developed for the batching part and the implementation ofthe branch and bound can be improved. These algorithms remain a solid base to find good feasible solutionsfor industrial cases.

Ilinka Clerc & Sandrine Bouguen
