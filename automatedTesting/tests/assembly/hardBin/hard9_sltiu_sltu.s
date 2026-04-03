# Hard Test 9: sltiu + sltu comparison
addi t0, zero, -1
addi t1, zero, 1
slt  a0, t0, t1
sltu a1, t0, t1
sltiu a2, t0, 1
beq zero, zero, 0
