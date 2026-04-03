# Hard Test 3: JAL + JALR (function call and return)
# Function placed before main so halt stays last
jal ra, main
func: addi a0, a0, 3
jalr zero, ra, 0
main: addi a0, zero, 7
jal ra, func
addi t1, zero, 1
beq zero, zero, 0
