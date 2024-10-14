import streamlit as st
from streamlit_tags import st_tags_sidebar
import pandas as pd
import json
from datetime import datetime
from scraper import fetch_html_selenium, save_raw_data, format_data, save_formatted_data, html_to_markdown_with_readability, create_dynamic_listing_model, create_listings_container_model

# Initialize Streamlit app
st.set_page_config(page_title="Multi-Page AI Web Scraper")
st.title("Multi-Page AI Web Scraper")

# Sidebar components
st.sidebar.title("Web Scraper Settings")
model_selection = st.sidebar.selectbox("Select Model", options=["groq-llama3"], index=0)

# Multiple URL input
urls_input = st.sidebar.text_area("Enter URLs (one per line)")
urls = [url.strip() for url in urls_input.split('\n') if url.strip()]

# Tags input specifically in the sidebar
tags = st.sidebar.empty()
tags = st_tags_sidebar(
    label='Enter Fields to Extract:',
    text='Press enter to add a tag',
    value=[],
    suggestions=[],
    maxtags=-1,
    key='tags_input'
)
st.sidebar.markdown("---")

# Process tags into a list
fields = tags

# Initialize variables to store token and cost information
input_tokens = output_tokens = total_cost = 0

# Define the scraping function for a single URL
def perform_scrape(url):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    raw_html = fetch_html_selenium(url)
    markdown = html_to_markdown_with_readability(raw_html)
    save_raw_data(markdown, timestamp)
    DynamicListingModel = create_dynamic_listing_model(fields)
    DynamicListingsContainer = create_listings_container_model(DynamicListingModel)
    formatted_data = format_data(markdown, DynamicListingsContainer)
    formatted_data_text = json.dumps(formatted_data.dict())
    df = save_formatted_data(formatted_data, timestamp)
    return df, formatted_data, markdown, timestamp

# Function to scrape all URLs
def scrape_all_urls():
    all_results = []
    for url in urls:
        with st.spinner(f'Scraping {url}...'):
            result = perform_scrape(url)
            all_results.append(result)
    return all_results

# Handling button press for scraping
if 'perform_scrape' not in st.session_state:
    st.session_state['perform_scrape'] = False

if st.sidebar.button("Scrape All URLs"):
    st.session_state['results'] = scrape_all_urls()
    st.session_state['perform_scrape'] = True

if st.session_state.get('perform_scrape'):
    all_results = st.session_state['results']
    print(all_results)
    
    for i, (df, formatted_data, markdown, timestamp) in enumerate(all_results):
        st.subheader(f"Results for URL {i+1}")
        st.write("Scraped Data:", df)
        
        # Create columns for download buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(f"Download JSON (URL {i+1})", data=json.dumps(formatted_data.dict(), indent=4), file_name=f"{timestamp}data{i+1}.json")
        with col2:
            data_dict = formatted_data.dict() if hasattr(formatted_data, 'dict') else formatted_data
            first_key = next(iter(data_dict))
            main_data = data_dict[first_key]
            df = pd.DataFrame(main_data)
            st.download_button(f"Download CSV (URL {i+1})", data=df.to_csv(index=False), file_name=f"{timestamp}data{i+1}.csv")
        with col3:
            st.download_button(f"Download Markdown (URL {i+1})", data=markdown, file_name=f"{timestamp}data{i+1}.md")
        
        st.markdown("---")

    # Option to download all data combined
    all_dfs = [result[0] for result in all_results]
    combined_df = pd.concat(all_dfs, ignore_index=True)
    st.subheader("Download All Data Combined")
    st.download_button("Download All as CSV", data=combined_df.to_csv(index=False), file_name="all_scraped_data.csv")