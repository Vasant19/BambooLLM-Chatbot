import os
import pandas as pd
import streamlit as st
import sqlite3
import matplotlib.pyplot as plt
import io
import base64
from pandasai import SmartDataframe, Agent

# Set the PandasAI API key
os.environ["PANDASAI_API_KEY"] = ""

# Function to load data from SQLite database
def load_data_from_sqlite(db_path, table_name):
    conn = sqlite3.connect(db_path)
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Function to ensure DataFrame column types are compatible with Arrow
def fix_column_types(df):
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                df[col] = pd.to_numeric(df[col])
            except ValueError:
                pass
    return df

# Function to generate a plot and return base64 encoded image
def generate_plot(plot_data, plot_type='line', x_col=None, y_col=None):
    plt.figure(figsize=(10, 5))
    
    if plot_type == 'bar':
        plot_data.plot(kind='bar', color='blue')
    elif plot_type == 'line':
        plot_data.plot(kind='line', x=x_col, y=y_col, color='blue')
    elif plot_type == 'scatter':
        plot_data.plot(kind='scatter', x=x_col, y=y_col, color='blue')
    
    plt.xlabel(x_col if x_col else 'X-axis')
    plt.ylabel(y_col if y_col else 'Y-axis')
    plt.title('Visualization based on query')
    plt.xticks(rotation=0)
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    buffer.close()
    
    return img_base64

# Main function to run the Streamlit web application
def main():
    st.title("IRCC Data Analysis")

    # Sidebar for SQLite database selection and CSV upload
    st.sidebar.title('Database and CSV Input')
    db_path = st.sidebar.text_input("Enter SQLite Database Path:", r'E:\SQLite Studio Databases\Db1.db')
    table_name = st.sidebar.text_input("Enter Table Name:")

    # CSV file uploader
    uploaded_file = st.sidebar.file_uploader("Upload a CSV file", type=["csv"])

    if db_path and table_name:
        try:
            with st.spinner("Loading data from SQLite..."):
                data_information = load_data_from_sqlite(db_path, table_name)
                data_information = fix_column_types(data_information)

            st.subheader("Loaded data from SQLite")
            st.write(data_information)
        except Exception as e:
            st.error(f"Error loading data from SQLite: {str(e)}")
            return
    elif uploaded_file is not None:
        try:
            data_information = pd.read_csv(uploaded_file)
            data_information = fix_column_types(data_information)
            st.subheader("Loaded data from CSV")
            st.write(data_information)
        except Exception as e:
            st.error(f"Error loading data from CSV: {str(e)}")
            return
    else:
        st.write("Please enter a valid SQLite database path or upload a CSV file.")
        return

    # Initialize pandasai agent with data_information
    agent = Agent(data_information)

    query = st.text_input("Enter your question about the data: ")

    if st.button("Ask"):
        with st.spinner("Analyzing..."):
            try:
                response = agent.chat(query)
                
                if isinstance(response, pd.DataFrame):
                    # Try to determine the type of plot and the columns involved
                    plot_type = 'line'  # Default plot type
                    x_col, y_col = response.columns[:2]
                    
                    st.subheader("Generated Plot")
                    st.line_chart(response.set_index(x_col)[y_col] if plot_type == 'line' else response)

                else:
                    st.subheader("Response")
                    st.write(response)

            except Exception as e:
                st.error(f"An error occurred during analysis: {str(e)}")

if __name__ == "__main__":
    main()
