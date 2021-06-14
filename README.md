This repository accompanies the Network Test Pyramid blog. 

# Running the test suite

1. Download and run Batfish. Details [here](https://pybatfish.readthedocs.io/en/latest/getting_started.html); short version:
   - `docker pull batfish/allinone`
   - `docker run --name batfish -v batfish-data:/data -p 8888:8888 -p 9997:9997 -p 9996:9996 batfish/allinone`
3. Clone this repo
4. In a Python virtual environment: 
   - `pip install -r requirements.txt`
   - `pytest test_suite`

# Repository organization

- The `test_suite` folder has the tests, written as pytest modules. 
- The `snapshot` folder has the network snapshot that is used in the tests.
- The `SoT` folder represents a mock source of truth for the network. 
- `test-suite/sot_utils.py` makes this information available to the tests. If you are adapting this test suite for your network, start by modifying this script to use your actual SoT. 
