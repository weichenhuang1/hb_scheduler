# Hungry Belly Scheduler

A PyQt6 desktop application for assigning employees to lunch/dinner shifts across the week, using linear programming. It reads employee availability from a CSV or Excel file, converts it to an LP model, and uses [CBC](https://github.com/coin-or/Cbc) to solve for an optimal schedule.

## Features

- **GUI built with PyQt6**  
  For easy file selection and interaction.

- **Flexible input**  
  Accepts CSV or Excel (`.xlsx`) files containing columns:

  | Employee | Wage | Trained | MinHours | MaxHours | Mon   | Tue   | Wed   | Thu   | Fri   | Sat   | Sun   |
  |----------|------|---------|----------|----------|-------|-------|-------|-------|-------|-------|-------|
  | John     | 20   | 1       | 5        | 20       | Both  | Dinner| ...   | ...   | ...   | ...   | ...   |

  - `Trained`: A boolean or 0/1 indicating if the employee is qualified (at least 1 qualified person is required per shift).  
  - `Mon` ... `Sun`: Possible values: `"Neither"`, `"Lunch"`, `"Dinner"`, or `"Both"`.

- **Automatic Excel -> CSV conversion**  
  If you load an `.xlsx` file, the app converts it to CSV before proceeding.

- **LP Model Generation**  
  - Creates a `.lp` file representing the linear program.  
  - Minimizes total wages.  
  - Ensures coverage (2 at Lunch, 4 at Dinner, plus at least 1 trained person for each shift).  
  - Enforces max/min hours when possible.

- **CBC Solver Execution**  
  Runs the Coin-OR CBC solver on the `.lp` file.  
  - If no feasible solution is found with min-hours constraints, the app automatically removes those constraints and re-solves.

- **Schedule Output**  
  Generates a CSV schedule with assigned employees for each day and shift.

## Requirements

- **Python 3.9+** (tested with Python 3.10)
- **PyQt6** (for the GUI)
- **pandas** (for CSV/Excel data handling)
- **PuLP** (for building the LP model)
- **CBC Solver**  
  - Ensure the `cbc` executable is on your system’s PATH.  
  - [Download CBC](https://github.com/coin-or/Cbc/releases) or install via conda (`conda install -c conda-forge coincbc`).

## Installation

1. Clone or download this repository:
   ```bash
   git clone https://github.com/your-username/hungry-belly-scheduler.git
   cd hungry-belly-scheduler
2. An executable file containing all dependencies needed can be found here: https://drive.google.com/file/d/1EEKNUqBs-LJToNp3Fdrr0tV8qOr0Daz4/view?usp=sharing
