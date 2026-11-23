import numpy as np

# seed
x1, x2, x3 = 6, -6, 0

# Funcs
def f1(x1, x2, x3):
    return x1 * x2 * x3 - 4.188

def f2(x1, x2, x3):
    return x1 + x2 + x3 - 3.677

def f3(x1, x2, x3):
    return x1 + 1.258 * x2

# Jacobian
def df1_dx1(x1, x2, x3):
    return x2 * x3
def df1_dx2(x1, x2, x3):
    return x1 * x3
def df1_dx3(x1, x2, x3):
    return x1 * x2

def df2_dx1(x1, x2, x3):
    return 1
def df2_dx2(x1, x2, x3):
    return 1
def df2_dx3(x1, x2, x3):
    return 1

def df3_dx1(x1, x2, x3):
    return 1
def df3_dx2(x1, x2, x3):
    return 1.258
def df3_dx3(x1, x2, x3):
    return 0

def newton_raphson(x1, x2, x3):
    iteration = 0
    while iteration < 3:
        F = np.array([-f1(x1, x2, x3), -f2(x1, x2, x3), -f3(x1, x2, x3)])
        J = np.array([[df1_dx1(x1, x2, x3), df1_dx2(x1, x2, x3), df1_dx3(x1, x2, x3)], 
                      [df2_dx1(x1, x2, x3), df2_dx2(x1, x2, x3), df2_dx3(x1, x2, x3)],
                      [df3_dx1(x1, x2, x3), df3_dx2(x1, x2, x3), df3_dx3(x1, x2, x3)]])
        
        # J * delta_x = -F
        delta = np.linalg.solve(J, F)
        
        x1_new, x2_new, x3_new = x1 + delta[0], x2 + delta[1], x3 + delta[2]

        print(f"x1_{iteration}: {x1_new}, x2_{iteration}: {x2_new}, x3_{iteration}: {x3_new}, errs: [ {delta[0]}, {delta[1]}, {delta[2]} ]")
        
        # Update values for next iteration
        x1, x2, x3 = x1_new, x2_new, x3_new
        iteration += 1

    return x1_new, x2_new, x3_new, iteration

solution_x1, solution_x2, solution_x3, total_iterations = newton_raphson(x1, x2, x3)
print(f"\nSOL - x1: {solution_x1}, x2: {solution_x2}, x3: {solution_x3}, iters: {total_iterations}")
