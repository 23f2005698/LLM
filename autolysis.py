import os
import sys
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import requests

# Get the AIPROXY_TOKEN (JWT) from environment variables
AIPROXY_TOKEN = os.environ.get("AIPROXY_TOKEN")
if not AIPROXY_TOKEN:
    print("Error: AIPROXY_TOKEN environment variable not set.")
    sys.exit(1)

# Set the AI Proxy URL for requests
openai_api_base = "https://aiproxy.sanand.workers.dev/openai"  # Ensure no trailing slash

# Set the Authorization header using the JWT token
headers = {
    "Authorization": f"Bearer {AIPROXY_TOKEN}"
}

# Analyze the dataset
def analyze_data(data):
    # Basic stats
    summary = data.describe(include='all').transpose()
    missing_values = data.isnull().sum()

    # Filter numeric columns for correlation
    numeric_data = data.select_dtypes(include=['number'])
    correlation = None
    if not numeric_data.empty:
        correlation = numeric_data.corr()

    return summary, missing_values, correlation

# Visualize the data
def create_visualizations(data):
    # Filter out non-numeric columns
    numeric_data = data.select_dtypes(include=['number'])
    
    # Check if there are more than one numeric column
    if numeric_data.shape[1] > 1:
        # Calculate and plot the correlation matrix
        correlation = numeric_data.corr()
        sns.heatmap(correlation, annot=True, cmap='coolwarm')
        plt.title("Correlation Matrix")
        plt.savefig("correlation_matrix.png")
        plt.close()

# Query GPT-4o-Mini via AI Proxy (new structure for OpenAI 1.0.0+)
def query_llm(prompt):
    try:
        # Send request to AI Proxy chat completions endpoint
        response = requests.post(
            f"{openai_api_base}/v1/chat/completions",  # Correct endpoint without double slash
            headers=headers,
            json={
                "model": "gpt-4o-mini",  # Use the correct model
                "messages": [{"role": "system", "content": "You are a data analysis assistant."},
                             {"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.7,
                "n": 1
            }
        )

        # Check if the request was successful
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
        else:
            print(f"Error querying the LLM: {response.status_code} - {response.text}")
            sys.exit(1)

    except Exception as e:
        print(f"Error querying the LLM: {e}")
        sys.exit(1)

# Narrate the story
def narrate_story(data, summary, missing_values, insights):
    with open("README.md", "w") as f:
        f.write("# Automated Analysis\n\n")
        f.write("## Dataset Overview\n")
        f.write(summary.to_markdown())
        f.write("\n\n## Missing Values\n")
        f.write(missing_values.to_markdown())
        f.write("\n\n## Insights\n")
        f.write(insights)
        f.write("\n\n## Visualizations\n")
        f.write("![Correlation Matrix](correlation_matrix.png)")

# Main function
# Main function
def main():
    if len(sys.argv) != 2:
        print("Usage: python autolysis.py <dataset.csv>")
        sys.exit(1)

    csv_file = sys.argv[1]

    # Try reading the CSV file with different encodings
    encodings = ['ISO-8859-1', 'latin1', 'utf-16', 'windows-1252']

    for encoding in encodings:
        try:
            # Attempt to read the CSV file with the current encoding
            data = pd.read_csv(csv_file, encoding=encoding)
            # print(f"Successfully read the file with encoding {encoding}")
            break  # Exit loop once the file is read successfully
        except UnicodeDecodeError:
            print(f"Failed to read the file with encoding {encoding}")
        except Exception as e:
            print(f"Error reading {csv_file} with encoding {encoding}: {e}")
            sys.exit(1)

    # After successfully reading the file, proceed with the rest of the script
    # Analyze data
    summary, missing_values, correlation = analyze_data(data)

    # Generate insights
    prompt = f"Here is a summary of the dataset:\n{summary.to_string()}\n\n"
    prompt += f"Here are the missing values:\n{missing_values.to_string()}\n\n"
    insights = query_llm(prompt)

    # Visualize data
    create_visualizations(data)

    # Narrate the story
    narrate_story(data, summary, missing_values, insights)

if __name__ == "__main__":
    main()
