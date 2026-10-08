# Report

Report prepared by Alessandro Trigilio

In the following section, I explain the procedure I followed to solve task 1, followed by the answers to tasks 2 and 3.

## Task/Question 1

### Files breakdown

The source files are located in the folder `/sources`, and the generated files are in `/intermediate`. The reports are located in `/reports`.

### Data inspection

The first step after inspecting the files in the package was to understand what the data represented physically. To that end, and keeping in mind that a UI is not the goal of the exercise, I created an interactive map using the physical coordinates and facility type (port, distillery, or cracker). The map is located in the file `facilities_map.html`, and the Python script to generate it (created by an AI agent) in `/sources/map_facilities.py`.

### Data preparation

The most relevant information about the facilities and units was condensed into a single file (`main.xlsx`). Not all the information was used. Some information was deliberately left out, for example, the information in `transport_legs.csv` and `port_throughput.csv`, because it was specific to certain units and easier to treat separately.

In a broader model, the information could be contained in a database, but for this relatively small dataset and the time constraint, using a spreadsheet helps to visualize the information.

### Assumptions (some of them taken directly from the initial document)

- The capacity of each unit is 80% of what was reported
- The naphtha yield is 7.5% of the crude oil
- The naphtha required per ton of ethylene is 2.75:1
- All the capacities are given in tons per year
- Due to time constraints, the veracity of the information provided was not questioned, but it was taken as received. This must be assessed for a deployed model.
- Exported and imported were used as "in" and "out" of the port, not in the strict "international border" sense.
- For the ports, missing information for any port was treated as a lack of exports/imports
- To check: the travel distances from port to refinery are feasible (i.e., they don't imply transporting over the sea again, e.g. north of Spain to west of France, vs north of Spain to west of Spain)

### Steam cracker

Critical assumptions that impact the results:

- The reported physical links have priority over other means of transport
- During the assignment of sources, the priority was given to neighbors with pipelines
- The rest was assigned by physical proximity
- In case that the linked neighbors could not provide the needed input, then the closest port or refinery was considered
- This last point applies also to the two crackers without known physical links
- In view of breadth instead of depth and not to go over time, it was assumed a naïve approach that any source can supply its capacity to any cracker

Important negative impact of this assumption:

- From the last assumption, this approach is not realistic because there are many shared sources that cannot physically give all their capacity every time.
- The ports that can provide naphtha are underutilized due to the priority of using the physical link, and the possibility of counting the same source multiple times

How to help avoid or minimize this (not implemented):

- Give priority to the ones from the same organization and treat this as data anchors, especially if their proximity is close, even if no physical link is reported
- If more reliable data is lacking, order the steam crackers from lowest to highest number of reported connections and give priority to the lowest one when assigning the capacities; this way, they take advantage of the closer neighbors and give more freedom in the models to the ones with more possibilities.
- I made a test only tackling the first point in this list, and the situation didn't improve, so the next level is needed: check partners within the same organization with or without reported physical links.
- Once all those constraints are set, and without any extra information, it becomes an optimization problem in which the source capacities must be distributed among the crackers considering distances and physical links.

A known error due to what was discussed: the triad Porvoo [FI] <-> Porvoo Refinery <-> Porvoo Olefins is not trading, because, according to the naïve model implemented, the cracker prefers to import from a railroad line +1500km away instead of the closest neighbor, which belongs to the same organization

### Refineries

For the refineries, I matched using the information in `port_throughput.csv` directly. I used the closest ports to each facility in sequence to supply the necessary capacity, as needed. There was no information on inland crude-oil sources, so I assumed it all came from ports.

As before, there are a number of ports that are giving their capacity to more than one distillery, which should be a constraint of the model and could be minimized following the steps described for the steam cracker.

### Output

The sources breakdown predictions are located in the files `/reports/stream_crackers_report.xlsx` and `/reports/crude_distillation_report.xlsx`.

Below is an extract of the report for some of the steam crackers:

| facility_id | facility_name | unit_name | partner_id | partner_name | mode | supplied_fraction |
|---|---|---|---|---|---|---|
| 47cf22ae | Terneuzen Petrochemical | LHC 1 | 62086957 | Antwerpen Refinery | pipeline | 0.65 |
| | | | a6630b6f | Zeeland Refinery | pipeline | 0.35 |
| 47cf22ae | Terneuzen Petrochemical | LHC 2 | 62086957 | Antwerpen Refinery | pipeline | 0.65 |
| | | | a6630b6f | Zeeland Refinery | pipeline | 0.35 |
| 47cf22ae | Terneuzen Petrochemical | LHC 3 | 62086957 | Antwerpen Refinery | pipeline | 0.65 |
| | | | a6630b6f | Zeeland Refinery | pipeline | 0.35 |
| 47f7223d | Litvinov Petrochemical Complex | Ethylene | a43ffbc5 | Litvinov Refinery | pipeline | 0.38 |
| | | | fac4c032 | Slovnaft Refinery (MOL Nyrt) | pipeline | 0.39 |
| | | | fd662c46 | Kralupy nad Vltavou Refinery | pipeline | 0.24 |
| 4ff39f24 | Lavera Ethylene | Ethylene | 391abb50 | Feyzin Refinery | pipeline | 0.18 |
| | | | 39dc8740 | Fos-sur-Mer Refinery | pipeline | 0.21 |
| | | | a81a21a0 | Petroineos Lavera Refinery | pipeline | 0.33 |
| | | | 58b886ef | Iplom Refinery | extra | 0.05 |
| | | | 7ebca8e8 | Sannazzaro Refinery | extra | 0.23 |

## Task/Question 2

To ensure data safety, set up regular backups of the model's current state so you can roll back with minimal downtime and delays, with no information lost.

A specific model benchmark can be set and used for comparison. For this, I would use the model's initial state before the change and evaluate the outcome after the changes. Check which sourcing breakdown changed and by how much, which can also give an idea about the sensitivity of the outputs with respect to the changes in the model.

In this benchmark, I wouldn't include the data that the modeler introduced but instead only measure/evaluate what changed compared with the initial state. For example, if a specific fraction of the feed of one of the facilities was allocated with total certainty, it will have a ripple effect on the other shares: now a fraction of a specific source is being used or freed and that can be used or not by another facility.

Scrutinize outliers or borderline cases. For example, I obtained a result where a railway located +1500km from a facility is the source. If there is any anchor data or certainty in the results of data that we know is an irrefutable fact, and that has not been used to train or fit the model, we could use it to check.

Like this example, many can arise that go against common sense. Understanding that sometimes it is difficult to put common sense into mathematical language, an additional step can be to manually check the outputs of what changed in the model. There are statistical ways of being certain that, e.g., "at most 5% of your data has errors, with 95% confidence", which can be employed for these models (i.e., checking 50 data points from a population of 100 to 5000 data points achieves that goal).

Other regular checks that must always be performed refer to internal consistency. For example, the breakdown fractions should add to 1, and there should be no double counting of the sources (e.g., all the sources must supply at most their adjusted capacity).

In general, I would refuse to deploy any changes that go against the known data or that produce results that can't be explained with the information at hand. Also, a worst agreement with the anchors should be refused.

## Task/Question 3

The user should understand that these are estimates and may be comparable to the cost-estimation methodology for class 4 or 5 engineering project calculations. This means that general certainty is low in the early stages, where the amount of inference needed is high. It must also be understood that the reliability of the results comes from the accuracy of the underlying data (inferences vs. confirmed data), and this accuracy (or lack of it) propagates throughout the model. In other words, if 10% of the data has a significant uncertainty, it will propagate in a compounded way through all the calculations made in the model (either in a direct algorithmic way or through stochastic optimizations), ultimately affecting the global accuracy in a factor proportional to the inferences made.

A confident answer starts from a low uncertainty in the data. For example, if the parent organization is known from a triad of port/refinery/cracker, and they are physically close, there is an extremely high chance that the three of them are trading. As in the previous question, a trade link using a railroad 1500km apart is very unlikely.

These are the easy cases, and for the intermediate ones, an expert user should have an assessment and assign a certainty, based on factors like physical connections, proximity, previous trading experience, knowledge of the status of the partnership, and any other real-world data that can help make a good evaluation of the model. These factors could be measured independently and then assigned a scoring weight, resulting in a sort of linear combination of all the factors and their weights that can be assigned as a certainty link-score to each link.

If I design a model to quantify uncertainty, I would use the link-score I described in a graph model. Every facility is the center of a graph, and all the possible sources are nodes. Each link between nodes will have its link-score, based on the factors I mentioned before. If a link is too far or physically impossible, the link-score is automatically 0. If they belong to the same organization, the link-score is most likely 1. The values in between come from the combination of parameters and the weight factors. The links with 0 score are useful for removing degrees of freedom from the optimization problem.

Once the link-scores are assigned for all the links, I would use the breakdown fraction for each supplier as a weight and calculate a weighted sum of the fraction times the link-score for each link between supplier and facility, and then that could be used as an uncertainty measure.

Beware that additional checks are needed to ensure that no more than the capacity of each source is used.

We could assign levels of accuracy (low, high, medium, extremely high, extremely low) to report to the user according to the calculated uncertainty.
