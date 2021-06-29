This repository accompanies [the Networking Test Pyramid blog](https://www.intentionet.com/blog/the-networking-test-pyramid/). 

# Running the test suite

1. Download and run Batfish. Details [here](https://pybatfish.readthedocs.io/en/latest/getting_started.html); short version:
   - `docker pull batfish/allinone`
   - `docker run --name batfish -v batfish-data:/data -p 8888:8888 -p 9997:9997 -p 9996:9996 batfish/allinone`
3. Clone this repo
4. In a Python virtual environment: 
   - `pip install -r requirements.txt`
   - `pytest test_suite`

## Running on the example network

This repo contains an example network that you can use to play with the test suite. 

 - You can run the test suite on this network by running the following command in the top-level folder:

   `pytest -v test_suite`

    The `-v` command line options will make pytest print the pass-fail status of each test is runs. Otherwise, only a summary and information about failing tests is printed on the console. All tests should pass if you run the test suite without modifying any test or network config. 
    
    Feel free to change network configs in `snapshot/configs` and observe their impact on test status. The following commands may help you in such an exploration.

 - If you wanted to run tests at only one level of the pyramid, you can do: 

   `pytest -v -k config_content test_suite`
   
   `-k` is a powerful pytest command line option that lets you run a subset of the tests by supplying a pattern. Full documentation is [here](https://docs.pytest.org/en/latest/example/markers.html#using-k-expr-to-select-tests-based-on-their-name) but common patterns include a subset of the name of the test module or the test name. 
   
   You can find out all the tests and modules in the test suite via 
   
   `pytest --collect-only test_suite` 
   
 - So, if you wanted to run a particular test, you can do: 
 
    `pytest -v -k test_no_duplicate_ips test_suite`
    
 - Or, if you wanted to run all tests with the word 'blocked' in them, you can do:   

    `pytest -v -k blocked test_suite`
    

## Running on your network

To run the tests on your network, you need to supply your own network configs and your own source of truth. You may follow these steps

1. Package your network configurations. See the `snapshot` folder of this repo as an example--the short version is to put all router configuration files in a subfolder named `configs`. Full details [these instructions](https://pybatfish.readthedocs.io/en/latest/notebooks/interacting.html#Packaging-snapshot-data).

2. At this point, you can run tests that do not depend on network-specific input or the source of truth. In the test suite, we have marked such tests as `network_independent` and you can run them via:

    `pytest -v -k network_independent test_suite`

3. Now, you can port the tests that are relevant for your network--not all tests in the test suite may be meaningful for you. A simple way to do that is to port over the constants and functions in `test_suite/sot_utils.py.` Many of these functions are based on the data in the `SoT` folder. 

   You may do this porting test at a time, updating the inputs for individual tests and testing along the way. 

4. Develop new tests that are relevant for your network, e.g., for behaviors your ACLs and firewall rules are intended to implement or for end-to-end connectivity properties of your network.

For questions or feedback, find us on [Slack](https://join.slack.com/t/batfish-org/shared_invite/enQtMzA0Nzg2OTAzNzQ1LTcyYzY3M2Q0NWUyYTRhYjdlM2IzYzRhZGU1NWFlNGU2MzlhNDY3OTJmMDIyMjQzYmRlNjhkMTRjNWIwNTUwNTQ).

# Repository overview

- The `test_suite` folder has the tests, written as pytest modules. 
- The `snapshot` folder has the network snapshot that is used in the tests.
- The `SoT` folder represents a mock source of truth for the network. 
- `test-suite/sot_utils.py` makes this information available to the tests. If you are adapting this test suite for your network, start by modifying this script to use your actual SoT. 
