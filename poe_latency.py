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
        
        # Set minimum window size
        self.root.minsize(800, 600)
        
        # Set default window size
        self.root.geometry("1200x800")
        
        # Configure window scaling
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
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
        columns = ('location', 'host', 'progress', 'min', 'avg', 'max', 'loss', 'last_check')
        self.tree = ttk.Treeview(self.main_frame, columns=columns, show='headings')
        
        # Initialize sort direction dictionary
        self.sort_direction = {col: True for col in columns}  # True for ascending
        
        # Configure headers with sorting
        self.tree.heading('location', text='Location', command=lambda: self.sort_column('location'))
        self.tree.heading('host', text='Host', command=lambda: self.sort_column('host'))
        self.tree.heading('progress', text='Progress', command=lambda: self.sort_column('progress'))
        self.tree.heading('min', text='Min (ms)', command=lambda: self.sort_column('min'))
        self.tree.heading('avg', text='Avg (ms)', command=lambda: self.sort_column('avg'))
        self.tree.heading('max', text='Max (ms)', command=lambda: self.sort_column('max'))
        self.tree.heading('loss', text='Packet Loss', command=lambda: self.sort_column('loss'))
        self.tree.heading('last_check', text='Last Check', command=lambda: self.sort_column('last_check'))
        
        # Configure column widths and behavior
        self.tree.column('location', width=180, minwidth=120, stretch=True)  # Expandable
        self.tree.column('host', width=250, minwidth=180, stretch=True)     # Expandable
        self.tree.column('progress', width=80, minwidth=80, stretch=False)  # Fixed
        self.tree.column('min', width=80, minwidth=60, stretch=False)       # Fixed
        self.tree.column('avg', width=80, minwidth=60, stretch=False)       # Fixed
        self.tree.column('max', width=80, minwidth=60, stretch=False)       # Fixed
        self.tree.column('loss', width=100, minwidth=80, stretch=False)     # Fixed
        self.tree.column('last_check', width=150, minwidth=120, stretch=True)  # Expandable
        
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
                '-',  # progress
                '-', '-', '-', '-', 'Not checked'
            ))

    def create_log_box(self):
        # Create log frame with better padding
        log_frame = ttk.LabelFrame(self.main_frame, text="Log", padding="8")
        log_frame.grid(row=2, column=0, columnspan=5, sticky=(tk.W, tk.E, tk.N, tk.S), pady=8)
        
        # Create horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(log_frame, orient=tk.HORIZONTAL)
        v_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL)
        
        # Configure text widget with both scrollbars and word wrap
        self.log_text = tk.Text(
            log_frame,
            height=8,  # Minimum height in lines
            wrap=tk.NONE,  # Allow horizontal scrolling
            xscrollcommand=h_scrollbar.set,
            yscrollcommand=v_scrollbar.set
        )
        
        # Configure scrollbar commands
        h_scrollbar.configure(command=self.log_text.xview)
        v_scrollbar.configure(command=self.log_text.yview)
        
        # Grid layout with proper weights and sticky
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Configure grid weights for proper resizing
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        
        # Set initial state
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
        
        # Create ping count spinbox
        ping_frame = ttk.Frame(control_frame)
        ping_frame.grid(row=0, column=0, padx=5)
        
        ping_label = ttk.Label(ping_frame, text="Pings:")
        ping_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.ping_count = tk.StringVar(value="8")  # Default 8 pings
        self.ping_spinbox = ttk.Spinbox(
            ping_frame,
            from_=4,
            to=50,
            width=3,
            textvariable=self.ping_count,
            validate="key",
            validatecommand=(self.root.register(self.validate_ping_count), '%P')
        )
        self.ping_spinbox.pack(side=tk.LEFT)
        
        self.check_button = ttk.Button(control_frame, text="Check All", command=self.start_checking)
        self.check_button.grid(row=0, column=1, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="Stop", command=self.stop_checking, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=2, padx=5)
        
        # Add thread count label
        thread_label = ttk.Label(control_frame, text=f"Using {self.thread_count} threads")
        thread_label.grid(row=0, column=3, padx=5)

    def validate_ping_count(self, value):
        """Validate the ping count input (4-50)"""
        if value == "":
            return True
        try:
            count = int(value)
            return 4 <= count <= 50
        except ValueError:
            return False

    def ping_server(self, server_data):
        """Ping a server and return results (thread-safe)"""
        host = server_data['host']
        location = server_data['location']
        
        try:
            ping_count = int(self.ping_count.get())
            self.log_message(f"Starting ping test for {location} ({host}) with {ping_count} pings")
            
            times = []
            current_ping = 0
            
            # Initialize progress
            self.root.after(0, self.update_server_status, location, {
                'min': '-', 'avg': '-', 'max': '-', 'loss': '-',
                'progress': f"0/{ping_count}"
            })
            
            # Run individual pings
            while current_ping < ping_count and not self.stop_flag:
                if platform.system().lower() == "windows":
                    cmd = ["ping", "-n", "1", host]
                else:
                    cmd = ["ping", "-c", "1", host]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                current_ping += 1
                
                # Extract time from single ping
                if platform.system().lower() == "windows":
                    time_match = re.search(r"time[=<](\d+)ms", result.stdout)
                else:
                    time_match = re.search(r"time=(\d+\.\d+)", result.stdout)
                
                if time_match:
                    ping_time = float(time_match.group(1))
                    times.append(ping_time)
                    
                    # Calculate current statistics
                    current_stats = {
                        'min': min(times),
                        'avg': statistics.mean(times),
                        'max': max(times),
                        'loss': f"{((current_ping - len(times)) / current_ping * 100):.0f}%",
                        'progress': f"{current_ping}/{ping_count}"
                    }
                    
                    # Update UI with current progress
                    self.root.after(0, self.update_server_status, location, current_stats)
                else:
                    # Update progress even for failed pings
                    current_stats = {
                        'min': min(times) if times else '-',
                        'avg': statistics.mean(times) if times else '-',
                        'max': max(times) if times else '-',
                        'loss': f"{((current_ping - len(times)) / current_ping * 100):.0f}%",
                        'progress': f"{current_ping}/{ping_count}"
                    }
                    self.root.after(0, self.update_server_status, location, current_stats)
            
            # Final results
            if times:
                result_data = {
                    'min': min(times),
                    'avg': statistics.mean(times),
                    'max': max(times),
                    'loss': f"{((ping_count - len(times)) / ping_count * 100):.0f}%",
                    'progress': f"{current_ping}/{ping_count}"
                }
                self.log_message(
                    f"Completed ping test for {location}: "
                    f"min={result_data['min']:.1f}ms, "
                    f"avg={result_data['avg']:.1f}ms, "
                    f"max={result_data['max']:.1f}ms, "
                    f"loss={result_data['loss']}"
                )
                return location, result_data
            else:
                result_data = {
                    'min': '-', 'avg': '-', 'max': '-', 'loss': '100%',
                    'progress': f"{current_ping}/{ping_count}"
                }
                self.log_message(f"No response from {location} ({host})")
                return location, result_data
                
        except Exception as e:
            error_msg = f"Error pinging {location} ({host}): {str(e)}"
            self.log_message(error_msg)
            return location, {'min': '-', 'avg': '-', 'max': '-', 'loss': 'Error'}

    def update_server_status(self, location, results):
        """Update server status in the table (thread-safe)"""
        for item in self.tree.get_children():
            if self.tree.set(item, 'location') == location:
                # Format latency values as integers
                min_val = round(results['min']) if isinstance(results['min'], (int, float)) else results['min']
                avg_val = round(results['avg']) if isinstance(results['avg'], (int, float)) else results['avg']
                max_val = round(results['max']) if isinstance(results['max'], (int, float)) else results['max']
                
                # Update progress first
                if 'progress' in results:
                    self.tree.set(item, 'progress', results['progress'])
                
                self.tree.set(item, 'min', min_val)
                self.tree.set(item, 'avg', avg_val)
                self.tree.set(item, 'max', max_val)
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

    def sort_column(self, column):
        """Sort tree contents when a column header is clicked."""
        # Get all items
        items = [(self.tree.set(item, column), item) for item in self.tree.get_children('')]
        
        # Determine sort order
        reverse = not self.sort_direction[column]
        self.sort_direction[column] = reverse
        
        def convert_value(value):
            """Convert string values to appropriate types for sorting"""
            if value == '-':
                return float('-inf')
            # Handle already numeric values
            if isinstance(value, (int, float)):
                return float(value)
            # Handle string values
            if isinstance(value, str):
                # Remove 'ms' and '%' suffixes and try to convert to float
                try:
                    return float(value.rstrip('ms%'))
                except ValueError:
                    # If conversion fails, return original string for lexicographical sorting
                    return value
            return value
        
        # Sort items
        items.sort(key=lambda x: convert_value(x[0]), reverse=reverse)
        
        # Rearrange items in sorted order
        for index, (_, item) in enumerate(items):
            self.tree.move(item, '', index)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = LatencyChecker()
    app.run()