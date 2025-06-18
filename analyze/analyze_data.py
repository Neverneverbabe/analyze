import pandas as pd
import os
import json
import asyncio # Required for running async functions
import requests # Required for making HTTP requests to LM Studio

# --- Configuration ---
# FILE_PATH will now be passed by the web server (app.py)
# CHUNK_SIZE can remain a constant or be made configurable via the web UI if desired.
CHUNK_SIZE = 10000  # Number of rows to process at a time
# OUTPUT_ANALYSIS_FILE will now be passed by the web server (app.py)

# --- 1. Simulate a Large Data File ---
def create_dummy_large_csv(file_path, num_rows=100000):
    """
    Creates a dummy large CSV file for testing purposes.
    This simulates having a large file that needs to be processed in chunks.
    This function is primarily for initial setup/testing without manual uploads.
    """
    print(f"Creating a dummy CSV file with {num_rows} rows at {file_path}...")
    data = {
        'id': range(num_rows),
        'value1': [i * 0.5 for i in range(num_rows)],
        'category': [f'cat_{(i % 5)}' for i in range(num_rows)],
        'description': [f'This is a description for item {i}. It might contain some keywords.' for i in range(num_rows)]
    }
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    print("Dummy CSV created successfully.")

# --- 2. LLM Interaction (LM Studio Integration) ---
async def call_local_llm_for_analysis(prompt_text):
    """
    This function calls a local LLM (like one hosted by LM Studio) using the
    'requests' library to interact with its OpenAI-compatible API.

    Ensure LM Studio is running and serving a model at the specified URL.
    """
    print(f"\n--- Calling LLM with prompt (first 200 chars): ---\n{prompt_text[:200]}...")
    
    # --- IMPORTANT: Ensure LM Studio is running and serving a model ---
    # You need to have 'requests' installed: pip install requests
    try:
        lm_studio_api_url = "http://localhost:1234/v1/chat/completions" # Adjust port if different
        response = requests.post(lm_studio_api_url, json={
            "messages": [{"role": "user", "content": prompt_text}],
            "temperature": 0.7, # Adjust temperature for creativity (0.0 for deterministic)
            "max_tokens": 500,   # Adjust max tokens for response length
            "stream": False      # Streaming is not needed for this synchronous call
        })
        if response.status_code == 200:
            # Extract the content from the LLM's response
            return response.json()['choices'][0]['message']['content']
        else:
            print(f"Error calling LM Studio: HTTP Status {response.status_code} - {response.text}")
            return f"Error: Could not get response from local LLM (Status: {response.status_code})."
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to LM Studio. Is the server running at http://localhost:1234?")
        return "Error: LM Studio not running or accessible. Please start LM Studio server."
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON response from LM Studio. Response: {response.text}")
        return "Error: Invalid JSON response from LM Studio."
    except Exception as e:
        print(f"An unexpected error occurred during LM Studio API call: {e}")
        return f"Error: Failed to get response from LM Studio - {e}"


