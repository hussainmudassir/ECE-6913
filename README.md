## How to run the project:

# File structure 

```
-Project (ECE-6193)
    -test_cases
        -TC0
            -ExpectedResults
            -Code.asm
            -dmem.txt
            -imem.txt
        -TC1
            -ExpectedResults
            -Code.asm
            -dmem.txt
            -imem.txt
        -TC2
            -ExpectedResults
            -Code.asm
            -dmem.txt
            -imem.txt
        -TC3
            -ExpectedResults
            -Code.asm
            -dmem.txt
            -imem.txt
        -TC4
            -ExpectedResults
            -Code.asm
            -dmem.txt
            -imem.txt
    -dmem.txt
    -imem.txt
    -final.py
    -README.md

```

## TO RUN THE PROJECT:

    There are two ways to run the project.
    1. Bulk run all the test cases
    2. Test custom test case one at a time.

    1. Bulk run all the test cases
        To run the all the test cases, we need to put all the TCs in the test_cases folder  and run the following command:

`python3 final.py --iodir test_cases`

        This command will pick each test case and add the output file in the same tc folder as the input. 
    
    2. Test custom test case one at a time. 
        To run just one test case or a custom test case, we need to add dmem.txt and imem.txt in the same directory as final.py and run the following command:

`python3 final.py`

        The output of the same will be generated in the same directory as the input. 