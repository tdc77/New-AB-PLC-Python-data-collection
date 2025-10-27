import customtkinter as ctk
import pandas as pd
from pages.main_page import MainPage
from pages.setup_page import SetupPage
import tkinter as tk


class AppController(ctk.CTk):
    """Main application controller that manages page switching, shared state, and data sync."""

    def __init__(self):
        super().__init__()

        # ---------------- Window Settings ----------------
        self.title("PLC Data Collector")
        self.geometry("1400x900")
        ctk.set_appearance_mode("light")
        self.protocol("WM_DELETE_WINDOW", self.on_close)  # Handle window close safely

        # ---------------- Shared Data ----------------
        self.shared_data = {
            "dataframe": pd.DataFrame(),
            "excel_file": "PLC_Log.xlsx",
            "tags_to_monitor": [],
            "interval": 5,
            "ip": "192.168.1.10"
        }

        # Registered listener callbacks (e.g., MainPage, SetupPage)
        self.data_listeners = []

        # ---------------- Page Container ----------------
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (MainPage, SetupPage):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Start on the MainPage
        self.show_frame("MainPage")

    # ---------------- Frame Management ----------------
    def show_frame(self, page_name: str):
        """Raise a given frame by name."""
        frame = self.frames[page_name]
        frame.tkraise()
        if hasattr(frame, "on_show"):
            frame.on_show()

    # ---------------- Shared Data Sync ----------------
    def register_listener(self, listener_callback):
        """Register a page method to be notified when shared_data changes."""
        if listener_callback not in self.data_listeners:
            self.data_listeners.append(listener_callback)

    def notify_data_change(self):
        """Notify all registered pages that shared_data was updated."""
        for callback in self.data_listeners:
            try:
                callback(self.shared_data)
            except Exception as e:
                print(f"⚠️ Listener error: {e}")

    # ---------------- Graceful App Shutdown ----------------
    def on_close(self):
        """Stop logging, save data, and close safely."""
        print("🛑 Application shutting down...")

        # --- Call on_close for all pages ---
        for page_name, frame in self.frames.items():
            if hasattr(frame, "on_close") and callable(frame.on_close):
              try:
                frame.on_close()
              except Exception as e:
                print(f"Error during {page_name} cleanup: {e}")

        # --- Destroy all matplotlib canvases to cancel redraw timers ---
        try:
            import matplotlib.pyplot as plt
            plt.close("all")  # closes all active figures, cancels their redraws
        except Exception as e:
            print(f"⚠️ Error closing matplotlib figures: {e}")

        # --- Also cancel any Tk 'after' jobs at the root level ---
        try:
            self.after_cancel(self.after_id)
        except Exception:
            pass

        # --- Now continue with your popup save routine ---
        popup = tk.Toplevel(self)
        popup.title("Saving Data...")
        popup.geometry("300x100")
        popup.resizable(False, False)
        label = tk.Label(popup, text="Saving the most recent data...", font=("Arial", 12))
        label.pack(expand=True)
        popup.update()

        # Center popup
        x = self.winfo_x() + (self.winfo_width() // 2) - 150
        y = self.winfo_y() + (self.winfo_height() // 2) - 50
        popup.geometry(f"+{x}+{y}")

        # --- Save DataFrame to Excel ---
        saved = False
        try:
            df = self.shared_data.get("dataframe")
            save_path = self.shared_data.get("excel_file", "PLC_Log.xlsx")
            if isinstance(df, pd.DataFrame) and not df.empty:
                df.to_excel(save_path, index=False)
                saved = True
        except Exception as e:
            print(f"⚠️ Failed to save data on close: {e}")

        label.config(text=f"✅ Data saved to:\n{save_path}" if saved else "⚠️ Failed to save data!")

        # --- Close popup and main window safely ---
        def close_app():
            try:
                plt.close("all")  # redundant but safe double close
            except Exception:
                pass
            popup.destroy()
            self.destroy()

        popup.after(1500, close_app)

if __name__ == "__main__":
    app = AppController()
    app.mainloop()
