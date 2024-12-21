import tkinter as tk
from tkinter import ttk
import subprocess
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
import re
import platform
from datetime import datetime
import statistics
import queue

class LatencyChecker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Path of Exile Server Latency Checker")
        self.root.geometry("1200x800")
        
        # Get optimal thread count (leaving one core free for UI)
        self.thread_count = max(1, multiprocessing.cpu_count() - 1)
        
        # Thread-safe queue for logging
        self.log_queue = queue.Queue()
        
        # Server data - Combined name and region into location
        self.servers = [
            {"location": "Texas (US)", "host": "us.speedtest.pathofexile.com"},
            {"location": "Amsterdam (EU)", "host": "eu.speedtest.pathofexile.com"},
            {"location": "Singapore", "host": "sg.speedtest.pathofexile.com"},
            {"location": "Australia", "host": "au.speedtest.pathofexile.com"},
            {"location": "London (EU)", "host": "lon.speedtest.pathofexile.com"},
            {"location": "Frankfurt (EU)", "host": "fra.speedtest.pathofexile.com"},
            {"location": "Washington DC (US)", "host": "wdc.speedtest.pathofexile.com"},
            {"location": "California (US)", "host": "sjc.speedtest.pathofexile.com"},
            {"location": "Milan (EU)", "host": "mil.speedtest.pathofexile.com"},
            {"location": "São Paulo (BR)", "host": "br.speedtest.pathofexile.com"},
            {"location": "Paris (EU)", "host": "par.speedtest.pathofexile.com"},
            {"location": "Moscow (RU)", "host": "mo.speedtest.pathofexile.com"},
            {"location": "Auckland (NZ)", "host": "nz.speedtest.pathofexile.com"},
            {"location": "Japan", "host": "jp.speedtest.pathofexile.com"},
            {"location": "Seoul (KR)", "host": "kr.speedtest.pathofexile.com"},
            {"location": "Toronto (CA)", "host": "tor.speedtest.pathofexile.com"},
            {"location": "South Africa", "host": "zaf-m.speedtest.pathofexile.com"},
            {"location": "Hong Kong", "host": "hkg.speedtest.pathofexile.com"}
        ]
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=3)
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Create and configure table
        self.create_table()
        
        # Create log box
        self.create_log_box()
        
        # Create control buttons
        self.create_controls()
        
        # Initialize status variables
        self.is_checking = False
        self.stop_flag = False
        
        # Start log queue processing
        self.process_log_queue()

    def create_table(self):
        columns = ('location', 'host', 'min', 'avg', 'max', 'loss', 'last_check')
        self.tree = ttk.Treeview(self.main_frame, columns=columns, show='headings')
        
        # Configure headers
        self.tree.heading('location', text='Location')
        self.tree.heading('host', text='Host')
        self.tree.heading('min', text='Min (ms)')
        self.tree.heading('avg', text='Avg (ms)')
        self.tree.heading('max', text='Max (ms)')
        self.tree.heading('loss', text='Packet Loss')
        self.tree.heading('last_check', text='Last Check')
        
        # Configure column widths
        self.tree.column('location', width=180)  # Wider for combined location info
        self.tree.column('host', width=250)
        self.tree.column('min', width=80)
        self.tree.column('avg', width=80)
        self.tree.column('max', width=80)
        self.tree.column('loss', width=100)
        self.tree.column('last_check', width=150)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid table and scrollbar
        self.tree.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=4, sticky=(tk.N, tk.S))
        
        # Insert server data
        for server in self.servers:
            self.tree.insert('', tk.END, values=(
                server['location'],
                server['host'],
                '-', '-', '-', '-', 'Not checked'
            ))

    def create_log_box(self):
        log_frame = ttk.LabelFrame(self.main_frame, text="Log", padding="5")
        log_frame.grid(row=2, column=0, columnspan=5, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        
        self.log_text.configure(state=tk.DISABLED)

    def process_log_queue(self):
        """Process logs from the queue and update the log box"""
        while True:
            try:
                message = self.log_queue.get_nowait()
                self._append_to_log(message)
            except queue.Empty:
                break
        
        # Schedule next queue check
        self.root.after(100, self.process_log_queue)

    def log_message(self, message):
        """Thread-safe logging"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        self.log_queue.put(log_entry)

    def _append_to_log(self, message):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def create_controls(self):
        control_frame = ttk.Frame(self.main_frame, padding="5")
        control_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E))
        
        self.check_button = ttk.Button(control_frame, text="Check All", command=self.start_checking)
        self.check_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="Stop", command=self.stop_checking, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5)
        
        # Add thread count label
        thread_label = ttk.Label(control_frame, text=f"Using {self.thread_count} threads")
        thread_label.grid(row=0, column=2, padx=5)

    def ping_server(self, server_data):
        """Ping a server and return results (thread-safe)"""
        host = server_data['host']
        location = server_data['location']
        
        try:
            self.log_message(f"Starting ping test for {location} ({host})")
            
            if platform.system().lower() == "windows":
                cmd = ["ping", "-n", "8", host]
            else:
                cmd = ["ping", "-c", "8", host]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if platform.system().lower() == "windows":
                times = re.findall(r"time[=<](\d+)ms", result.stdout)
                times = [int(t) for t in times]
                loss_match = re.search(r"\((\d+)% loss\)", result.stdout)
                loss_percentage = loss_match.group(1) if loss_match else "100"
            else:
                times = re.findall(r"time=(\d+\.\d+)", result.stdout)
                times = [float(t) for t in times]
                loss_match = re.search(r"(\d+)% packet loss", result.stdout)
                loss_percentage = loss_match.group(1) if loss_match else "100"
            
            if times:
                result_data = {
                    'min': min(times),
                    'avg': statistics.mean(times),
                    'max': max(times),
                    'loss': f"{loss_percentage}%"
                }
                self.log_message(
                    f"Completed ping test for {location}: "
                    f"min={result_data['min']}ms, "
                    f"avg={result_data['avg']:.1f}ms, "
                    f"max={result_data['max']}ms, "
                    f"loss={result_data['loss']}"
                )
                return location, result_data
            else:
                self.log_message(f"No response from {location} ({host})")
                return location, {'min': '-', 'avg': '-', 'max': '-', 'loss': '100%'}
                
        except Exception as e:
            error_msg = f"Error pinging {location} ({host}): {str(e)}"
            self.log_message(error_msg)
            return location, {'min': '-', 'avg': '-', 'max': '-', 'loss': 'Error'}

    def update_server_status(self, location, results):
        """Update server status in the table (thread-safe)"""
        for item in self.tree.get_children():
            if self.tree.set(item, 'location') == location:
                self.tree.set(item, 'min', results['min'])
                self.tree.set(item, 'avg', results['avg'])
                self.tree.set(item, 'max', results['max'])
                self.tree.set(item, 'loss', results['loss'])
                self.tree.set(item, 'last_check', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                break

    def check_servers_parallel(self):
        """Check all servers using thread pool"""
        self.log_message(f"Starting parallel server checks using {self.thread_count} threads...")
        
        with ThreadPoolExecutor(max_workers=self.thread_count) as executor:
            futures = []
            
            # Submit all servers to thread pool
            for server in self.servers:
                if self.stop_flag:
                    break
                futures.append(executor.submit(self.ping_server, server))
            
            # Process results as they complete
            for future in futures:
                if self.stop_flag:
                    break
                try:
                    location, results = future.result()
                    self.root.after(0, self.update_server_status, location, results)
                except Exception as e:
                    self.log_message(f"Error processing server result: {str(e)}")
        
        if not self.stop_flag:
            self.log_message("All server checks completed")
        
        self.is_checking = False
        self.root.after(0, self.update_button_states)

    def start_checking(self):
        if not self.is_checking:
            self.is_checking = True
            self.stop_flag = False
            self.update_button_states()
            
            # Start checking in a separate thread
            thread = threading.Thread(target=self.check_servers_parallel)
            thread.daemon = True
            thread.start()

    def stop_checking(self):
        self.stop_flag = True
        self.is_checking = False
        self.update_button_states()
        self.log_message("Stopping server checks...")

    def update_button_states(self):
        if self.is_checking:
            self.check_button.configure(state=tk.DISABLED)
            self.stop_button.configure(state=tk.NORMAL)
        else:
            self.check_button.configure(state=tk.NORMAL)
            self.stop_button.configure(state=tk.DISABLED)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = LatencyChecker()
    app.run()