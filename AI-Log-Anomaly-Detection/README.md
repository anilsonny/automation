# AI-Based System Log Anomaly Detection

A Python-based demonstration of unsupervised log anomaly detection using
[scikit-learn](https://scikit-learn.org/) and the Isolation Forest algorithm.
The tool parses timestamped text logs, derives simple numerical features,
classifies entries as normal or anomalous, and exports a CSV report.

## Features

- Parses timestamp, severity level, and the complete log message.
- Skips malformed lines and reports how many were skipped.
- Maps common severity levels to numerical scores.
- Uses message length as a second feature.
- Applies Isolation Forest without requiring labelled training data.
- Allows the input file, output CSV path, and contamination setting to be configured.
- Exports anomalies only by default, or all classified entries with `--show-all`.
- Uses a fixed random seed for repeatable results on the same data and environment.

## How it works

1. Reads the input file as UTF-8 (invalid byte sequences are replaced).
2. Parses each line in the format shown below.
3. Converts severity to `level_score` and calculates `message_length`.
4. Fits an Isolation Forest model on those two features.
5. Labels each record `Normal` (`1`) or `Anomaly` (`-1`).
6. Writes the selected records to a CSV report.

### Features used by the model

| Feature | Description |
|---|---|
| `level_score` | Numeric severity score: DEBUG=0, INFO/NOTICE=1, WARNING/WARN=2, ERROR=3, CRITICAL/FATAL=4. Unknown levels receive 0. |
| `message_length` | Number of characters in the log message. |

**Important:** This is a lightweight demonstration, not a complete security analytics
or production incident detection system. The model does not understand the meaning
of a message. It identifies statistical outliers based only on severity and message
length. An anomalous entry is not necessarily an incident, and an incident may not
be flagged.

## Repository layout

```text
AI-Log-Anomaly-Detection/
├── log_anomaly_detection.py
├── README.md
├── requirements.txt
├── system_logs.txt
├── .gitignore
└── output/
    └── .gitkeep
```

## Requirements

- Python 3.9 or later
- pip

## Installation

Clone the repository and enter the project directory:

```bash
git clone https://github.com/<your-username>/AI-Log-Anomaly-Detection.git
cd AI-Log-Anomaly-Detection
```

(Optional) Create and activate a virtual environment:

```bash
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Input log format

Each valid line must use this format:

```text
YYYY-MM-DD HH:MM:SS LEVEL MESSAGE
```

Example:

```text
2026-11-16 09:00:00 INFO System started successfully
2026-11-16 09:05:00 INFO CPU utilization is normal
2026-11-16 09:10:00 WARNING Memory utilization is high
2026-11-16 09:15:00 ERROR Database connection failed
2026-11-16 09:20:00 CRITICAL Disk space is critically low
```

The timestamp format must be `YYYY-MM-DD HH:MM:SS`. The message may contain
spaces. Blank lines, malformed timestamps, and lines without all required
fields are skipped.

## Usage

Run with the default input (`system_logs.txt`) and default report
(`output/anomalies.csv`):

```bash
python log_anomaly_detection.py
```

Specify an input and output path:

```bash
python log_anomaly_detection.py \
  --input system_logs.txt \
  --output output/anomalies.csv
```

Set the expected anomaly proportion:

```bash
python log_anomaly_detection.py --contamination 0.05
```

Use the algorithm's automatic contamination setting:

```bash
python log_anomaly_detection.py --contamination auto
```

Export and display every classified log entry, not only anomalies:

```bash
python log_anomaly_detection.py --show-all
```

See all available options:

```bash
python log_anomaly_detection.py --help
```

### Command-line options

| Option | Default | Description |
|---|---|---|
| `-i`, `--input` | `system_logs.txt` | Input log file path |
| `-o`, `--output` | `output/anomalies.csv` | CSV report path |
| `-c`, `--contamination` | `0.1` | Expected anomaly proportion (`0 < value <= 0.5`) or `auto` |
| `--show-all` | Disabled | Display and export all classified entries |

## Output

By default, only records identified as anomalies are written to the CSV file.
The report contains:

- `timestamp`
- `level`
- `message`
- `level_score`
- `message_length`
- `source_line` (original line number in the input file)
- `anomaly_prediction` (`-1` for anomaly, `1` for normal)
- `classification` (`Anomaly` or `Normal`)

The output directory is created automatically when required. If no anomalies
are detected, the CSV is still created with its column headers.

## Understanding contamination

The `contamination` parameter tells Isolation Forest the expected proportion
of outliers in the dataset. For example, `0.1` represents an expected 10%.
It is a model setting, not a measured anomaly rate or a guarantee of accuracy.
Choose it based on the dataset and validate results against operational context.
The value `auto` delegates the threshold choice to scikit-learn's implementation.

## Limitations and possible enhancements

Current limitations:

- Only severity score and message length are used as model features.
- The model does not parse semantic meaning, event IDs, host names, or processes.
- The current implementation trains on the input file being analyzed; it does
  not maintain a historical baseline.
- Results depend on the dataset and contamination setting.
- Small or repetitive datasets may produce unhelpful classifications.

Possible future enhancements:

- Add event frequency and time-window aggregation features.
- Detect repeated failures and unusual sequences of events.
- Extract host, service, process, and event identifiers.
- Add message-template parsing and text-based features.
- Compare current logs against a historical baseline.
- Integrate with Azure Monitor / Log Analytics, ELK, or Grafana.
- Add alerting and scheduled execution.

## Exit behaviour

The script exits with status code `0` when processing completes successfully.
It returns a non-zero status for missing/unreadable input, no valid entries,
insufficient records, invalid configuration, or report-writing errors.

## License

This project is provided under the MIT License. Add a `LICENSE` file with
the standard MIT License text and your chosen copyright holder before
publishing it as an MIT-licensed repository.
