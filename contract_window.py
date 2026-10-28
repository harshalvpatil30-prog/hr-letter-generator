import os
import sys
import time
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

from tkcalendar import DateEntry
from letter_engine import generate_contract
from signer import sign_pdf
from drive_sync import upload_pdf


def open_file(path):
    if sys.platform.startswith("win"):
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.run(["open", path])
    else:
        subprocess.run(["xdg-open", path])


class ContractWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Employment Contract")
        self.resizable(False, False)

        frm = ttk.Frame(self, padding=20)
        frm.grid()
        ttk.Label(frm, text="Employment Contract",
                  font=("Segoe UI", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 15))

        self.name_var = tk.StringVar()
        self.role_var = tk.StringVar()
        self.addr_var = tk.StringVar()
        self.salary_var = tk.StringVar()
        self.prob_var = tk.StringVar(value="6")
        self.notice_var = tk.StringVar(value="60")

        rows = [
            ("Employee name *", ttk.Entry(frm, textvariable=self.name_var, width=32)),
            ("Designation *", ttk.Entry(frm, textvariable=self.role_var, width=32)),
            ("Address *", ttk.Entry(frm, textvariable=self.addr_var, width=32)),
            ("Annual CTC (INR) *", ttk.Entry(frm, textvariable=self.salary_var, width=32)),
            ("Probation (months)", ttk.Entry(frm, textvariable=self.prob_var, width=32)),
            ("Notice period (days)", ttk.Entry(frm, textvariable=self.notice_var, width=32)),
        ]
        self.start_picker = DateEntry(frm, width=29, date_pattern="dd-mm-yyyy")
        self.issue_picker = DateEntry(frm, width=29, date_pattern="dd-mm-yyyy")
        rows.append(("Joining date *", self.start_picker))
        rows.append(("Agreement date", self.issue_picker))

        for i, (label, widget) in enumerate(rows, start=1):
            ttk.Label(frm, text=label).grid(row=i, column=0, sticky="w", pady=4, padx=(0, 12))
            widget.grid(row=i, column=1, pady=4)

        self.btn = ttk.Button(frm, text="Generate Contract", command=self.on_generate)
        self.btn.grid(row=20, column=0, columnspan=2, pady=(14, 5), ipadx=20, ipady=4)
        self.status = ttk.Label(frm, text="", foreground="gray", wraplength=340)
        self.status.grid(row=21, column=0, columnspan=2)

    def on_generate(self):
        name = self.name_var.get().strip()
        role = self.role_var.get().strip()
        addr = self.addr_var.get().strip()
        if not name or not role or not addr:
            messagebox.showwarning("Missing details", "Name, designation and address are required.", parent=self)
            return
        try:
            salary = int(self.salary_var.get().replace(",", "").strip())
            probation = int(self.prob_var.get())
            notice = int(self.notice_var.get())
        except ValueError:
            messagebox.showwarning("Invalid number", "CTC, probation and notice must be whole numbers.", parent=self)
            return

        data = {
            "name": name, "role": role, "address": addr,
            "salary": salary, "probation_months": probation, "notice_days": notice,
            "start_date": self.start_picker.get_date(),
            "issue_date": self.issue_picker.get_date(),
        }
        upload = self.parent.upload_var.get()     # reuse the main window's checkbox
        self.btn.config(state="disabled")
        threading.Thread(target=self._worker, args=(data, upload), daemon=True).start()

    def _worker(self, data, upload):
        start = time.time()
        try:
            self._set_status("Generating contract...")
            path = generate_contract(data)
            self._set_status("Signing document...")
            signed = sign_pdf(path, reason="Employment agreement")
        except Exception as e:
            self.after(0, self._finish, None, f"Could not create the contract:\n{e}", 0)
            return

        warning = None
        if upload:
            try:
                self._set_status("Uploading to Google Drive...")
                upload_pdf(signed)
            except Exception as e:
                warning = f"Saved locally, but Drive upload failed:\n{e}"
        self.after(0, self._finish, signed, warning, time.time() - start)

    def _set_status(self, text):
        self.after(0, lambda: self.status.config(text=text, foreground="gray"))

    def _finish(self, signed, message, elapsed):
        self.btn.config(state="normal")
        if signed is None:
            self.status.config(text="Failed.", foreground="red")
            messagebox.showerror("Error", message, parent=self)
            return
        if message:
            self.status.config(text="Signed. Drive upload failed.", foreground="orange")
            messagebox.showwarning("Drive upload failed", message, parent=self)
        else:
            self.status.config(text=f"Done in {elapsed:.1f}s: {os.path.basename(signed)}",
                               foreground="green")
        open_file(signed)