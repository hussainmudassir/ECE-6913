0:      LW R1, R0, #0       // Load Mem[R0+0] into R1 - Value 8
4:  C2: ADDI R2, R2, #4     // Increment R2 by 4
8:      BEQ R1, R2, C1      // If R1 != R2 branch to C1 (PC+8)
12:     JAL R3, C2          // Store PC + 4 in R3 and jump to C2 (PC-8)
16: C1: HALT                // Halt

/* Binary
00000000000000000000000010000011
00000000010000010000000100010011
00000000000100010000010001100011
11111111100111111111000111101111
11111111111111111111111111111111
*/