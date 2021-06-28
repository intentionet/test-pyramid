This repository accompanies [the Networking Test Pyramid blog](https://www.intentionet.com/blog/the-networking-test-pyramid/). 

# Running the test suite

## Setup
1. Run the Batfish service. Details [here](https://pybatfish.readthedocs.io/en/latest/getting_started.html); short version:
   - `docker pull batfish/allinone`
   - `docker run --name batfish -v batfish-data:/data -p 8888:8888 -p 9997:9997 -p 9996:9996 batfish/allinone`
3. Clone this repo:
   - ` git clone git@github.com:intentionet/test-pyramid.git`
4. Install dependencies. In the top-level folder where you cloned the repo, and ideally in a Python virtual environment, do: 
   - `pip install -r requirements.txt`


## Running on the example network

This repo contains an example network that you can use to play with the test suite. 

 - You can run the test suite on this network by running the following command in the top-level folder:

   `pytest test_suite`

   All tests should pass.

 - If you wanted to run tests at only one level of the pyramid, you can do: 

   `pytest -k config_content test_suite`

 - If you wanted to run a particular test, you can do: 
 
    `pytest -k test_no_duplicate_ips test_suite`

## Running on your network

To run the tests on your network, you need to supply your own network configs and your own source of truth. You may follow these steps

1. Package your network configurations. See the `snapshot` folder of this repo as an example--the short version is to put all router configuration files in a subfolder named `configs`. Full details [these instructions](https://pybatfish.readthedocs.io/en/latest/notebooks/interacting.html#Packaging-snapshot-data).

2. At this point, you can run tests that do not depend on network-specific input or the source of truth. Two such tests that you can run:

    `pytest -k test_no_duplicate_ips test_suite`
    `pytest -k test_no_undefined_references test_suite`

3. Now, you can port the test code to your network. A simple way to do that is to port over the constants and functions in `test_suite/sot_utils.py.` Many of these functions are based on the data in the `SoT` folder. 

   You may do this porting test at a time, updating the inputs for indiviidual tests and testing along the way. 


For questions or feedback, find us on [Slack](https://join.slack.com/t/batfish-org/shared_invite/enQtMzA0Nzg2OTAzNzQ1LTcyYzY3M2Q0NWUyYTRhYjdlM2IzYzRhZGU1NWFlNGU2MzlhNDY3OTJmMDIyMjQzYmRlNjhkMTRjNWIwNTUwNTQ).

# Repository overview

- The `test_suite` folder has the tests, written as pytest modules. 
- The `snapshot` folder has the network snapshot that is used in the tests.
- The `SoT` folder represents a mock source of truth for the network. 
- `test-suite/sot_utils.py` makes this information available to the tests. If you are adapting this test suite for your network, start by modifying this script to use your actual SoT. 

