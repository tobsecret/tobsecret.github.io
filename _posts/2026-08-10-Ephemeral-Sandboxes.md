---
layout: post
title: "Ephemeral Sandboxes in the Cloud"
date: 2026-08-10 12:00:00 +0000
feature_image: /assets/blog/2026-08-10/sandbox_1920px.png
---

Every tech company faces this problem at some point: features are tested locally but shipped in the cloud, and the discrepancies are often difficult to account for. Short-lived cloud-native sandboxes are one way to address this and come with a few additional benefits.
These ephemeral sandboxes allow us developers to share a working live version of our app with other members of the company, have them interact with it and allow us to afterwards query the logs to see if everything worked as intended. This async cloud-native nature makes ephemeral sandboxes an attractive solution, even for tech stacks that can comfortably stay performant on the local dev stack.

I was inspired by [shopify’s “The Journey to Cloud Development” ](https://shopify.engineering/shopifys-cloud-development-journey) article series to build such a system for our team. I especially liked how they talked through their iteration process all the way from very early experiments to finding the solution that worked for their developers. They do a great job explaining the decisions, failures and wins along the way.

While it was a great inspiration our path to sandboxes was different. Unlike the developers at shopify, we did not typically run into the issue of having too little compute for running our local dev setup. If anything we had too much compute power and workloads that looked fine on a local machine could fail in the cloud.
At work we develop in a typical web application stack, a frontend, a backend API service, worker queues, cache and a database. 
We already had a stable sandbox with automated deploys, but our CD pipeline to said sandbox was gatekept by approval and typically done in larger releases rather than truly continuously. As a result, testing my changes in our real full stack required waiting until the sandbox branch was merged and deployed to our stable sandbox.
 
Being able to spin up such sandboxes also opens the door to letting agents test changes in full-stack environments for which we’d want that emulation of our production stack to be as close as possible.

## Implementation
So I set out to scope and build a system that would allow us to easily create an ephemeral sandbox off of work in progress. The first question was how the system should be controlled: a signal sent from a local machine (i.e. via a script), a signal sent from a PR or from some other central resource like slack?
I decided to tie it to PRs. This leaves a visible and centralized record, it ties it to an individual unit of work and it lets us easily get back to a sandbox if we need to.

I opted to go for a comment-driven workflow powered by GitHub actions because comments are easy to understand and carry the PR context with them. A /sandbox create comment would create a sandbox and similar commands exist to poll the status of a sandbox, to update one with newly pushed changes, and to destroy a sandbox when no longer needed.

Every sandbox should also be uniquely identifiable. Since we base each on a branch, we use the hash of that branch name to create a unique sandbox id. 

The next question was around how we should provision the infrastructure. The most naive, faithful and complete option would be to create a 1-1 copy of the sandbox environment, entirely on its own VPC, gateway, with its own ALB, subnets, app workers, db server, etc.
This isn’t feasible for cost reasons but also because AWS sets a per-account limit on the max number of resources per region, which is especially low for VPCs, Elastic IPs, and NAT gateways. 

So instead I opted for a solution where we reuse most of the existing infrastructure in our sandbox environment. We use our unique sandbox ID to tag all associated resources. This makes it much easier to take them down.
The only top level infrastructure resources we provision entirely newly are the app and worker queue tasks in ECS. We route them through the shared ALB, have them use the same REDIS cache instances but with their own queues.

The database required the biggest effort in all of this. I did consider seeding the database with our typical local seed script but decided against it. I wanted my colleagues to have a really familiar environment so they can easily reuse and inspect resources they have created. As a result I decided to use the existing stable sandbox db as the basis for populating ephemeral sandboxes.

Initially I tested out the naive method of copying the entire existing stable sandbox db on every ephemeral sandbox. The idea was that this would have resulted in the most up-to-date data in the fresh ephemeral sandbox db. Unsurprisingly this turned out to be prohibitively slow and would put a lot of strain on the db server. 
So instead I maintain a template db on the db server which is copied nightly from the stable sandbox db on the same server. When we provision a new ephemeral sandbox we clone from the template db and then apply migrations and security permissions. This is much faster and less strain on the db server. However, it also means that the ephemeral sandbox db lags behind the original sandbox db by the update cadence of the template db.

## Impact

Our <span class="footnote-hover">GTM lead's<span class="tooltip-text"> Go To Market Lead - in charge of launching products to potential buyers</span> </span> eyes lit up when he realized we’d be able to quickly set up a demo from a feature branch to show a customer a fully-functioning custom integration they might have asked about, all without needing to have our GTM team setup a local coding environment. They just click on the frontend link and do their full demo.
Our engineers have been using the sandboxes for demoing and more importantly sharing changes. It has been particularly nice for async review of large coupled frontend/backend reworks.

I myself use the sandboxes whenever I need to test how certain objects work in our cloud environment or when I develop a feature with a frontend component that I want feedback on.


## Leftover crumbs
No project like this is perfect and of course right out the gate a few requests have landed. 

The most consistent feedback I have gotten is that real-time syncing of the database would be nice. As soon as developers and GTM realized that all their content from stable sandboxes could be available, they asked how easy it would be to keep all the sandboxes in sync. Unfortunately in the current system I don’t see a good way to get true real-time syncing because we cannot expect the db schema to be the same between an ephemeral sandbox and the stable sandbox.

I have also been asked about the reverse, i.e. syncing changes from ephemeral sandboxes back to the stable sandbox. This is similarly challenging but slightly more realistic because we could potentially copy over data after the PR contents make it into the stable sandbox.

Surprisingly the startup time of 14 minutes for a fresh sandbox has not been subject to criticism. Developers find something else to do in the meantime. I have identified work to get about 6 minutes of potential time saves but they are more involved and startup time does not seem to be a big issue currently.

Scalability of ephemeral sandboxes isn’t a huge factor for us as a team right now but when it becomes more important, I will also have to revisit shaping our infra so it can more accurately dynamically scale to the demands of spinning up sandboxes, especially the db.

## About the LocalStack-shaped elephant in the room
Why build all this when LocalStack exists? I frankly didn’t know about LocalStack’s sandbox support and only learned about it when Bill Easton was lauding them on LinkedIn. I certainly learned a lot about the wiring and internals of our AWS setup and the limitations of per-account AWS resources in the process and would definitely consider a solution like LocalStack if I was to do this again. That being said, the crunchiest parts of the project, e.g. generating, updating and maintaining the template DB, would have still been required. 

## Why not build this in Kubernetes
The sandboxing use case does sound like a perfect fit for kubernetes - spinning up and down sandboxes.
Our main deployment does however not run on k8s, so if we wanted the sandboxes to model our production stack, we would have to move all of that over to k8s.
Most of the difficulty in this process also did not come from starting/shutting down the AWS resources. The most difficult part was getting the database seeding right, and k8s doesn’t help with that. As a result the move to k8s did not seem worth it for our use case. When the time is right, we will revisit a port to k8s.
Currently, I am considering moving most of our deployment to a parametrized CloudFormation template so we have an even easier time spinning up/down instances. 

![Lego Figure in Sandbox](/assets/blog/2026-08-10/sandbox2_1920px.png "Lego figure standing inside a lego sandbox")



## What’s next

It’s a running joke at work that my three values are observability, observability, observability. Since the logs from these sandboxes are tagged with the sandbox ID, it should be easy for us to make a nice dashboard with a switcher so we can observe any individual sandbox from the same dashboard instead of creating a new dashboard for each and flooding our dashboard section.
Being able to see the backend activity visualized like that is really handy when testing new backend features and will be the next thing I build when I get the time.

This has been my favorite infra project so far because it really had me dig through all aspects of our infra, from the networking intricacies and zero-downtime deployment to db setup strategies. The best part has been the positive response and regular usage from the team, which is what makes me consider this a success. 

Other than adding observability and fixing a few issues with the implementation, much like for the developers at shopify, user feedback and user data will tell me what direction I get to push this project next.
There is also potential in using these sandboxes for letting agents experiment, but that and all the associated engineering changes might be the subject of a future writeup.
