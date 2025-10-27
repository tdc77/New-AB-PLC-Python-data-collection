import customtkinter as ctk
from pycomm3 import LogixDriver
from tkinter import filedialog, messagebox

class SetupPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.selected_tags = {}

        # Layout configuration
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)
        self.grid_columnconfigure(0, weight=1)

        # Header
        ctk.CTkLabel(self, text="🔧 Setup PLC Monitoring", font=("Arial", 24)).grid(row=0, column=0, pady=10)

        # Top frame
        self.top_frame = ctk.CTkFrame(self, fg_color="lightgrey")
        self.top_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.top_frame.grid_columnconfigure((1, 3), weight=1)

        # ---- IP Address ----
        ctk.CTkLabel(self.top_frame, text="IP Address:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.ip_entry = ctk.CTkEntry(self.top_frame, placeholder_text="192.168.1.1")
        self.ip_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # ---- Interval ----
        ctk.CTkLabel(self.top_frame, text="Interval (s):").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.interval_entry = ctk.CTkEntry(self.top_frame, placeholder_text="2")
        self.interval_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        # ---- Excel Save File ----
        ctk.CTkLabel(self.top_frame, text="Save File:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.excel_entry = ctk.CTkEntry(self.top_frame, placeholder_text="PLC_Log.xlsx")
        self.excel_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.top_frame, text="Browse", command=self.select_save_file).grid(row=1, column=2, padx=5, pady=5)

        # ---- Test Connection ----
        ctk.CTkButton(self.top_frame, text="Test PLC Connection", fg_color="green", command=self.test_connection).grid(row=1, column=3, padx=5, pady=5)

        # Load saved values
        self.ip_entry.insert(0, controller.shared_data.get("ip", ""))
        interval = controller.shared_data.get("interval", "")
        self.interval_entry.insert(0, str(interval) if interval else "")
        self.excel_entry.insert(0, controller.shared_data.get("excel_file", "PLC_Log.xlsx"))

        # Auto-save on typing
        self.ip_entry.bind("<KeyRelease>", self.update_shared_data)
        self.interval_entry.bind("<KeyRelease>", self.update_shared_data)
        self.excel_entry.bind("<KeyRelease>", self.update_shared_data)

        # Scrollable frame for tags
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        # Footer buttons
        btn_frame = ctk.CTkFrame(self)
        btn_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        btn_frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(btn_frame, text="Connect & Load Tags", command=self.load_tags).grid(row=0, column=0, padx=10)
        ctk.CTkButton(btn_frame, text="💾 Save Selection & Start Logging", command=self.save_selection).grid(row=0, column=1, padx=10)
        ctk.CTkButton(btn_frame, text="⬅ Back to Main", command=lambda: controller.show_frame("MainPage")).grid(row=0, column=2, padx=10)

    # ---------------- Update Shared Data ----------------
    def update_shared_data(self, event=None):
        self.controller.shared_data["ip"] = self.ip_entry.get().strip()
        interval_text = self.interval_entry.get().strip()
        try:
            interval = float(interval_text)
            if interval <= 0:
                raise ValueError
            self.controller.shared_data["interval"] = interval
        except ValueError:
            self.controller.shared_data["interval"] = None
            if interval_text:
                messagebox.showwarning("Invalid Interval", "Please enter a positive number for the interval.")

        excel_file = self.excel_entry.get().strip()
        self.controller.shared_data["excel_file"] = excel_file if excel_file else "PLC_Log.xlsx"

        if hasattr(self.controller, "notify_data_change"):
            self.controller.notify_data_change()

    # ---------------- Test PLC Connection ----------------
    def test_connection(self):
        ip = self.ip_entry.get().strip()
        if not ip:
            messagebox.showwarning("Missing IP", "Please enter a PLC IP address first.")
            return
        try:
            with LogixDriver(ip) as plc:
                _ = plc.tags
            messagebox.showinfo("Success", f"Successfully connected to PLC at {ip}")
        except Exception as e:
            messagebox.showerror("Connection Failed", f"Failed to connect to PLC:\n{e}")

    # ---------------- Load Tags ----------------
    def load_tags(self):
        ip = self.ip_entry.get().strip()
        self.controller.shared_data["ip"] = ip

        if not ip:
            messagebox.showwarning("Missing IP", "Please enter a PLC IP address before loading tags.")
            return

        try:
            with LogixDriver(ip) as plc:
                all_tags = plc.tags
        except Exception as e:
            all_tags = []
            messagebox.showerror("Connection Error", f"Failed to connect to PLC: {e}")

        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.selected_tags = {}

        ctk.CTkLabel(self.scrollable_frame, text="Tag Name", anchor="w").grid(row=0, column=0, sticky="w", padx=5)
        ctk.CTkLabel(self.scrollable_frame, text="Array Elements (optional)").grid(row=0, column=1, padx=5)

        for i, tag in enumerate(all_tags, start=1):
            var = ctk.BooleanVar(value=False)
            entry = ctk.CTkEntry(self.scrollable_frame, width=60, placeholder_text="e.g. 5")
            entry.grid(row=i, column=1, padx=5, pady=2)
            entry.configure(state="disabled")

            def toggle_entry(v=var, e=entry, t=tag):
                if v.get():
                    e.configure(state="normal")
                else:
                    e.delete(0, "end")
                    e.configure(state="disabled")
                    self._remove_expanded_elements(t)

            cb = ctk.CTkCheckBox(self.scrollable_frame, text=tag, variable=var, command=toggle_entry)
            cb.grid(row=i, column=0, sticky="w", padx=5, pady=2)

            self.selected_tags[tag] = {"var": var, "entry": entry, "expanded": []}
            entry.bind("<Return>", lambda event, t=tag: self._expand_array(t))

    # ---------------- Expand/Remove Array ----------------
    def _expand_array(self, tag):
        widgets = self.selected_tags.get(tag)
        if not widgets:
            return
        arr_len = widgets["entry"].get().strip()
        self._remove_expanded_elements(tag)
        if arr_len.isdigit() and int(arr_len) > 0:
            n = int(arr_len)
            expanded_vars = []
            base_row = list(self.selected_tags.keys()).index(tag) + 1
            for i in range(n):
                element_name = f"{tag}[{i}]"
                var = ctk.BooleanVar(value=True)
                cb = ctk.CTkCheckBox(self.scrollable_frame, text=element_name, variable=var)
                cb.grid(row=base_row + i, column=0, columnspan=2, sticky="w", padx=30, pady=1)
                expanded_vars.append((element_name, var, cb))
            widgets["expanded"] = expanded_vars

    def _remove_expanded_elements(self, tag):
        widgets = self.selected_tags.get(tag)
        if not widgets:
            return
        for _, _, cb in widgets["expanded"]:
            cb.destroy()
        widgets["expanded"] = []

    # ---------------- Save Selection ----------------
    def save_selection(self):
        selected = []
        for tag, widgets in self.selected_tags.items():
            if widgets["var"].get():
                arr_len = widgets["entry"].get().strip()
                if arr_len.isdigit() and int(arr_len) > 0:
                    selected.append(f"{tag}{{{arr_len}}}")
                else:
                    selected.append(tag)

        self.controller.shared_data["tags_to_monitor"] = selected
        print(f"Selected tags: {selected}")

        if hasattr(self.controller, "notify_data_change"):
            self.controller.notify_data_change()

        # ✅ Automatically start logging on MainPage
        main_page = self.controller.frames.get("MainPage")
        if main_page:
            main_page.stop_refresh()  # stop any old refresh
            main_page.start_refresh()  # start immediately
            self.controller.show_frame("MainPage")  # navigate back
            messagebox.showinfo("Logging Started", "Data collection has started automatically.")


            # ---------------- Select Save File ----------------
    def select_save_file(self):
        """Open file dialog to choose where logs will be saved."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
            title="Select Excel Save Location"
        )
        if filename:
            self.excel_entry.delete(0, "end")
            self.excel_entry.insert(0, filename)
            self.controller.shared_data["excel_file"] = filename
            print(f"💾 Excel save file set to: {filename}")
            if hasattr(self.controller, "notify_data_change"):
                self.controller.notify_data_change()
