import customtkinter as ctk
from tkinter import ttk
from pycomm3 import LogixDriver
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class MainPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.controller.register_listener(self.on_shared_data_update)
        self._after_ids = []  # Track all after() jobs

        # Shared state
        self.log_df = self.controller.shared_data.get("dataframe", pd.DataFrame())
        self.current_date = datetime.date.today()
        self.tree = None
        self.refresh_job = None
        self.checkbox_vars = {}
        self.selected_columns = set()

        # ---------------- Layout ----------------
        self.grid_rowconfigure((0, 1, 2, 3), weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ---------- Header ----------
        header = ctk.CTkFrame(self, fg_color="gray30", corner_radius=15)
        header.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
        ctk.CTkLabel(header, text="📊 Main Dashboard", font=("Arial", 22, "bold")).pack(pady=10)

        # ---------- Body ----------
        body = ctk.CTkFrame(self, fg_color="gray20", corner_radius=15)
        body.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        body.grid_columnconfigure((0, 1, 2), weight=1)
        body.grid_rowconfigure(0, weight=1)

        # --- Controls (left) ---
        control_frame = ctk.CTkFrame(body, fg_color="gray25", corner_radius=10)
        control_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        ctk.CTkButton(control_frame, text="⚙ Go to Setup Page",
                      command=lambda: controller.show_frame("SetupPage")).pack(pady=10)
        ctk.CTkButton(control_frame, text="▶ Start Logging", command=self.start_refresh).pack(pady=10)
        ctk.CTkButton(control_frame, text="⏹ Stop Logging", command=self.stop_refresh).pack(pady=10)
        ctk.CTkButton(control_frame, text="🧹 Clear Table", command=self.clear_table).pack(pady=10)

        # --- Chart area (middle) ---
        chart_frame = ctk.CTkFrame(body, fg_color="gray25", corner_radius=10)
        chart_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        chart_frame.grid_rowconfigure(0, weight=1)
        chart_frame.grid_columnconfigure(0, weight=1)

        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.ax.set_title("Live Tag Values")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Value")
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        # --- Checkbox area (right) ---
        self.checkbox_frame = ctk.CTkScrollableFrame(body, fg_color="gray25", corner_radius=10)
        self.checkbox_frame.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)
        ctk.CTkLabel(self.checkbox_frame, text="Select Columns to Plot:",
                     font=("Arial", 14, "bold")).pack(pady=5)

        # ---------- Footer ----------
        footer = ctk.CTkFrame(self, fg_color="gray15", corner_radius=15)
        footer.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        footer.grid_rowconfigure(0, weight=1)
        footer.grid_columnconfigure(0, weight=1)

        # Live Table
        self.table_frame = ctk.CTkFrame(footer, fg_color="white", corner_radius=10)
        self.table_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)
        self.create_table()

    # ---------------- Shared Data Sync ----------------
    def on_shared_data_update(self, new_data):
        print("🔄 Shared data updated:", new_data)
        self.current_ip = new_data.get("ip")
        self.current_interval = new_data.get("interval")
        self.current_tags = new_data.get("tags_to_monitor")
        self.controller.data_view = new_data.get("dataframe", self.controller.shared_data["dataframe"])

        if self.refresh_job:
            self.stop_refresh()
            self.start_refresh()
            print("✅ Logging restarted with new settings.")

    # ---------------- Table ----------------
    def create_table(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        self.tree = ttk.Treeview(self.table_frame, show="headings")
        self.tree.grid(row=0, column=0, sticky="nsew")

        y_scroll = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll = ttk.Scrollbar(self.table_frame, orient="horizontal", command=self.tree.xview)
        x_scroll.grid(row=1, column=0, sticky="ew")

        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        if not self.log_df.empty:
            self.tree["columns"] = list(self.log_df.columns)
            for col in self.log_df.columns:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=120, anchor="center")
            for _, row in self.log_df.iterrows():
                self.tree.insert("", "end", values=row.tolist())
            self.tree.yview_moveto(1.0)
            self.update_checkboxes()

    def update_checkboxes(self):
        for widget in self.checkbox_frame.winfo_children():
            if isinstance(widget, ctk.CTkCheckBox):
                widget.destroy()
        self.checkbox_vars.clear()

        if self.log_df.empty:
            return

        for col in self.log_df.columns:
            if col in ("Timestamp", "Error", "Info"):
                continue
            var = ctk.BooleanVar(value=True)
            chk = ctk.CTkCheckBox(
                self.checkbox_frame,
                text=col,
                variable=var,
                command=self.update_selected_columns
            )
            chk.pack(anchor="w", pady=2, padx=10)
            self.checkbox_vars[col] = var

        self.update_selected_columns()

    def update_selected_columns(self):
        self.selected_columns = {
            col for col, var in self.checkbox_vars.items() if var.get()
        }
        self.update_chart()

    # ---------------- Unified Refresh ----------------
    def start_refresh(self):
        for after_id in getattr(self, "_after_ids", []):
            try:
                self.after_cancel(after_id)
            except Exception:
                pass
        self._after_ids.clear()

        tags = self.controller.shared_data.get("tags_to_monitor", [])
        interval_sec = self.controller.shared_data.get("interval")
        ip = self.controller.shared_data.get("ip")

        if not tags or not interval_sec or not ip:
            print("⚠️ Logging not started: missing IP, tags, or interval.")
            return

        try:
            interval_sec = float(interval_sec)
        except (ValueError, TypeError):
            print("⚠️ Invalid interval. Logging not started.")
            return

        self._run_refresh_loop(int(interval_sec * 1000))
        print(f"▶ Unified logging started every {interval_sec}s from {ip}")

    def _run_refresh_loop(self, interval_ms):
        if not self.winfo_exists():
            return

        try:
            self.update_table()
            self.update_chart()
        except Exception as e:
            print(f"⚠️ Refresh loop error: {e}")

        after_id = self.after(interval_ms, lambda: self._run_refresh_loop(interval_ms))
        self._after_ids.append(after_id)
        self.refresh_job = after_id

    def stop_refresh(self):
        for after_id in getattr(self, "_after_ids", []):
            try:
                self.after_cancel(after_id)
            except Exception:
                pass
        self._after_ids.clear()
        self.refresh_job = None
        print("⏹ Unified logging stopped.")

    # ---------------- Data Logging ----------------
    def update_table(self):
        tags = self.controller.shared_data.get("tags_to_monitor", [])
        ip = self.controller.shared_data.get("ip")
        now = datetime.datetime.now()
        data = {"Timestamp": now.strftime("%Y-%m-%d %H:%M:%S")}

