This repository accompanies the Network Test Pyramid blog. 

# Running the test suite

1. Clone this repo
2. In a Python virtual environment: 
   - `pip install -r requirements.txt`
   - `pytest test_suite`

# Repository organization

- The `test_suite` folder has the tests, written as pytest modules. 
- The `snapshot` folder has the network snapshot that is used in the tests.
- The `SoT` folder represents a mock source of truth for the network. `test-suite/sot_utils.py` makes this and other information available to the tests. 