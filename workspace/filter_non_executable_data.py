# -*- coding: utf-8 -*-
import json
import argparse
import os


def filter_error_versions(input_file, output_file):
    """
    Filter error versions to keep only those with traceback information.
    
    Args:
        input_file: Path to input JSONL file
        output_file: Path to output filtered JSONL file
    """
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        count = 0
        processed = 0
        
        for idx, line in enumerate(infile):
            # Parse JSON data
            data = json.loads(line)
            processed += 1
            
            # Filter error_versions containing traceback information
            filtered_error_versions = [
                error_version for error_version in data.get('error_versions', [])
                if "Traceback (most recent call last):" in error_version.get('execution_output', '')
            ]
            
            # If there are valid error versions, save to the new JSON
            if filtered_error_versions:
                # Keep other data unchanged, only replace error_versions
                data['error_versions'] = filtered_error_versions
                count += len(filtered_error_versions)
                # Write to output file
                outfile.write(json.dumps(data, ensure_ascii=False) + '\n')
        
        print(f"Processed {processed} entries, found {count} valid error versions.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Filter error versions with valid traceback information')
    parser.add_argument('--input', default='workspace/sklearn_pandas_errors/monitored_errors.jsonl',
                      help='Path to input JSONL file')
    parser.add_argument('--output', default='workspace/sklearn_pandas_errors/filtered_errors.jsonl',
                      help='Path to output filtered JSONL file')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Execute filtering
    filter_error_versions(args.input, args.output)
    print(f"Filtered data saved to {args.output}")
