# Local Large File Analyzer with LM Studio

This small Flask application lets you analyze large CSV or Excel files (100MB–300MB or larger) offline by chunking them with **pandas** and sending summaries to a local language model served by **LM Studio**.

## Requirements

- Python 3.8+
- LM Studio running locally with an API server (default `http://localhost:1234`)
- See `requirements.txt` for Python packages

## Setup

1. **Clone the repository**

   ```bash
   git clone <repo-url>
   cd analyze
   ```

2. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Install and start LM Studio**

   - Download from [https://lmstudio.ai](https://lmstudio.ai) (free).
   - Open LM Studio, download a model such as **LLaMA&nbsp;3 8B Instruct** or **Mistral&nbsp;7B Instruct**.
   - In the **Developer** tab enable the API server (default port `1234`).

4. **Run the Flask application**

   ```bash
   python analyze/app.py
   ```

   The server starts on `http://localhost:5000`.

5. **Upload a file for analysis**

   - Open `http://localhost:5000` in your browser.
   - Upload a `.csv` or `.xlsx` file (up to ~1&nbsp;GB).
   - The app processes the file in chunks (10&nbsp;000 rows by default) and sends each chunk summary to the local LLM.
   - Results are written to `uploads/analysis_results_<filename>.txt`.

## Customization

- Adjust the chunk size or prompts in `analyze/analyze_data.py`.
- Modify the upload page template under `analyze/templates/` if desired.
- Ensure LM Studio remains running while the analysis executes.

## License

This project is provided as-is under the MIT license.
