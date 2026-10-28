import os
import sys
import time
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog
from bulk import run_bulk
from tkinter import ttk, messagebox
from contract_window import ContractWindow
from tkcalendar import DateEntry
from letter_engine import generate_experience_letter
from signer import sign_pdf
from drive_sync import upload_pdf


def open_file(path: str):
    """Open the PDF in the default viewer, on any operating system."""
    if sys.platform.startswith("win"):
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.run(["open", path])
    else:
        subprocess.run(["xdg-open", path])


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HR Letter Generator")
        self.resizable(False, False)

        frm = ttk.Frame(self, padding=20)
        frm.grid()

        ttk.Label(
            frm, text="Experience Letter", font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, columnspan=2, pady=(0, 15))

        self.name_var = tk.StringVar()
        self.role_var = tk.StringVar()
        self.dept_var = tk.StringVar()
        self.gender_var = tk.StringVar(value="Male")
        self.upload_var = tk.BooleanVar(value=True)      # NEW: checkbox state

        self._add_row(frm, 1, "Employee name *", ttk.Entry(frm, textvariable=self.name_var, width=32))
        self._add_row(frm, 2, "Designation *", ttk.Entry(frm, textvariable=self.role_var, width=32))
        self._add_row(frm, 3, "Department", ttk.Entry(frm, textvariable=self.dept_var, width=32))
        self._add_row(
            frm, 4, "Gender",
            ttk.Combobox(frm, textvariable=self.gender_var, width=29, state="readonly",
                         values=["Male", "Female", "Other"]),
        )

        self.start_picker = DateEntry(frm, width=29, date_pattern="dd-mm-yyyy")
        self.end_picker = DateEntry(frm, width=29, date_pattern="dd-mm-yyyy")
        self.issue_picker = DateEntry(frm, width=29, date_pattern="dd-mm-yyyy")
        self._add_row(frm, 5, "Joining date *", self.start_picker)
        self._add_row(frm, 6, "Last working day *", self.end_picker)
        self._add_row(frm, 7, "Letter date", self.issue_picker)

        # NEW: upload checkbox
        ttk.Checkbutton(
            frm, text="Upload to Google Drive", variable=self.upload_var
        ).grid(row=8, column=0, columnspan=2, sticky="w", pady=(8, 0))

        self.btn = ttk.Button(frm, text="Generate Letter", command=self.on_generate)
        self.btn.grid(row=9, column=0, columnspan=2, pady=(14, 5), ipadx=20, ipady=4)

        self.status = ttk.Label(frm, text="", foreground="gray", wraplength=340)
        self.status.grid(row=10, column=0, columnspan=2)

        self.bulk_btn = ttk.Button(frm, text="Bulk from CSV...", command=self.on_bulk)
        self.bulk_btn.grid(row=11, column=0, columnspan=2, pady=(6, 0))
        ttk.Button(frm, text="New Employment Contract...",
                   command=lambda: ContractWindow(self)).grid(row=12, column=0, columnspan=2, pady=(6, 0))

    @staticmethod
    def _add_row(parent, row, label, widget):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4, padx=(0, 12))
        widget.grid(row=row, column=1, pady=4)

    # ---------- Main thread: collect + validate ----------
    def on_generate(self):
        data = {
            "name": self.name_var.get().strip(),
            "role": self.role_var.get().strip(),
            "department": self.dept_var.get().strip(),
            "gender": self.gender_var.get(),
            "start_date": self.start_picker.get_date(),
            "end_date": self.end_picker.get_date(),
            "issue_date": self.issue_picker.get_date(),
        }

        if not data["name"] or not data["role"]:
            messagebox.showwarning("Missing details", "Employee name and designation are required.")
            return
        if data["end_date"] < data["start_date"]:
            messagebox.showwarning("Invalid dates", "Last working day cannot be before the joining date.")
            return

        self.btn.config(state="disabled")                # stop double-clicks
        upload = self.upload_var.get()
        threading.Thread(target=self._worker, args=(data, upload), daemon=True).start()

    # ---------- Background thread: the slow work ----------
    def _worker(self, data, upload):
        start = time.time()
        try:
            self._set_status("Generating PDF...")
            path = generate_experience_letter(data)
            self._set_status("Signing document...")
            signed = sign_pdf(path)
        except Exception as e:
            self.after(0, self._finish_error, f"Could not create the letter:\n{e}")
            return

        link, drive_error = None, None
        if upload:
            try:
                self._set_status("Uploading to Google Drive...")
                link = upload_pdf(signed)
            except Exception as e:
                drive_error = str(e)                     # letter is safe on disk

        elapsed = time.time() - start
        self.after(0, self._finish_ok, signed, link, drive_error, elapsed)

    # ---------- Helpers that update the screen (run on main thread) ----------
    def _set_status(self, text):
        self.after(0, lambda: self.status.config(text=text, foreground="gray"))

    def _finish_error(self, message):
        self.btn.config(state="normal")
        self.status.config(text="Failed.", foreground="red")
        messagebox.showerror("Error", message)

    def _finish_ok(self, signed, link, drive_error, elapsed):
        self.btn.config(state="normal")
        name = os.path.basename(signed)
        if drive_error:
            self.status.config(
                text=f"Signed and saved locally ({elapsed:.1f}s). Drive upload failed.",
                foreground="orange")
            messagebox.showwarning("Drive upload failed",
                                   f"The letter was saved at:\n{signed}\n\nDrive error:\n{drive_error}")
        elif link:
            self.status.config(text=f"Done in {elapsed:.1f}s. Signed and uploaded: {name}",
                               foreground="green")
        else:
            self.status.config(text=f"Done in {elapsed:.1f}s. Signed: {name}",
                               foreground="green")
        open_file(signed)

    def on_bulk(self):
        csv_path = filedialog.askopenfilename(
            title="Choose employee CSV", filetypes=[("CSV files", "*.csv")])
        if not csv_path:
            return
        self.btn.config(state="disabled")
        self.bulk_btn.config(state="disabled")
        upload = self.upload_var.get()
        threading.Thread(target=self._bulk_worker, args=(csv_path, upload),
                         daemon=True).start()

    def _bulk_worker(self, csv_path, upload):
        start = time.time()
        try:
            results = run_bulk(
                csv_path, upload,
                progress=lambda done, total: self._set_status(f"Processing {done}/{total}..."))
        except Exception as e:
            self.after(0, self._bulk_failed, str(e))
            return
        self.after(0, self._bulk_done, results, time.time() - start)

    def _bulk_failed(self, message):
        self.btn.config(state="normal")
        self.bulk_btn.config(state="normal")
        self.status.config(text="Bulk run failed.", foreground="red")
        messagebox.showerror("Error", message)

    def _bulk_done(self, results, elapsed):
        self.btn.config(state="normal")
        self.bulk_btn.config(state="normal")
        bad = [r for r in results if not r["ok"]]
        ok_count = len(results) - len(bad)
        self.status.config(
            text=f"{ok_count} created, {len(bad)} failed in {elapsed:.1f}s",
            foreground="green" if not bad else "orange")
        if bad:
            messagebox.showwarning(
                "Some rows failed",
                "\n".join(f"Line {r['line']} ({r['name']}): {r['error']}" for r in bad))    


if __name__ == "__main__":
    App().mainloop()