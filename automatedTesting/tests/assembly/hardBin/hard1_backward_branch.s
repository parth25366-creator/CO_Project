# Hard Test 1: Backward branch (loop)
# Counts down from 5 to 0 using bne
addi t0, zero, 5
addi t1, zero, 0
loop: addi t0, t0, -1
bne t0, t1, loop
beq zero, zero, 0