# --- Check if date changed (midnight rollover) ---
        if now.date() != self.current_date:
            print("🌙 Midnight reached — creating new Excel file.")
            self.save_log_to_excel()
            self.log_df = pd.DataFrame()  # start a fresh sheet
            self.create_table()
            self.current_date = now.date()


        if tags and ip:
            try:
                with LogixDriver(ip) as plc:
                    for tag in tags:
                        value = plc.read(tag).value
                        if isinstance(value, (list, tuple)):
                            for i, v in enumerate(value):
                                data[f"{tag}[{i}]"] = v
                        else:
                            data[tag] = value
            except Exception as e:
                data["Error"] = str(e)
        else:
            data["Info"] = "No tags selected"

        self.log_df = pd.concat([self.log_df, pd.DataFrame([data])], ignore_index=True)
        self.controller.shared_data["dataframe"] = self.log_df

        if self.tree is None:
            self.create_table()
        else:
            current_columns = set(self.tree["columns"])
            new_columns = set(self.log_df.columns)
            if current_columns != new_columns:
                self.create_table()
            row_values = self.log_df.iloc[-1].tolist()
            self.tree.insert("", "end", values=row_values)
            self.tree.yview_moveto(1.0)
            self.auto_adjust_columns()


    def save_log_to_excel(self):
        """Save current log_df to an Excel file named by date."""
        if self.log_df.empty:
            print("ℹ️ No data to save yet.")
            return

        date_str = datetime.date.today().strftime("%Y-%m-%d")
        filename = f"log_{date_str}.xlsx"

        try:
            self.log_df.to_excel(filename, index=False)
            print(f"💾 Log saved to {filename}")
        except Exception as e:
            print(f"⚠️ Failed to save log to Excel: {e}")

    def auto_adjust_columns(self):
        if not self.tree:
            return
        for col in self.tree["columns"]:
            max_width = len(col) * 10
            for row_id in self.tree.get_children():
                cell_value = str(self.tree.set(row_id, col))
                max_width = max(max_width, len(cell_value) * 10)
            self.tree.column(col, width=max_width)

    def clear_table(self):
        self.log_df = pd.DataFrame()
        self.controller.shared_data["dataframe"] = self.log_df
        if self.tree:
            for row in self.tree.get_children():
                self.tree.delete(row)
        print("🧹 Table cleared.")

    # ---------------- Chart ----------------
    def update_chart(self):
        if self.log_df.empty:
            self.ax.clear()
            self.ax.text(0.5, 0.5, "No data yet", ha="center", va="center")
            self.canvas.draw()
            return

        self.ax.clear()

        # Safe timestamps
        if "Timestamp" in self.log_df.columns:
            x_values = pd.to_datetime(self.log_df["Timestamp"], errors="coerce")
        else:
            x_values = range(len(self.log_df))

        for col in self.selected_columns:
            if col in self.log_df.columns:
                y_values = pd.to_numeric(self.log_df[col], errors="coerce")
                self.ax.plot(x_values, y_values, label=col)

        if self.selected_columns:
            self.ax.legend()
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Value")
        self.ax.grid(True)
        self.fig.tight_layout()
        self.canvas.draw()

    # ---------------- Cleanup ----------------
    def on_close(self):
        """Stop all background jobs and safely shut down MainPage."""
        print("🛑 MainPage shutting down...")

        # --- Cancel all .after() jobs ---
        if hasattr(self, "_after_ids"):
            for after_id in self._after_ids:
              try:
                self.after_cancel(after_id)
              except Exception:
                pass
            self._after_ids.clear()

        # Cancel chart refresh if it exists
        if hasattr(self, "chart_refresh_job") and self.chart_refresh_job:
            try:
             self.after_cancel(self.chart_refresh_job)
            except Exception:
                pass
            self.chart_refresh_job = None

        # Cancel main refresh job if it exists
        if hasattr(self, "refresh_job") and self.refresh_job:
            try:
                self.after_cancel(self.refresh_job)
            except Exception:
                pass
            self.refresh_job = None

        # --- Safely close any matplotlib canvases ---
        try:
            if hasattr(self, "canvas"):
              self.canvas.get_tk_widget().destroy()
        except Exception:
            pass

        # --- Preserve last data state ---
        try:
            self.controller.shared_data["dataframe"] = self.log_df
        except Exception:
            pass

        
        self.save_log_to_excel()
    
        print("✅ MainPage closed safely — all timers canceled.")
