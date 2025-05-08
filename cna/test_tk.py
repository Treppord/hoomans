import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("Tkinter Test")
root.geometry("300x200")

label = ttk.Label(root, text="Hello World")
label.pack(pady=20)

button = ttk.Button(root, text="Click Me", command=lambda: print("Button clicked"))
button.pack(pady=20)

root.mainloop()