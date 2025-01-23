from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QFileDialog, QVBoxLayout
import pandas as pd
import os
import subprocess
from pulp import LpProblem, LpMinimize, LpVariable, lpSum

class SchedulerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.filename = ""

    def initUI(self):
        self.setWindowTitle("Hungry Belly Scheduler!")
        self.setGeometry(100, 100, 400, 200)

        layout = QVBoxLayout()

        self.label = QLabel("Select a CSV or Excel file", self)
        layout.addWidget(self.label)

        self.btn_select = QPushButton("Load employee availability", self)
        self.btn_select.clicked.connect(self.openFileDialog)
        layout.addWidget(self.btn_select)

        self.btn_generate_lp = QPushButton("Convert", self)
        self.btn_generate_lp.clicked.connect(self.generateLP)
        self.btn_generate_lp.setEnabled(False)
        layout.addWidget(self.btn_generate_lp)

        self.btn_run_solver = QPushButton("Get Schedule", self)
        self.btn_run_solver.clicked.connect(self.runSolver)
        self.btn_run_solver.setEnabled(False)
        layout.addWidget(self.btn_run_solver)

        self.setLayout(layout)

    def openFileDialog(self):
        file_filter = "CSV Files (*.csv);;Excel Files (*.xlsx)"
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Employee File", "", file_filter)

        if file_name:
            self.filename = file_name
            self.label.setText(f"Selected: {os.path.basename(file_name)}")
            
            #converts xlsx to csv
            if file_name.endswith(".xlsx"):
                csv_filename = file_name.replace(".xlsx", ".csv")
                df = pd.read_excel(file_name)
                df.to_csv(csv_filename, index=False)
                self.filename = csv_filename

            self.btn_generate_lp.setEnabled(True)

    def generateLP(self):
        if not self.filename:
            return

        df = pd.read_csv(self.filename)

        required_columns = {"Employee", "Wage", "Trained", "MinHours", "MaxHours", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}
        if not required_columns.issubset(df.columns):
            self.label.setText("Incorrect format, try again! (Check your columns)")
            return

        employees = df["Employee"].tolist()
        wages = dict(zip(df["Employee"], df["Wage"]))
        is_trained = dict(zip(df["Employee"], df["Trained"]))
        min_hours = dict(zip(df["Employee"], df["MinHours"]))
        max_hours = dict(zip(df["Employee"], df["MaxHours"]))

        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        shifts = ["Lunch", "Dinner"]
        required_staff = {d: {"Lunch": 2, "Dinner": 4} for d in days}

        shift_durations = {"Lunch": 4, "Dinner": 6.5}

        availability = {}
        for _, row in df.iterrows():
            employee = row["Employee"]
            availability[employee] = {day: row[day] for day in days}

        self.prob = LpProblem("Workforce_Scheduling", LpMinimize)

        x = LpVariable.dicts("Assign", [(employee, day, shift) for employee in employees for day in days for shift in shifts], 0, 1, cat="Binary")

        self.prob += lpSum(wages[employee] * x[(employee, day, shift)] for employee in employees for day in days for shift in shifts), "Total_Cost"

        for day in days:
            for shift in shifts:
                self.prob += lpSum(x[(employee, day, shift)] for employee in employees) >= required_staff[day][shift], f"Shift_Coverage_{day}_{shift}"

        for day in days:
            for shift in shifts:
                self.prob += lpSum(x[(employee, day, s)] for e in employees if is_trained[employee]) >= 1, f"Trained_Coverage_{day}_{shift}"

        for employee in employees:
            self.prob += lpSum(shift_durations[shift] * x[(employee, day, shift)] for day in days for s in shifts) <= max_hours[employee], f"Max_Hours_{employee}"

        self.min_constraints = []
        for employee in employees:
            constraint = lpSum(shift_durations[shift] * x[(employee, day, shift)] for day in days for s in shifts) >= min_hours[employee]
            self.min_constraints.append(constraint)
            self.prob += constraint, f"Min_Hours_{employee}"

        for employee in employees:
            for day in days:
                for s in shifts:
                    if availability[employee][day] == "Neither":
                        self.prob += x[(employee, day, shift)] == 0, f"Availability_{employee}_{day}_{shift}"
                    elif availability[employee][day] == "Lunch" and s == "Dinner":
                        self.prob += x[(employee, day, shift)] == 0, f"Availability_{employee}_{day}_Dinner"
                    elif availability[employee][day] == "Dinner" and s == "Lunch":
                        self.prob += x[(employee, day, shift)] == 0, f"Availability_{employee}_{day}_Lunch"

        lp_filename = self.filename.replace(".csv", ".lp")
        self.prob.writeLP(lp_filename)

        self.label.setText(f"LP file generated: {os.path.basename(lp_filename)}")
        self.btn_run_solver.setEnabled(True)


    def runSolver(self):
        if not hasattr(self, 'prob'):
            self.label.setText("Need to convert first!")
            return

        lp_filename = self.filename.replace(".csv", ".lp")
        solution_filename = self.filename.replace(".csv", "_solution.txt")

        subprocess.run(["cbc", lp_filename, "solve", "-solu", solution_filename])

        with open(solution_filename, "r") as f:
            lines = f.readlines()
            if any("No feasible solution" in line for line in lines):
                self.label.setText("No feasible solution. Removing min hours constraint...")

                # Remove min hours constraint and resolve
                for constraint in self.min_constraints:
                    self.prob.constraints.pop(str(constraint))
                self.prob.writeLP(lp_filename)
                subprocess.run(["cbc", lp_filename, "solve", "-solu", solution_filename])

        shifts = ["Lunch", "Dinner"]
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        assignments = {d: {s: [] for s in shifts} for d in days}

        with open(solution_filename, "r") as file:
            for line in file:
                parts = line.strip().split()
                if len(parts) == 2 and "Assign" in parts[0]:
                    _, employee, day, shift = parts[0].split("_")
                    assignments[day][shift].append(employee)

        schedule_filename = self.filename.replace(".csv", "_schedule.csv")
        schedule_df = pd.DataFrame(
            [(d, s, ", ".join(assignments[d][s])) for d in days for s in shifts],
            columns=["Day", "Shift", "Employees"]
        )
        schedule_df.to_csv(schedule_filename, index=False)

        self.label.setText(f"Schedule saved: {os.path.basename(schedule_filename)}")

if __name__ == '__main__':
    app = QApplication([])
    window = SchedulerApp()
    window.show()
    app.exec()