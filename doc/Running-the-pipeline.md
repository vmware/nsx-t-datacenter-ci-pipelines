There are four options for running the pipelines:
1. Full deployment
- Deploying OVAs and setting up NSX components
- Setting up logical routing, overlay and transport nodes 
- Configures Extras such as NAT rules, tags, and spoofguard profiles and LB
2. OVAs and edge hosts deployment only <br>
3. Routing only (T0, T1 Routers, and Logical switches), overlay and TNs <br>
4. Extras configurations only <br> <br>

![](https://github.com/vmware/nsx-t-datacenter-ci-pipelines/blob/Wiki-files/Wiki%20images/concourse3.png?raw=true) 
<br>
The idea is that while it makes sense to run the full deployment most of the times, one might want to run only a certain portion of the pipeline in stages. <br>
For example, it takes a bit of time to deploy the NSX components (about 40 minutes) and much shorter time to deploy the logical routing and extras, one can decide to run only “deploy OVAs” portion and then run the other parts (or the full install), and the pipeline will validate that the previous steps have been completed and will pick it up from there
For all of these options, we use a single parameters file (See appendix for populating the param file. The following are the steps to run the pipeline.
<br>
In the pipeline page select the job you want to run, in this guide we will run the full install:

Click on the first grey box representing the first task <br> <br>
![](https://github.com/vmware/nsx-t-datacenter-ci-pipelines/blob/Wiki-files/Wiki%20images/concourse4.png) <br>

<br>
Click on the + sign on the top right <br> <br>

![](https://github.com/vmware/nsx-t-datacenter-ci-pipelines/blob/Wiki-files/Wiki%20images/concourse5.png) <br>

At this point the pipeline should start, you can follow its progress from this site