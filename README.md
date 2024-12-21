# Path of Exile Server Latency Checker

A desktop application that helps Path of Exile players monitor and analyze latency to different game servers worldwide. The application provides real-time ping measurements, packet loss statistics, and a user-friendly interface for tracking server performance.

## Features

- Real-time latency monitoring for all Path of Exile game servers
- Multi-threaded ping testing for efficient server checks
- Sortable data grid showing:
  - Minimum latency
  - Average latency
  - Maximum latency
  - Packet loss percentage
  - Last check timestamp
- Detailed logging system
- Cross-platform support (Windows and Unix-based systems)
- User-friendly GUI with resizable interface
- Stop/Start functionality for server checks

## Technical Details

### Requirements

- Python 3.x
- tkinter (usually comes with Python)
- Standard Python libraries:
  - subprocess
  - threading
  - multiprocessing
  - concurrent.futures
  - statistics
  - datetime
  - platform
  - queue
  - re

### Architecture

The application follows an object-oriented design with the main `LatencyChecker` class handling:

- GUI creation and management
- Multi-threaded server ping operations
- Data collection and display
- Event handling and user interactions

### Performance Considerations

- Utilizes multi-threading for parallel server checks
- Automatically determines optimal thread count based on CPU cores
- Thread-safe logging implementation
- Efficient data updates using tkinter's event loop

## Usage

1. Run the application:
   ```bash
   python poe_latency.py
   ```

2. The main window will display a list of all available Path of Exile servers.

3. Click "Check All" to start monitoring server latencies.
   - The application will ping each server 8 times
   - Results are displayed in real-time
   - Data can be sorted by clicking column headers

4. Use the "Stop" button to interrupt the checking process if needed.

## Server Locations

The application monitors the following Path of Exile servers:

- North America: Texas, Washington DC, California
- Europe: Amsterdam, London, Frankfurt, Milan, Paris
- Asia: Singapore, Japan, South Korea, Hong Kong
- Oceania: Australia, New Zealand
- South America: São Paulo
- Russia: Moscow
- Africa: South Africa

## Implementation Details

### Threading Model

- Uses `ThreadPoolExecutor` for parallel server checks
- Main GUI runs in the primary thread
- Server checks run in separate threads to prevent GUI freezing
- Thread-safe queue for log message handling

### Error Handling

- Graceful handling of network timeouts and errors
- Clear error reporting in the log window
- Proper thread cleanup on application exit

### GUI Components

- Treeview for server data display
- Scrollable log window
- Control buttons for operation management
- Responsive layout with proper scaling

## Best Practices

- Thread-safe operations for all network and GUI interactions
- Proper resource cleanup
- Cross-platform compatibility considerations
- Efficient memory usage
- Clear separation of concerns (GUI, network operations, data management)