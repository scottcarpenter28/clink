# Clink Finance
A personal finance tracker.

# About This Project
This application has been developed with the use of Claude Code. I have been working on this project as a way to understand how to work with an AI agent, and get it to accurately create an application.
Although not tracked, I have been creating a prompt, then I setup an agent as a project planner to generate a "Project Enhancement Proposal" document with phases. From there, I setup my next agent using a
developer prompt, a set of code standards to follow, then the proposal that the project planner created.

## Development
This has probably been the hardest part to figure out. As I the review the proposal, I will determine which phases I want the model to work on. Usually I keep it to one or two small phases. It seems that
the agents work best when focusing on smaller tasks. As they work on the proposal, I have the agents update the proposals with what they have done, as well as mark of the tasks that they have completed. This has been very useful, since
I can later pass it to the future models if needed.

I have run into issues where I would have a model work on a phase, give OK code, code that doesn't work, or a missunderstanding. In these cases, I have the current thread update the proposal with what it is done,
then I start a new thread with the same setup as before, but describe what needs to be changed, and how I would do it. Using images as well has helped get the model to do what I want.

## Keeping Clean Code
By default, agents tend to create long winded functions full of comments and replication. I have created a prompt that I provide my developer agent with how to keep the code clean. It does ok, but as I accept changes, I do take note of things
that are getting long, or has repetition. Once I've identified these issues, I will have the agent refactor the code into something that is more maintainable.
