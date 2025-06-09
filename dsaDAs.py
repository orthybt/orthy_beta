import json
import os
import tkinter as tk
from tkinter import simpledialog, messagebox, scrolledtext

data_file = 'patients.json'

def load_data():
    if not os.path.exists(data_file):
        return []
    with open(data_file, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=4)

def add_patient(name, phone, notes):
    data = load_data()
    patient = {'name': name, 'phone': phone, 'notes': notes}
    data.append(patient)
    save_data(data)

def view_patients():
    data = load_data()
    patient_list = ""
    for i, patient in enumerate(data, 1):
        patient_list += f"{i}. Name: {patient['name']}, Phone: {patient['phone']}, Notes: {patient['notes']}\n"
    messagebox.showinfo("Patient List", patient_list if patient_list else "No patients found.")

# GUI setup
root = tk.Tk()
root.title("Dental Management")

def add_patient_gui():
    name = simpledialog.askstring("Input", "Enter patient name:")
    if not name:
        return
    phone = simpledialog.askstring("Input", "Enter phone number:")
    if not phone:
        return
    notes = simpledialog.askstring("Input", "Enter notes:")
    add_patient(name, phone, notes)
    messagebox.showinfo("Success", "Patient added successfully.")

add_btn = tk.Button(root, text="Add Patient", command=add_patient_gui)
add_btn.pack(pady=5)

view_btn = tk.Button(root, text="View Patients", command=view_patients)
view_btn.pack(pady=5)

exit_btn = tk.Button(root, text="Exit", command=root.quit)
exit_btn.pack(pady=5)

root.mainloop()