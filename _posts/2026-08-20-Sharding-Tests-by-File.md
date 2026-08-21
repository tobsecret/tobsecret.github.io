---
layout: post
title: "Sharding pytest by file cut collection time from 3 minutes to 40 seconds"
date: 2026-08-20 12:00:00 +0000
---

When your pytest CI unit test workflow starts taking longer and longer, you’ll want to speed it up. We don’t like to wait for tests to complete in CI, and while you can run them locally, eventually it will take a long time on your local machine as well. Waiting for tests to complete wastes developer time, so let’s speed up your pytest CI workflow.
The first most obvious step is to use a plugin like `xdist` to parallelize the tests across multiple workers. A standard GitHub Actions runner comes with two cores by default so we set `-n 2 --dist=loadgroup` which means we spawn two workers which get assigned a set of tests each.

Eventually this will be too slow as well and you will want to run multiple CI jobs with a matrix strategy.
We started using the `split` plugin for this which lets you record test times and split them into balanced shards so each matrix job should take around the same amount of time. We always have to wait for all tests to complete in our CI, so we care that they are well-balanced since the longest shard is the limiting factor.
The test durations are recorded in a `.test_durations` file that is committed into the repo. There will be drift over time so tests without known test duration will be assumed to have the arithmetic mean test duration from the known test durations.

Recently our test jobs had once again reached too high a duration and initially my plan was to just increase the number of shards again. However, even when doubling the shards I noticed only a minor speedup.
When going through the logs of the recent test run I noticed that pytest startup took over 3 minutes:

* Python, uv setup and syncing dependencies: ~25 seconds
* Docker/test infrastructure: ~16 seconds
* Pytest startup/import/collection: ~3 minutes
* Actual test execution: ~3½ minutes
{: style="margin-left: 40px;"}

Digging into it, it turns out the major slow down came from each shard and each worker in each shard collecting all of the test files. At around **18k** tests split across around **1.5k** files, the collection of tests was starting to add up to almost half of the runtime of our CI test jobs.

This makes sense since the shards are balanced by individual test times so there is no guarantee collection can skip any files, so the plugin lets pytest collect all tests and then tells it which ones to deselect in `pytest_collection_modifyitems`.

This fine-grained balancing of test shards by individual test durations can be necessary if you have outlier tests concentrated in just a few test files. However in our codebase we can balance shards for our unit tests by test files instead of by individual tests because test files generally have a small number of tests and outliers aren’t too extreme (our longest measured test file takes *24.8s*).

<iframe src="/assets/blog/2026-08-20/2026-08-20-beakr-file-test-duration-histogram.html" width="100%" height="600" style="border:none;"></iframe>

Figure 1: Histogram of test durations. X-axis is logarithmic. Longest test file took 24.8s, shortest under a ms. Bimodal distribution with means at 10ms and 1s.

Balancing by test shards allows us to use the `pytest_ignore_collect` hook to avoid collecting the entire test code base in each shard and instead only collect the assigned files.
Here an abridged time line of the `pytest_collect` phases:

##### pytest_collection
* pytest_ignore_collect<br>
Our sharder rejects unassigned directories and files<br>
→ rejected files are never imported
* pytest_collect_directory, pytest_collect_file, pytest_pycollect_makemodule, pytest_pycollect_makeitem, pytest_generate_tests<br>
→ collects tests and generates the test objects
* pytest_collection_modifyitems, pytest_deselected<br>
→ plugins apply filters, marks, reorders to collected items and finally lets plugins know about which tests have been deselected
{: style="margin-left: 40px;"}


Without file-based sharding test collection took 3:08 minutes: 

```
13:59:56 GMT ~  uv run pytest -n 2 --dist=loadgroup -m "not e2e” --splits 8 --group 4 --splitting-algorithm least_duration
14:03:04 GMT ~ ========================= test session starts =========================
```

With file-based sharding it took 40s:
```
20:48:10 GMT ~ uv run pytest -n 2 --dist=loadgroup -m "not e2e" --fsplits 8 --fgroup 4
20:48:50 GMT ~ ========================= test session starts =========================
```


**a tiny nitpick here - the second time stamp also includes the first test that was run, so there is variability introduced by that but we know that it’s not significant since our longest recorded test in test durations is 7s, so even if we double that we’re saving 2 minutes**

With around 1.7k runs (not shards, full runs) of our unit test CI workflow last month, that amounts to roughly 57 hours of time saved. Of course developers usually don’t sit there waiting for CI to finish, so this is a purely theoretical number and the more realistic return is that it feels good in the cases when you are eager for the tests to finish so you can submit a PR for review.

Without this optimization your test setup scales worse and worse through sharding as your test codebase grows and your test shards spend more and more of their time collecting tests and less time actually running tests. 

We built [pytest-fsplit](https://github.com/BeakrHub/pytest-fsplit) for this purpose. It's built with `pytest-xdist`, `pytest-split` and `nbval` in mind. 
You could of course also use an alternative like `rpytest` or `maelstrom` but for us this little pytest plugin was the right fix.

### Installation

```
pip install pytest-fsplit
```

### Usage

First record durations from a complete, unsharded run:

```
pytest --fsplit-store-durations
```
Which produces the aforementioned `.test_durations`.

Then run each file shard separately similar to how you would with `pytest-split`:

```
pytest --fsplits 4 --fgroup 1
pytest --fsplits 4 --fgroup 2
pytest --fsplits 4 --fgroup 3
pytest --fsplits 4 --fgroup 4
```