# --- 3. Main Analysis Pipeline ---
async def analyze_large_file(file_path, chunk_size, output_file):
    """
    Processes a large file chunk by chunk, performs a simple analysis,
    and then sends the summary of each chunk to the LLM for deeper insights.
    """
    total_chunks_processed = 0
    all_analysis_results = []
    global_summary = {
        'total_rows_processed': 0,
        'sum_value1': 0,
        'category_counts': {}
    }

    print(f"Starting analysis of '{file_path}' with chunk size {chunk_size}...")

    # Using an iterator for pd.read_csv to handle large files
    try:
        # Determine file type and use appropriate Pandas reader
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension == '.csv':
            reader = pd.read_csv(file_path, chunksize=chunk_size)
        elif file_extension == '.xlsx':
            reader = pd.read_excel(file_path, chunksize=chunk_size)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}. Only .csv and .xlsx are supported.")

        for chunk_df in reader:
            total_chunks_processed += 1
            global_summary['total_rows_processed'] += len(chunk_df)

            print(f"\nProcessing chunk {total_chunks_processed} (rows {global_summary['total_rows_processed'] - len(chunk_df) + 1} to {global_summary['total_rows_processed']})...")

            # --- Basic Pandas Analysis on the Chunk ---
            # Ensure 'value1' and 'category' columns exist, handle missing if necessary
            # This makes the script more robust to different CSV/XLSX structures.
            avg_value1_chunk = chunk_df['value1'].mean() if 'value1' in chunk_df.columns else 0
            global_summary['sum_value1'] += chunk_df['value1'].sum() if 'value1' in chunk_df.columns else 0

            category_counts_chunk = {}
            if 'category' in chunk_df.columns:
                category_counts_chunk = chunk_df['category'].value_counts().to_dict()
                for cat, count in category_counts_chunk.items():
                    global_summary['category_counts'][cat] = global_summary['category_counts'].get(cat, 0) + count
            
            high_value_rows = pd.DataFrame() # Initialize as empty DataFrame
            num_high_value_rows = 0
            if 'value1' in chunk_df.columns:
                high_value_rows = chunk_df[chunk_df['value1'] > 40000]
                num_high_value_rows = len(high_value_rows)

            chunk_summary_text = (
                f"Chunk Summary (Chunk {total_chunks_processed}):\n"
                f"  - Rows in chunk: {len(chunk_df)}\n"
                f"  - Average 'value1': {avg_value1_chunk:.2f} (if 'value1' column exists)\n"
                f"  - Category counts: {category_counts_chunk} (if 'category' column exists)\n"
                f"  - Number of rows with 'value1' > 40000: {num_high_value_rows} (if 'value1' column exists)\n"
            )

            print(chunk_summary_text)

            # --- Prepare Prompt for LLM and Call LLM ---
            llm_prompt = (
                f"Analyze the following data chunk summary and provide insights, "
                f"potential anomalies, or interesting patterns. Consider the overall "
                f"data context if available (e.g., 'This data is sales transactions').\n\n"
                f"Chunk Data (first 5 rows as JSON for context):\n"
                f"{chunk_df.head(5).to_json(orient='records', lines=True, date_format='iso')}\n\n"
                f"Chunk Summary:\n{chunk_summary_text}\n"
                f"Specific high-value rows (if any, first 3 as JSON):\n"
                f"{high_value_rows.head(3).to_json(orient='records', lines=True) if not high_value_rows.empty else 'None'}\n\n"
                f"What are the key takeaways from this chunk regarding trends, outliers, or anything noteworthy?"
            )

            llm_response = await call_local_llm_for_analysis(llm_prompt)
            print(f"\nLLM Response for Chunk {total_chunks_processed}:\n{llm_response}\n{'='*80}")
            all_analysis_results.append({
                'chunk_id': total_chunks_processed,
                'chunk_summary': chunk_summary_text,
                'llm_analysis': llm_response
            })

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found. Please ensure it exists.")
        raise # Re-raise to be caught by the Flask app
    except pd.errors.EmptyDataError:
        print(f"Error: The file '{file_path}' is empty or contains no data.")
        raise # Re-raise to be caught by the Flask app
    except Exception as e:
        print(f"An unexpected error occurred during file processing in analyze_large_file: {e}")
        raise # Re-raise to be caught by the Flask app

    # --- Final Global Analysis and Reporting ---
    print("\n--- Final Global Summary Across All Chunks ---")
    print(f"Total rows processed: {global_summary['total_rows_processed']}")
    print(f"Overall sum of 'value1': {global_summary['sum_value1']:.2f}")
    print(f"Overall category counts: {global_summary['category_counts']}")

    final_llm_prompt = (
        f"Based on the following global summary of a large dataset and individual chunk analyses, "
        f"provide a comprehensive overview, highlight overarching trends, and identify any "
        f"significant anomalies or insights that span across the entire dataset. "
        f"The data represents a collection of transactions/records.\n\n"
        f"Global Summary:\n"
        f"- Total rows processed: {global_summary['total_rows_processed']}\n"
        f"- Overall sum of 'value1': {global_summary['sum_value1']:.2f}\n"
        f"- Overall category counts: {global_summary['category_counts']}\n\n"
        f"Individual Chunk Analyses (Summaries):\n"
    )
    # Only include LLM analysis results, not full chunk summaries to keep the final prompt manageable
    for result in all_analysis_results:
        final_llm_prompt += f"--- Chunk {result['chunk_id']} LLM Analysis ---\n{result['llm_analysis']}\n\n"

    final_llm_prompt += "What are the most important conclusions and actionable insights from this entire dataset?"

    final_llm_response = await call_local_llm_for_analysis(final_llm_prompt)
    print("\n--- Comprehensive LLM Analysis of Entire Dataset ---")
    print(final_llm_response)

    # Save all analysis results to a file
    with open(output_file, 'w') as f:
        f.write("--- Large File Analysis Results ---\n\n")
        f.write(f"File Processed: {file_path}\n")
        f.write(f"Chunk Size: {chunk_size}\n\n")
        f.write("--- Global Data Summary ---\n")
        json.dump(global_summary, f, indent=4)
        f.write("\n\n")
        f.write("--- Detailed Chunk-by-Chunk LLM Analysis ---\n")
        for result in all_analysis_results:
            f.write(f"\nChunk {result['chunk_id']}:\n")
            f.write(f"  Summary:\n{result['chunk_summary']}")
            f.write(f"  LLM Insights:\n{result['llm_analysis']}\n")
        f.write("\n--- Final Comprehensive LLM Analysis ---\n")
        f.write(final_llm_response)

    print(f"\nAnalysis complete. Results saved to '{output_file}'")

# This __name__ == "__main__" block is for when analyze_data.py is run directly,
# but in this setup, it's primarily imported by app.py.
# The create_dummy_large_csv is called from app.py's main block.
if __name__ == "__main__":
    # If you run analyze_data.py directly, it will still try to create a dummy file and analyze it.
    # This is useful for standalone testing of the analysis logic.
    DUMMY_FILE_PATH = 'dummy_standalone_data.csv'
    if not os.path.exists(DUMMY_FILE_PATH):
        create_dummy_large_csv(DUMMY_FILE_PATH)
    asyncio.run(analyze_large_file(DUMMY_FILE_PATH, CHUNK_SIZE, 'standalone_analysis_results.txt'))
