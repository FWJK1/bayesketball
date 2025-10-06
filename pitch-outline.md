Basic information about the project: team members, planned title, and team members’ roles.
 One section outlining your learning objectives.
These will generally differ for each team member.
 One section outlining the project idea. This section should be a paragraph or two.
 One section outlining at least 3 relevant references. These references can be a paper you plan to
reproduce, information about a data set or method you want to use, or a type of models you’d like to
learn more about.
 One section outlining your planned timeline: milestones, and when do you plan to reach them.
 The pitch must be written clearly, with correct grammar, and be well-organized.
 You must turn in the pitch on time.

# Basic information

-   Title: Bayesketball: comparing hierarchical bayesian prediction of basketball win probabilities to machine learning models.
-   Team Members:
    -   Prithaj Nath
    -   Nate Borland
    -   Fitz Koch

# Learning Objectives

## Prithaj

Implement Bayesian regression or other Bayesian ML techniques on a sizeable dataset that requires more computation power than a laptop can handle. Stretch goal would be to build an interactive dashboard that lets you pick teams and set player level metrics, and then runs the model to create posteriors for those teams.

## Nate

## Fitz

By the time this project is completed, I will have learned how to work with Bayesian Hierarchical models, helping both with breaking down large predictive problems into smaller pieces and increasing familiarity with `MCMC` modelling using {INSERT TOOLKIT WE WANT TO USE, I WOLD ARGUE FOR JULIA or PYTHON}. This will invovlve substantial work developing new models and priors, as well as an integration of `MCMC` specific libraries into a data retrieval and storage framework. In addition, I will build familiarity with setting up pipelines with APIs such that we can automatically update our model as the season goes on. Broadly speaking, I expect more learning to occur on the Bayesian side of things then the data science side, just because I have already completed projects requiring at-scale data retrieval and processing, but I still expect to learn a lot from putting the two together. Also, in all previous projects I've completed of this sort I have generally been the best at coding, so I'm looking forward to learning from the more experience Prithaj and Nate and stepping up a bit more in the logistic and analytic aspects.

# Project idea

"One section outlining the project idea. This section should be a paragraph or two."

## Pitch

The idea is to hierarchically model basketball with Bayesian priors and posteriors. The goal will be to build probability distribution for any two teams facing each other, and thus predict the outcome of the league (and each team), both with historical data and with present data. These models will then be compared with machine learning models.

## Hierarchy

Proceeding 'down' to our original priors, something like this:

1. Win probability = comparison of team quality.
2. Team quality = player quality (scaled by expected playing portion)
    1. Player quality: based on stats, such as :
        - assists
        - rebounds
        - shots attempted
        - percentage shots scored
        - and so on.
    2. Expected playing time: based just on by their previous playing time (with injury = removed from team, not no playing time)

## Comparison Models

In addition to our Bayesian model, we will construct several machine learning comparison models to get a sense of total accuracy. While many ML models give raw predictions, not probability distributions, we're working on it by: { OTHERS CHIP IN}

-   Frequentist Linear Regression
-   Bayesian Linear Regression
-   Random Forest: gives raw predictions, but we can use the variation of predictions to approximate a normal pdf.

# References

 One section outlining at least 3 relevant references. These references can be a paper you plan to
reproduce, information about a data set or method you want to use, or a type of models you’d like to
learn more about.

# Timeline

 One section outlining your planned timeline: milestones, and when do you plan to reach them.

# Notes

 The pitch must be written clearly, with correct grammar, and be well-organized.
 You must turn in the pitch on time.
