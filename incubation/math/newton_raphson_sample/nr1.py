import numpy as np

# seed
x, y = 0.3, -0.03
tolerance = 1e-4  # 4 significant digits precision

# Funcs
def f(x, y):
    return (1.021 * x**2) / y + 4.953

def g(x, y):
    return 5.040 * x * y + 0.05440

# Jacobian
def df_dx(x, y):
    return 2 * 1.021 * x / y

def df_dy(x, y):
    return -1.021 * x**2 / y**2

def dg_dx(x, y):
    return 5.040 * y

def dg_dy(x, y):
    return 5.040 * x

# Newton-Raphson iteration
def newton_raphson(x, y, tolerance):
    iteration = 0
    while True:
        # Compute functions and Jacobian matrix
        F = np.array([-f(x, y), -g(x, y)])
        J = np.array([[df_dx(x, y), df_dy(x, y)], 
                      [dg_dx(x, y), dg_dy(x, y)]])
        
        # Solve J * delta = -F
        delta = np.linalg.solve(J, F)
        
        # Update x and y
        x_new, y_new = x + delta[0], y + delta[1]

        print(f"x_{iteration}: {x_new}, y_{iteration}: {y_new}, err_x: {delta[0]}, err_y: {delta[1]}")
        
        # Check for convergence
        if abs(delta[0]) <= tolerance and abs(delta[1]) <= tolerance:
            break
        
        # Update values for next iteration
        x, y = x_new, y_new
        iteration += 1

    return x_new, y_new, iteration

solution_x, solution_y, total_iterations = newton_raphson(x, y, tolerance)
print(f"\nSOL - x: {solution_x}, y: {solution_y}, iters: {total_iterations}")
