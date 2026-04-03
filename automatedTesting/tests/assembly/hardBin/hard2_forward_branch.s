# Hard Test 2: Forward branch (branch over instructions)
addi t0, zero, 10
addi t1, zero, 10
beq t0, t1, skip
addi t2, zero, 1
addi t3, zero, 2
skip: addi t2, zero, 99
beq zero, zero, 0
